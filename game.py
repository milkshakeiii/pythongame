from enum import Enum

import pygame
import sys, os, ctypes
import game_io
import gameplay
ctypes.windll.user32.SetProcessDPIAware()


pygame.font.init()
DEFAULT_FONT = pygame.font.SysFont('consolas', 22)

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


class HighlightColor(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
    WHITE = 4


class DisplayBoard:
    def __init__(self):
        self.surface = pygame.Surface(RIGHT_WINDOW_SHAPE)
        self.squares = dict() # coords to list of images
        self.light_square = load_image_square("light_square")
        self.dark_square = load_image_square("dark_square")
        self.highlight_squares = {
            HighlightColor.RED: load_image_square("highlight_square_red"),
            HighlightColor.GREEN: load_image_square("highlight_square_green"),
            HighlightColor.BLUE: load_image_square("highlight_square_blue"),
            HighlightColor.WHITE: load_image_square("highlight_square_white")}
        self.highlighted_square = None

    def surface_for_square(self, x, y, highlight=None):
        surface = pygame.Surface((GRID_WIDTH, GRID_HEIGHT))
        background_square = self.light_square if (x+y)%2==0 else self.dark_square
        surface.blit(background_square, (0, 0))
        if (x, y) in self.squares:
            images = self.squares[(x, y)]
            for image in images:
                surface.blit(image, (0, 0))
        if (highlight):
            surface.blit(self.highlight_squares[highlight], (0, 0))
        return surface

    def resurface(self):
        for x in range(43):
            for y in range(30):
                self.draw_square(x, y)

    def draw_square(self, x, y, highlight=None):
        self.surface.blit(self.surface_for_square(x, y, highlight=highlight),
                          (x*GRID_WIDTH, y*GRID_HEIGHT))

    '''
    draws mouseover highlight and returns highlighted game grid coords
    '''
    def highlight(self, mouse_position) -> tuple:
        mouse_board_position = (mouse_position[0] - TOP_LEFT_WINDOW_SHAPE[0],
                                mouse_position[1])
        if self.highlighted_square != None:
            self.draw_square(self.highlighted_square[0],
                              self.highlighted_square[1])
        if self.surface.get_rect().collidepoint(mouse_board_position):
            self.highlighted_square = (mouse_board_position[0]//GRID_WIDTH,
                                       mouse_board_position[1]//GRID_HEIGHT)
            self.draw_square(self.highlighted_square[0],
                             self.highlighted_square[1],
                             highlight=HighlightColor.WHITE)
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

    '''
    Based on the submitted actions in gameturn, draw highlights of
    different colors for movemenet, attack, production.
    '''
    def draw_working_turn(self, gameturn):
        pass # TODO

    '''
    Based on the dicts in highlight_info, draw highlights for UI
    actions in progress, determined by mouseover_window.
    '''
    def draw_highlights(self, highlight_info):
        attack = highlight_info.attack_highlights
        move = highlight_info.move_highlights
        produce = highlight_info.produce_highlights
        for color,squares in [(HighlightColor.RED, attack),
                              (HighlightColor.GREEN, move),
                              (HighlightColor.BLUE, produce)]:
            for square in squares:
                self.draw_square(square[0], square[1], highlight=color)
                

class HighlightInfo:
    def __init__(self):
        self.attack_highlights = set()
        self.move_highlights = set()
        self.produce_highlights = set()
        self.dehighlights = set()

    def add_based_on_part(self, add_us, part):
        if type(part) is gameplay.Armament:
            highlightInfo.attack_highlights.update(add_us)
        if type(part) is gameplay.Locomotor:
            highlightInfo.move_highlights.update(add_us)
        if type(part) is gameplay.Producer:
            highlightInfo.produce_highlights.update(add_us)

            
class MouseoverWindow:
    def __init__(self):
        self.surface = pygame.Surface(TOP_LEFT_WINDOW_SHAPE)
        self.resource_image = load_whole_image("big_resource")
        self.part_zone_offset = 200
        self.part_zone_increment = 30
        self.locked = None
        self.ui_active_part = None
        self.intermediary_production_unit = None

    def mouse_to_part_index(self, mouse_pos):
        part_zone_y = (mouse_pos[1] - self.part_zone_offset)
        return part_zone_y // self.part_zone_increment

    def legitimate_part_index(self, clicked_part_index, mouse_pos):
        return ((self.locked != None) and
                (clicked_part_index >= 0) and
                (clicked_part_index < len(self.locked.parts)) and
                (mouse_pos[0] < TOP_LEFT_WINDOW_SHAPE[0]))

    def click(self,
              gameboard,
              clicked_coords,
              gameturn,
              mouse_pos,
              local_player,
              research_mouseover):

        ### CLICKING A PART
        clicked_part_index = self.mouse_to_part_index(mouse_pos)
        if (self.legitimate_part_index(clicked_part_index, mouse_pos)):
            clicked_part = self.locked.parts[clicked_part_index]
            if gameturn.part_active(local_player,
                                    self.locked,
                                    clicked_part):
                gameturn.remove_action(local_player, self.locked, clicked_part)
            elif type(clicked_part) == gameplay.Researcher:
                action = gameplay.ResearcherAction()
                gameturn.add_action(local_player,
                                    self.locked,
                                    clicked_part,
                                    action)
            elif type(clicked_part) == gameplay.Collector:
                action = gameplay.CollectorAction()
                gameturn.add_action(local_player,
                                    self.locked,
                                    clicked_part,
                                    action)
            elif not (type(clicked_part) in [gameplay.EnergyCore,
                                             gameplay.Armor]):
                self.ui_active_part = clicked_part
            return
        ###

        ### CLICKING WHILE A PART IS ACTIVE 
        if type(self.ui_active_part) is gameplay.Armament:
            shape = self.ui_active_part.shape_type
            index = 0
            for path in shape.blast_paths(self.locked.coords,
                                          self.ui_active_part.size,
                                          self.locked.size):
                if clicked_coords in path:
                    action = gameplay.ArmamentAction(blast_index=index)
                    gameturn.add_action(local_player,
                                        self.locked,
                                        self.ui_active_part,
                                        action)
                    self.deselect_part()
                    return
                    
                index += 1
        if type(self.ui_active_part) is gameplay.Locomotor:
            shape = self.ui_active_part.shape_type
            for path in shape.move_paths(self.locked.coords,
                                          self.ui_active_part.size,
                                          self.locked.size):
                for coord in path:
                    if clicked_coords == coord:
                        delta = (coord[0] - self.locked.coords[0],
                                 coord[1] - self.locked.coords[1])
                        action = gameplay.LocomotorAction(move_target=delta)
                        gameturn.add_action(local_player,
                                            self.locked,
                                            self.ui_active_part,
                                            action)
                        self.deselect_part()
                        return

        if (type(self.ui_active_part) is gameplay.Producer and
            (self.ui_active_part.next_activation_produces() or
             self.intermediary_production_unit != None)):
            for coord in self.ui_active_part.spawn_coords(self.locked.coords,
                                                          self.locked.size):
                if clicked_coords == coord:
                    build_unit = self.ui_active_part.under_production
                    if build_unit == None:
                        build_unit = self.intermediary_production_unit
                    action = gameplay.ProducerAction(produced_unit=build_unit,
                                                     out_coords=clicked_coords)
                    gameturn.add_action(local_player,
                                        self.locked,
                                        self.ui_active_part,
                                        action)
                    self.deselect_part()
                    return
        elif (type(self.ui_active_part) is gameplay.Producer and
              self.ui_active_part.under_production == None and
              research_mouseover != None):
            if (self.ui_active_part.points_per_activation() <
                research_mouseover.production_cost):
                act = gameplay.ProducerAction(produced_unit=research_mouseover,
                                                 out_coords=None)
                gameturn.add_action(local_player,
                                    self.locked,
                                    self.ui_active_part,
                                    act)
                self.deselect_part()
            else:
                self.intermediary_production_unit = research_mouseover
            return
        ###

        ### LOCKING OR UNLOCKING
        new_lock = self.draw_mouseover_info(gameboard,
                                            clicked_coords,
                                            local_player,
                                            gameturn,
                                            mouse_pos)
        self.set_locked_unit(new_lock)
        ###

    def deselect_part(self):
        self.ui_active_part = None
        self.intermediary_production_unit = None

    def unclick(self):
        self.set_locked_unit(None)

    def set_locked_unit(self, locked):
        self.deselect_part()
        self.locked = locked

    '''
    Based on selected units and parts, build a HighlightInfo to
    tell DisplayGameboard about which squares should be highlighted
    for UI actions in progress.
    '''
    def get_highlights(self) -> HighlightInfo:
        highlightInfo = HighlightInfo()
        if type(self.ui_active_part) is gameplay.Armament:
            shape = self.ui_active_part.shape_type
            for path in shape.blast_paths(self.locked.coords,
                                          self.ui_active_part.size,
                                          self.locked.size):
                for coord in path:
                    highlightInfo.attack_highlights.add(coord)
        if type(self.ui_active_part) is gameplay.Locomotor:
            shape = self.ui_active_part.shape_type
            for path in shape.move_paths(self.locked.coords,
                                          self.ui_active_part.size,
                                          self.locked.size):
                for coord in path:
                    highlightInfo.move_highlights.add(coord)
        if (type(self.ui_active_part) is gameplay.Producer and
            (self.ui_active_part.next_activation_produces() or
             self.intermediary_production_unit != None)):
            for coord in self.ui_active_part.spawn_coords(self.locked.coords,
                                                          self.locked.size):
                highlightInfo.produce_highlights.add(coord)
        return highlightInfo

    '''
    Based on moused over coords, draw everything in the window and
    return the unit that is moused over
    '''
    def draw_mouseover_info(self,
                            gameboard,
                            mouseover_coords,
                            local_player,
                            gameturn,
                            mouse_pos):
        self.surface.fill((60, 30, 30))
        placeables = gameboard.squares.get(mouseover_coords, [])
        resources = 0
        unit = None
        for placeable in placeables:
            if type(placeable) is gameplay.ResourcePile:
                resources = placeable.amount
            elif type(placeable) is gameplay.Unit:
                unit = placeable
        if (self.locked != None):
            self.draw_unit_info(self.locked, local_player, gameturn)
        elif (unit != None):
            self.draw_unit_info(unit, local_player, gameturn)
        if (resources != 0):
            self.surface.blit(self.resource_image, (210, 160))
            resource_text = DEFAULT_FONT.render("x " + str(resources),
                                                False,
                                                (255, 255, 255))
            self.surface.blit(resource_text, (250, 170))

        if (self.locked != None):
            self.draw_part_mouseover_info(mouse_pos)
        
        return unit

    def draw_part_mouseover_info(self, mouse_pos):
        clicked_part_index = self.mouse_to_part_index(mouse_pos)
        part = None
        if (self.legitimate_part_index(clicked_part_index, mouse_pos)):
            part = self.locked.parts[clicked_part_index]
        if type(part) == gameplay.Producer:
            unit_name = "None"
            progress = "0/0"
            if part.under_production != None:
                unit_name = part.under_production[1]
                progress = (str(part.current_production_points) + '/' +
                            str(part.points_to_produce))
            under_production_string = "-> " + unit_name + " " + progress
            producer_text = DEFAULT_FONT.render(under_production_string,
                                                False,
                                                (255, 255, 255))
            self.surface.blit(producer_text, (10, 550))
    
    def draw_unit_info(self, unit, local_player, gameturn, clear_first = False):
        if (clear_first == True):
            self.surface.fill((60, 30, 30))
        image = load_whole_image(unit.image_name)
        self.surface.blit(image, (20, 20))
        parts = unit.parts
        activated_parts = gameturn[local_player].get(unit, [])
        y=self.part_zone_offset
        for part in parts:
            color = (255, 255, 255)
            if part == self.ui_active_part:
                color = (255, 255, 0)
            elif part in activated_parts:
                color = (0, 255, 0)
            size_text = DEFAULT_FONT.render(str(part.size),
                                            False,
                                            color)
            quality_string = "%6.2f" % (part.quality)
            quality_text = DEFAULT_FONT.render(quality_string,
                                               False,
                                               color)
            type_text = DEFAULT_FONT.render(part.display_name(),
                                            False,
                                            color)
            current_hp_string = str(part.max_hp()-part.damage)
            hp_string = current_hp_string + "/" + str(part.max_hp())
            hp_text = DEFAULT_FONT.render(hp_string,
                                          False,
                                          color)
            self.surface.blit(size_text, (10, y))
            self.surface.blit(quality_text, (35, y))
            self.surface.blit(type_text, (110, y))
            self.surface.blit(hp_text, (240, y))
            y+=self.part_zone_increment

        energy_text = DEFAULT_FONT.render("Energy: ",
                                          False,
                                          (255, 255, 255))
        self.surface.blit(energy_text, (210, 20))
        amount_info = gameturn.unit_pending_true__max_gain_energy(local_player,
                                                                  unit)
        pending, true, maximum, gain = amount_info
        pending = "%6.2f" % (pending)
        true = "%6.2f" % (true)
        maximum = str(maximum)
        gain = str(gain)
        amount_string = "("+true+")"
        energy_text = DEFAULT_FONT.render(amount_string,
                                          False,
                                          (255, 255, 255))
        self.surface.blit(energy_text, (210, 44))
        amount_string = pending+"+"+gain
        energy_text = DEFAULT_FONT.render(amount_string,
                                          False,
                                          (255, 255, 255))
        self.surface.blit(energy_text, (210, 64))
        amount_string = "/"+maximum
        energy_text = DEFAULT_FONT.render(amount_string,
                                          False,
                                          (255, 255, 255))
        self.surface.blit(energy_text, (210, 84))

        

class ResearchWindow:
    def __init__(self):
        self.surface = pygame.Surface(BOTTOM_LEFT_WINDOW_SHAPE)
        self.surface.fill((30, 60, 30))
        self.resource_image = load_whole_image("medium_resource")
        progress_image = DEFAULT_FONT.render("Research Progress:",
                                             False,
                                             (255, 255, 255))
        resources_text = DEFAULT_FONT.render("Store:",
                                             False,
                                             (255, 255, 255))
        self.surface.blit(resources_text, (30, 255))
        self.surface.blit(progress_image, (10, 10))
        self.surface.blit(self.resource_image, (0, 250))
        
        self.research_box_surface = load_whole_image("research_box")
        self.research_box_width = self.research_box_surface.get_width()
        self.research_box_height = self.research_box_surface.get_height()
        self.prototype_zone_offset = 40
        self.research_boxes = []
        self.prototypes = dict() # box row, column to Unit prototype

    def research_box_position(self, row, column):
        return (column*self.research_box_width,
                self.prototype_zone_offset + row*self.research_box_height)

    def build_box(self, row, column, player):
        research_box = pygame.Surface((self.research_box_width,
                                       self.research_box_height))
        research_box.fill((30, 60, 30))
        research_box.blit(load_whole_image("research_box"), (0, 0))

        prototype = self.prototypes.get((row, column), None)
        if (prototype != None):
            name = prototype.unit_name
            locked = player.research_fraction() < prototype.research_threshhold
            color = (125, 125, 125) if locked else (255, 255, 255)
            name_text = DEFAULT_FONT.render(name[:5],
                                            False,
                                            color)
            research_string = "{0:.1%}".format(prototype.research_threshhold)
            research_text = DEFAULT_FONT.render(research_string,
                                                False,
                                                (255, 255, 255))
            cost_string = str(prototype.production_cost)
            cost_text = DEFAULT_FONT.render(cost_string,
                                            False,
                                            (255, 255, 255))

            research_box.blit(name_text, (2, 4))
            research_box.blit(research_text, (62, 4))
            research_box.blit(cost_text, (125, 4))
        return research_box

    def draw_boxes(self, player):
        for i in range(6):
            row = []
            for j in range(2):
                research_box = self.build_box(i, j, player)
                position = self.research_box_position(i, j)
                self.surface.blit(research_box, position)
                row.append(research_box)
                
            self.research_boxes.append(row)
        
    '''
    Returns a unit prototype if a unit is moused over, else None
    '''
    def mouseover_check(self, mouse_pos):
        research_pos = (mouse_pos[0],
                        mouse_pos[1] - TOP_LEFT_WINDOW_SHAPE[1])
        prototype_zone_mouse = (research_pos[0],
                                research_pos[1] - self.prototype_zone_offset)
        research_box_row = prototype_zone_mouse[1]//self.research_box_height
        research_box_column = prototype_zone_mouse[0]//self.research_box_width
        
        if (research_box_row, research_box_column) in self.prototypes:
            return self.prototypes[(research_box_row, research_box_column)]
        else:
            return None

    def draw_player_info(self, player):
        self.displayed_player = player
        
        percentage_string = "{0:.1%}".format(player.research_fraction())
        percentage_text = DEFAULT_FONT.render(percentage_string,
                                              False,
                                              (255, 255, 255))
        self.surface.blit(percentage_text, (230, 10))

        resource_text = DEFAULT_FONT.render(str(player.resource_amount),
                                            False,
                                            (255, 255, 255))
        self.surface.blit(resource_text, (105, 255))

        for i in range(len(player.unit_prototypes)):
            prototype = player.unit_prototypes[i]
            box_coords = (i//2, i%2)
            self.prototypes[box_coords] = prototype

        self.draw_boxes(player)
        

def test_gamestate():
    gameboard = gameplay.Gameboard()
    test_resource = game_io.resource_pile_factory((6,6), 50)
    gameboard.add_to_board(test_resource)
    test_resource = game_io.resource_pile_factory((6,7), 4)
    gameboard.add_to_board(test_resource)
    test_unit = game_io.unit_prototype_from_file("test_team_1", "mothership_1")
    test_unit.coords = (5, 5)
    gameboard.add_to_board(test_unit)
    test_unit_2 = game_io.unit_prototype_from_file("test_team_1", "small_1")
    test_unit_2.coords = (20, 15)
    gameboard.add_to_board(test_unit_2)
    test_unit_3 = game_io.unit_prototype_from_file("test_team_1", "big_1")
    test_unit_3.coords = (5, 20)
    gameboard.add_to_board(test_unit_3)
    test_unit_4 = game_io.unit_prototype_from_file("test_team_1", "small_2")
    test_unit_4.coords = (20, 5)
    gameboard.add_to_board(test_unit_4)


    test_army = [game_io.unit_prototype_from_file("test_team_1", "mothership_1"),
                 game_io.unit_prototype_from_file("test_team_1", "small_1"),
                 game_io.unit_prototype_from_file("test_team_1", "small_2"),
                 game_io.unit_prototype_from_file("test_team_1", "big_1")]

    test_player = gameplay.Player(0, 0, test_army, research_amount=20)

    return gameplay.Gamestate(gameboard, [test_player])
        

if __name__=='__main__':
    pygame.init()
    display = Display()

    mouseover_window = MouseoverWindow()
    research_window = ResearchWindow()
    display_board = DisplayBoard()
    
    gamestate = test_gamestate()

    display_board.load_gameboard(gamestate.gameboard)
    display_board.resurface()

    display.draw()

    local_player = gamestate.players[0]
    research_window.draw_player_info(local_player)
    working_turn = gameplay.Gameturn(gamestate.players)
    
    while True:
        display_board.resurface()
        
        playzone_mouse = display.playzone_mouse(pygame.mouse.get_pos())
        highlighted_coords = display_board.highlight(playzone_mouse)
        mouseover_window.draw_mouseover_info(gamestate.gameboard,
                                             highlighted_coords,
                                             local_player,
                                             working_turn,
                                             playzone_mouse)
        research_mouseover = research_window.mouseover_check(playzone_mouse)
        if (research_mouseover != None):
            mouseover_window.draw_unit_info(research_mouseover,
                                            local_player,
                                            working_turn,
                                            clear_first=True)

        additional_highlights: HighlightInfo = mouseover_window.get_highlights()
        display_board.draw_working_turn(working_turn)
        display_board.draw_highlights(additional_highlights)
        
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
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouseover_window.click(gamestate.gameboard,
                                       highlighted_coords,
                                       working_turn,
                                       playzone_mouse,
                                       local_player,
                                       research_mouseover)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                mouseover_window.unclick()
