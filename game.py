import pygame, sys
import ctypes
ctypes.windll.user32.SetProcessDPIAware()



GAME_SHAPE = (1600, 900)
TOP_LEFT_WINDOW_SHAPE = (310, 600)
BOTTOM_LEFT_WINDOW_SHAPE = (310, 300)
RIGHT_WINDOW_SHAPE = (1290, 900)
GRID_WIDTH = 30
GRID_HEIGHT = 30
IMAGE_DIRECTORY = "images/"



def load_image(name):
    image = pygame.image.load(IMAGE_DIRECTORY + name + ".png").convert()
    return image


class Display:
    #self, string, pixel count, pixel count
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
        self.squares = dict()
        self.light_square = load_image("light_square")
        self.dark_square = load_image("dark_square")
        self.highlight_square = load_image("highlight_square")
        self.highlighted_square = None

    def surface_for_square(self, x, y, highlighted=False):
        surface = pygame.Surface((GRID_WIDTH, GRID_HEIGHT))
        background_square = self.light_square if (x+y)%2==0 else self.dark_square
        if (highlighted):
            background_square = self.highlight_square
        surface.blit(background_square, (0, 0))
        if (x, y) in self.squares:
            surface.blit(self.squares[(x, y)])
        return surface

    def resurface(self):
        for x in range(43):
            for y in range(30):
                self.paint_square(x, y)

    def paint_square(self, x, y, highlighted=False):
        self.surface.blit(self.surface_for_square(x, y, highlighted=highlighted),
                          (x*GRID_WIDTH, y*GRID_HEIGHT))

    def highlight(self, mouse_position):
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
            



if __name__=='__main__':
    pygame.init()
    display = Display()

    top_left_window = pygame.Surface(TOP_LEFT_WINDOW_SHAPE)
    top_left_window.fill((60, 30, 30))

    bottom_left_window = pygame.Surface(BOTTOM_LEFT_WINDOW_SHAPE)
    bottom_left_window.fill((30, 60, 30))

    display_board = DisplayBoard()
    display_board.resurface()

    display.draw()

    
    while True:

        playzone_mouse = display.playzone_mouse(pygame.mouse.get_pos())
        display_board.highlight(playzone_mouse)

        display.play_screen.blit(top_left_window, (0, 0))
        display.play_screen.blit(bottom_left_window,
                                 (0, TOP_LEFT_WINDOW_SHAPE[1]))
        display.play_screen.blit(display_board.surface,
                                 (TOP_LEFT_WINDOW_SHAPE[0], 0))
        display.draw()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
