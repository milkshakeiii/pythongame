import pygame
import sys, os, ctypes
import game_io
import gameplay
ctypes.windll.user32.SetProcessDPIAware()

pygame.font.init()
DEFAULT_FONT = pygame.font.SysFont('Ariel', 32)

GAME_SHAPE = (1600, 900)
TOP_LEFT_WINDOW_SHAPE = (310, 600)
BOTTOM_LEFT_WINDOW_SHAPE = (310, 300)
RIGHT_WINDOW_SHAPE = (1290, 900)
GRID_WIDTH = 30
GRID_HEIGHT = 30
IMAGE_DIRECTORY = "images/"

def load_whole_image(name):
    filename = os.path.join(IMAGE_DIRECTORY, name + ".png")
    full_image = pygame.image.load(filename)
    full_image.convert()
    full_image.convert_alpha()
    return full_image

def load_image_square(name, offset=(0, 0)):
    full_image = load_whole_image(name)
    square_rect = pygame.Rect(offset[0]*GRID_WIDTH,
                              offset[1]*GRID_HEIGHT,
                              GRID_WIDTH,
                              GRID_HEIGHT)
    image_square = full_image.subsurface(square_rect)
    return image_square


class Display:
    def __init__(self):
        self.screen = pygame.display.set_mode()
        self.play_screen = pygame.Surface(GAME_SHAPE)
        
    def draw(self):
        self.playtop_x = (self.screen.get_width() - self.play_screen.get_width()) // 2
        self.playtop_y = (self.screen.get_height() - self.play_screen.get_height()) // 2
        self.screen.blit(self.play_screen, (self.playtop_x, self.playtop_y))
        pygame.display.flip()

    def playzone_mouse(self, screenzone_mouse):
        return (screenzone_mouse[0] - self.playtop_x,
                screenzone_mouse[1] - self.playtop_y)


