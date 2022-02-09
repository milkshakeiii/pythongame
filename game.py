from enum import Enum

import pygame
import sys, os, ctypes
import copy

import game_io
import gameplay
import gameflow

from sys import platform
if platform == "win32":
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

load_whole_image_results = {}
def load_whole_image(name):
    if name in load_whole_image_results:
        return load_whole_image_results[name]
    filename = os.path.join(IMAGE_DIRECTORY, name + ".png")
    full_image = pygame.image.load(filename)
    full_image.convert()
    full_image.convert_alpha()
    load_whole_image_results[name] = full_image
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
    LIGHT_RED = 5
    LIGHT_GREEN = 6
    LIGHT_BLUE = 7


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
            HighlightColor.WHITE: load_image_square("highlight_square_white"),
            HighlightColor.LIGHT_RED: load_image_square("light_red"),
            HighlightColor.LIGHT_BLUE: load_image_square("light_blue"),
            HighlightColor.LIGHT_GREEN: load_image_square("light_green"),}
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
        self.squares = {}
        for coords, placeables in gameboard.squares.items():
            for placeable in placeables:
                offset = (coords[0] - placeable.coords[0],
                          coords[1] - placeable.coords[1])
                image = load_image_square(placeable.image_name, offset)
                self.squares[coords] = self.squares.get(coords, []) + [image]

    '''
    Based on the submitted actions in gameturn, draw highlights of
    different colors for movemenet, attack, production.
    '''
    def draw_working_turn(self, gameturn, player):
        for unit in gameturn[player]:
            for part in gameturn[player][unit]:
                action = gameturn[player][unit][part]
                if type(action) is gameplay.ArmamentAction:
                    shape_type = gameplay.shape_enum_to_object(part.shape_type)
                    blast_paths = shape_type.blast_paths(unit.coords,
                                                         part.size,
                                                         unit.size)
                    chosen_blast = blast_paths[action.blast_index]
                    for square in chosen_blast:
                        self.draw_square(square[0],
                                         square[1],
                                         HighlightColor.LIGHT_RED)
                if type(action) is gameplay.LocomotorAction:
                    shape_type = gameplay.shape_enum_to_object(part.shape_type)
                    move_paths = shape_type.move_paths(unit.coords,
                                                       part.size,
                                                       unit.size)
                    target_coords = (unit.coords[0] + action.move_target[0],
                                     unit.coords[1] + action.move_target[1])
                    for path in move_paths:
                        if target_coords not in path:
                            continue
                        for square in path:
                            self.draw_square(square[0],
                                             square[1],
                                             HighlightColor.LIGHT_GREEN)
                            if square == target_coords:
                                break
                if type(action) is gameplay.ProducerAction:
                    if action.out_coords != None:
                        self.draw_square(action.out_coords[0],
                                         action.out_coords[1],
                                         HighlightColor.LIGHT_BLUE)
                                
                        

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
              research_mouseover,
              turn_submitted):

        click_handled = False
        if (not turn_submitted):
            click_handled = self.gameturn_input_for_click(gameboard,
                                                          clicked_coords,
                                                          gameturn,
                                                          mouse_pos,
                                                          local_player,
                                                          research_mouseover)

        # Locking or unlocking
        if (not click_handled):
            new_lock = self.draw_mouseover_info(gameboard,
                                                clicked_coords,
                                                local_player,
                                                gameturn,
                                                mouse_pos)
            self.set_locked_unit(new_lock)

    '''
    return True iff the click has been handled and shouldn't be
    checked for locking/unlocking
    '''
    def gameturn_input_for_click(self,
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
            elif clicked_part.is_researcher():
                action = gameplay.ResearcherAction()
                gameturn.add_action(local_player,
                                    self.locked,
                                    clicked_part,
                                    action)
            elif clicked_part.is_collector():
                action = gameplay.CollectorAction()
                gameturn.add_action(local_player,
                                    self.locked,
                                    clicked_part,
                                    action)
            elif (not clicked_part.is_core()) and (not clicked_part.is_armor()):
                self.ui_active_part = clicked_part
            return True
        ###

        ### CLICKING WHILE A PART IS ACTIVE
        if self.ui_active_part is None:
            pass
        elif self.ui_active_part.is_armament():
            shape_type_enum = self.ui_active_part.shape_type
            shape = gameplay.shape_enum_to_object(shape_type_enum)
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
                    return True
                    
                index += 1
        elif self.ui_active_part.is_locomotor():
            shape_type_enum = self.ui_active_part.shape_type
            shape = gameplay.shape_enum_to_object(shape_type_enum)
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
                        return True

        elif (self.ui_active_part.is_producer() and
            (self.ui_active_part.next_activation_produces() or
             self.intermediary_production_unit != None)):
            build_unit = self.ui_active_part.under_production
            if self.intermediary_production_unit != None:
                build_unit = self.intermediary_production_unit
            for coord in self.ui_active_part.spawn_coords(self.locked.coords,
                                                          self.locked.size,
                                                          build_unit.size):
                if clicked_coords == coord:
                    action = gameplay.ProducerAction(produced_unit=build_unit,
                                                     out_coords=clicked_coords)
                    gameturn.add_action(local_player,
                                        self.locked,
                                        self.ui_active_part,
                                        action)
                    self.deselect_part()
                    return True
        elif (self.ui_active_part.is_producer() and
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
            return True
        ###
        
        return False

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
            shape_type_enum = self.ui_active_part.shape_type
            shape = gameplay.shape_enum_to_object(shape_type_enum)
            for path in shape.blast_paths(self.locked.coords,
                                          self.ui_active_part.size,
                                          self.locked.size):
                for coord in path:
                    highlightInfo.attack_highlights.add(coord)
        if type(self.ui_active_part) is gameplay.Locomotor:
            shape_type_enum = self.ui_active_part.shape_type
            shape = gameplay.shape_enum_to_object(shape_type_enum)
            for path in shape.move_paths(self.locked.coords,
                                          self.ui_active_part.size,
                                          self.locked.size):
                for coord in path:
                    highlightInfo.move_highlights.add(coord)
        if (type(self.ui_active_part) is gameplay.Producer and
            (self.ui_active_part.next_activation_produces() or
             self.intermediary_production_unit != None)):
            spawnee = self.ui_active_part.under_production
            if self.intermediary_production_unit != None:
                spawnee = self.intermediary_production_unit
            for coord in self.ui_active_part.spawn_coords(self.locked.coords,
                                                          self.locked.size,
                                                          spawnee.size):
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
            self.draw_part_mouseover_info(mouse_pos, gameturn, local_player)
        
        return unit

    def draw_part_mouseover_info(self, mouse_pos, gameturn, local_player):
        clicked_part_index = self.mouse_to_part_index(mouse_pos)
        part = None
        if (self.legitimate_part_index(clicked_part_index, mouse_pos)):
            part = self.locked.parts[clicked_part_index]
        if type(part) == gameplay.Producer:
            part_dict = gameturn[local_player].get(self.locked, dict())
            action = part_dict.get(part, None)

            displayed_unit = None
            if part.under_production != None:
                displayed_unit = part.under_production
            if action != None:
                displayed_unit = action.produced_unit
            if self.intermediary_production_unit != None:
                displayed_unit = self.intermediary_production_unit

            this_turn_addition = 0
            if action != None:
                this_turn_addition = part.points_per_activation()

            points_to_produce = "-"
            unit_name = "None"
            if displayed_unit != None:
                points_to_produce = displayed_unit.production_cost
                unit_name = displayed_unit.unit_name
            
            progress = (str(part.current_production_points) +
                        "+" + str(this_turn_addition)+ '/' +
                        str(points_to_produce))
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
        amount_info = gameturn.unit_pending_true_max_gain_energy(local_player,
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

        self.draw_button_text("Submit turn 1", (50, 70, 50))

    def draw_button_text(self, text, button_color):
        next_turn_button = pygame.Surface((155, 100))
        next_turn_button.fill(button_color)
        self.surface.blit(next_turn_button, (155, 232))
        
        submit_text = DEFAULT_FONT.render(text,
                                          False,
                                          (255, 255, 255))
        self.surface.blit(submit_text, (165, 255))
        
    '''
    Return true if submit turn button clicked else false
    '''
    def click(self, mouse_pos):
        research_pos = self.local_mouse_pos(mouse_pos)
        x_on_button = 155 < research_pos[0] < BOTTOM_LEFT_WINDOW_SHAPE[0]
        y_on_button = 232 < research_pos[1] < BOTTOM_LEFT_WINDOW_SHAPE[1]
        button_clicked = x_on_button and y_on_button
        if (button_clicked):
            self.draw_button_text("Submitted", (70, 50, 70))
        return button_clicked

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

    def local_mouse_pos(self, mouse_pos):
        research_pos = (mouse_pos[0],
                        mouse_pos[1] - TOP_LEFT_WINDOW_SHAPE[1])
        return research_pos
        
    '''
    Returns a unit prototype if a unit is moused over, else None
    '''
    def mouseover_check(self, mouse_pos):
        research_pos = self.local_mouse_pos(mouse_pos)
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

        percentage_background = pygame.Surface((80, 30))
        percentage_background.fill((30, 60, 30))
        self.surface.blit(percentage_background, (230, 10))
        percentage_string = "{0:.1%}".format(player.research_fraction())
        percentage_text = DEFAULT_FONT.render(percentage_string,
                                              False,
                                              (255, 255, 255))
        self.surface.blit(percentage_text, (230, 10))

        resource_background = pygame.Surface((50, 30))
        resource_background.fill((30, 60, 30))
        self.surface.blit(resource_background, (105, 255))
        resource_text = DEFAULT_FONT.render(str(player.resource_amount),
                                            False,
                                            (255, 255, 255))
        self.surface.blit(resource_text, (105, 255))

        for i in range(len(player.unit_prototypes)):
            prototype = player.unit_prototypes[i]
            box_coords = (i//2, i%2)
            self.prototypes[box_coords] = prototype

        self.draw_boxes(player)


def run_game(gameflow):
    clock = pygame.time.Clock()
    pygame.init()
    display = Display()

    mouseover_window = MouseoverWindow()
    research_window = ResearchWindow()
    display_board = DisplayBoard()
    
    gamestate = gameflow.most_recent_gamestate()

    display_board.load_gameboard(gamestate.gameboard)
    display_board.resurface()

    display.draw()

    local_player = gameflow.get_local_player(gamestate)
    research_window.draw_player_info(local_player)
    working_turn = gameplay.build_gameturn(gamestate.players)

    turn_submitted = False
    frame = 0
    while True:
        # local_player, working_turn, and gamestate
        # will be new objects each turn
        
        frame += 1
        clock.tick(30)

        display_board.load_gameboard(gamestate.gameboard)
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
        display_board.draw_working_turn(working_turn, local_player)
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
                                       research_mouseover,
                                       turn_submitted)
                submit_turn_clicked = research_window.click(playzone_mouse)
                if submit_turn_clicked:
                    gameflow.submit_local_turn(working_turn)
                turn_submitted = turn_submitted or submit_turn_clicked
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                mouseover_window.unclick()

        submit_success = False
        if (turn_submitted):
            submit_success = gameflow.try_to_advance_turn(gamestate)
        if (submit_success):
            turn_submitted = False
            working_turn = gameplay.default_turn_for(gamestate,
                                                     local_player,
                                                     working_turn)
            turn_number = str(len(gameflow.gamestates))
            research_window.draw_player_info(local_player)
            research_window.draw_button_text("Submit turn " + turn_number,
                                             (50, 70, 50))
            print("Turn " + turn_number)
            
        if frame%1000 == 0:
            print (clock.get_fps())



if __name__=='__main__':
    gameflow = gameflow.Gameflow(0)
    gameflow.start_game_host()
    run_game(gameflow)