class DisplayBoard:
    def __init__(self):
        self.surface = pygame.Surface(RIGHT_WINDOW_SHAPE)
        self.squares = dict() # coords to list of images
        self.light_square = load_image_square("light_square")
        self.dark_square = load_image_square("dark_square")
        self.highlight_square = load_image_square("highlight_square")
        self.highlighted_square = None

    def surface_for_square(self, x, y, highlighted=False):
        surface = pygame.Surface((GRID_WIDTH, GRID_HEIGHT))
        background_square = self.light_square if (x+y)%2==0 else self.dark_square
        if (highlighted):
            background_square = self.highlight_square
        surface.blit(background_square, (0, 0))
        if (x, y) in self.squares:
            images = self.squares[(x, y)]
            for image in images:
                surface.blit(image, (0, 0))
        return surface

    def resurface(self):
        for x in range(43):
            for y in range(30):
                self.paint_square(x, y)

    def paint_square(self, x, y, highlighted=False):
        self.surface.blit(self.surface_for_square(x, y, highlighted=highlighted),
                          (x*GRID_WIDTH, y*GRID_HEIGHT))

    '''
    returns highlighted game grid coords
    '''
    def highlight(self, mouse_position) -> tuple:
        mouse_board_position = (mouse_position[0] - TOP_LEFT_WINDOW_SHAPE[0],
                                mouse_position[1])
        if self.highlighted_square != None:
            self.paint_square(self.highlighted_square[0],
                              self.highlighted_square[1])
        if self.surface.get_rect().collidepoint(mouse_board_position):
            self.highlighted_square = (mouse_board_position[0]//GRID_WIDTH,
                                       mouse_board_position[1]//GRID_HEIGHT)
            self.paint_square(self.highlighted_square[0],
                              self.highlighted_square[1],
                              highlighted=True)
        else:
            self.highlighted_square = None
        return self.highlighted_square

    def load_gameboard(self, gameboard):
        for coords, placeables in gameboard.squares.items():
            for placeable in placeables:
                offset = (coords[0] - placeable.coords[0],
                          coords[1] - placeable.coords[1])
                image = load_image_square(placeable.image_name, offset)
                self.squares[coords]= self.squares.get(coords, []) + [image]
                
            
class MouseoverWindow:
    def __init__(self):
        self.surface = pygame.Surface(TOP_LEFT_WINDOW_SHAPE)
        self.resource_image = load_whole_image("big_resource")

    def draw_mouseover_info(self, gameboard, coords):
        self.surface.fill((60, 30, 30))
        placeables = gameboard.squares.get(coords, [])
        resources = 0
        unit = None
        for placeable in placeables:
            if type(placeable) is gameplay.ResourcePile:
                resources = placeable.amount
            elif type(placeable) is gameplay.Unit:
                unit = placeable
        if (unit != None):
            self.draw_unit_info(unit)
        if (resources != 0):
            self.surface.blit(self.resource_image, (210, 160))
            resource_text = DEFAULT_FONT.render("x " + str(resources),
                                                False,
                                                (255, 255, 255))
            self.surface.blit(resource_text, (250, 170))

    def draw_unit_info(self, unit):
        image = load_whole_image(unit.image_name)
        self.surface.blit(image, (20, 20))
        parts = unit.parts
        y=200
        for part in parts:
            size_text = DEFAULT_FONT.render(str(part.size),
                                            False,
                                            (255, 255, 255))
            quality_string = "%6.2f" % (part.quality)
            quality_text = DEFAULT_FONT.render(quality_string,
                                               False,
                                               (255, 255, 255))
            type_text = DEFAULT_FONT.render(part.display_name(),
                                            False,
                                            (255, 255, 255))
            current_hp_string = str(part.max_hp()-part.damage)
            hp_string = current_hp_string + "/" + str(part.max_hp())
            hp_text = DEFAULT_FONT.render(hp_string,
                                          False,
                                          (255, 255, 255))
            self.surface.blit(size_text, (10, y))
            self.surface.blit(quality_text, (40, y))
            self.surface.blit(type_text, (110, y))
            self.surface.blit(hp_text, (240, y))
            y+=30

class ResearchWindow:

    RESEARCH_BOX_SIZE = (155, 32)

    def mouse_pos_to_box_coords(mouse_pos):
        window_mouse_pos = (mouse_pos[0], mouse_pos[1]-TOP_LEFT_WINDOW_SHAPE[1])
        return (window_mouse_pos[0]//RESEARCH_BOX_SIZE[0],
                window_mouse_pos[1]//RESEARCH_BOX_SIZE[1])
    
    def __init__(self):
        self.surface = pygame.Surface(BOTTOM_LEFT_WINDOW_SHAPE)
        self.surface.fill((30, 60, 30))
        progress_image = DEFAULT_FONT.render("Research Progress:",
                                             False,
                                             (255, 255, 255))
        self.surface.blit(progress_image, (10, 10))
        self.displayed_player = None
        self.research_boxes = []
        for i in range(6):
            row = []
            for j in range(2):
                research_box = load_whole_image("research_box")
                row.append(research_box)
                self.surface.blit(research_box, (j*research_box.get_width(),
                                                 40+i*research_box.get_height()))
            self.research_boxes.append(row)

        resources_image = DEFAULT_FONT.render("Resources Available:",
                                              False,
                                              (255, 255, 255))
        self.surface.blit(resources_image, (10, 260))
        
        

    '''
    Returns a unit prototype if a unit is moused over, else None
    '''
    def mouseover_check(self):
        pass

    def draw_player_info(self, player):
        self.displayed_player = player
        
        percentage_string = "{0:.1%}".format(player.research_fraction())
        percentage_text = DEFAULT_FONT.render(percentage_string,
                                              False,
                                              (255, 255, 255))
        self.surface.blit(percentage_text, (230, 10))

        percentage_text = DEFAULT_FONT.render(str(player.resource_amount),
                                              False,
                                              (255, 255, 255))
        self.surface.blit(percentage_text, (240, 260))
        
            
            
        
        


if __name__=='__main__':
    pygame.init()
    display = Display()

    mouseover_window = MouseoverWindow()

    research_window = ResearchWindow()
    
    gameboard = gameplay.Gameboard()
    test_resource = game_io.resource_pile_factory((6,6), 50)
    gameboard.add_to_board(test_resource)
    test_unit = game_io.unit_prototype_from_file("test_team_1", "mothership_1")
    test_unit.coords = (5, 5)
    gameboard.add_to_board(test_unit)

    display_board = DisplayBoard()
    display_board.load_gameboard(gameboard)
    display_board.resurface()

    display.draw()

    player = gameplay.Player(0, 0, [test_unit], research_amount=20)
    research_window.draw_player_info(player)
    
    while True:

        playzone_mouse = display.playzone_mouse(pygame.mouse.get_pos())
        highlighted_coords = display_board.highlight(playzone_mouse)
        mouseover_window.draw_mouseover_info(gameboard, highlighted_coords)

        display.play_screen.blit(mouseover_window.surface, (0, 0))
        display.play_screen.blit(research_window.surface,
                                 (0, TOP_LEFT_WINDOW_SHAPE[1]))
        display.play_screen.blit(display_board.surface,
                                 (TOP_LEFT_WINDOW_SHAPE[0], 0))
        display.draw()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
