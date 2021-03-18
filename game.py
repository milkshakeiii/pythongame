import pygame, sys
from copy import copy

CARD_PROTOTYPES = {}


class Card:
    def __init__(self,
                 name,
                 my_damage = 0,
                 their_damage = 0,
                 my_front_cards_destroyed = 0,
                 their_front_cards_destroyed = 0,
                 my_front_cards_revealed = 0,
                 their_front_cards_revealed = 0,
                 block_damage_to_me = 0,
                 block_reveals_of_my_cards = 0,
                 block_destruction_of_my_cards = 0,
                 swap_with_position=-1,): #-1 means don't swap, otherwise 0-10 are front-back
        self.my_damage = my_damage
        self.their_damage = their_damage
        self.my_front_cards_destroyed = my_front_cards_destroyed
        self.their_front_cards_destroyed = their_front_cards_destroyed
        self.my_front_cards_revealed = my_front_cards_revealed
        self.their_front_cards_revealed = their_front_cards_revealed
        self.block_damage_to_me = block_damage_to_me
        self.block_reveals_of_my_cards = block_reveals_of_my_cards
        self.block_destruction_of_my_cards = block_destruction_of_my_cards
        self.swap_with_position = swap_with_position
        CARD_PROTOTYPES[name] = self

Card("Destructo", my_damage=2, their_damage=2)
Card("Revealo", their_front_cards_revealed=1, my_front_cards_revealed=1)
Card("Shiny Block", block_damage_to_me=1, my_front_cards_revealed=1)
Card("Nosee", block_reveals_of_my_cards=1)
Card("Nodie", block_destruction_of_my_cards=1, my_damage=1)
Card("Throw Card", my_front_cards_destroyed=1, their_damage=2)
Card("Headbutt", my_damage=2, their_front_cards_destroyed=1)
Card("Pain", my_damage=1, their_damage=1, swap_with_position=3)
Card("Explodo", my_front_cards_destroyed=1, their_front_cards_destroyed=1)
Card("Swapo", swap_with_position=6)


class Gamestate:
    def __init__(self,
                 player_1_cards = [copy(CARD_PROTOTYPES["Destructo"])]*3,
                 player_2_cards = [copy(CARD_PROTOTYPES["Destructo"])]*3,
                 player_1_front_card_index = 0,
                 player_2_front_card_index = 0,
                 player_1_revealed_cards_indices = [],
                 player_2_revealed_cards_indices = [],
                 player_1_life = 20,
                 player_2_life = 20):
        self.player_1_cards = player_1_cards
        self.player_2_cards = player_2_cards
        self.player_1_front_card_index = player_1_front_card_index
        self.player_2_front_card_index = player_2_front_card_index
        self.player_1_revealed_cards_indices = player_1_revealed_cards_indices
        self.player_2_revealed_cards_indices = player_2_revealed_cards_indices
        self.player_1_life = player_1_life
        self.player_2_life = player_2_life


def generate_advanced_gamestate(starting_gamestate, player_1_cards_played, player_2_cards_played):
    advanced_gamestate = copy.deepcopy(starting_gamestate)

    for i in range(min(player_1_cards_played, player_2_cards_played)):
        player_1_card = advanced_gamestate.player_1_cards[player_1_front_card_index+i]
        player_2_card = advanced_gamestate.player_2_cards[player_2_front_card_index+i]

        #damage
        player_1_damage = max(0, player_1_card.my_damage + player_2_card.their_damage - player_1_card.block_damage_to_me)
        player_2_damage = max(0, player_2_card.my_damage + player_1_card.their_damage - player_2_card.block_damage_to_me)
        advanced_gamestate.player_1_life -= player_1_damage
        advanced_gamestate.player_2_life -= player_2_damage

        #card destruction
        player_1_cards_destroyed = max(0, player_1_card.my_front_cards_destroyed + player_2_card.their_front_cards_destroyed - player_1_card.block_destruction_of_my_cards)
        player_2_cards_destroyed = max(0, player_2_card.my_front_cards_destroyed + player_1_card.their_front_cards_destroyed - player_2_card.block_destruction_of_my_cards)
        for j in range(min(player_1_cards_destroyed, len(starting_gamestate.player_1_cards))):
            delete_index = (player_1_front_card_index)%len(starting_gamestate.player_1_cards)
            del advanced_gamestate.player_1_cards[delete_index]
        for j in range(min(player_2_cards_destroyed, len(starting_gamestate.player_2_cards))):
            delete_index = (player_2_front_card_index)%len(starting_gamestate.player_2_cards)
            del advanced_gamestate.player_2_cards[delete_index]

        #revelation
        player_1_cards_revealed = max(0, player_1_card.my_front_cards_revealed + player_2_card.their_front_cards_revealed - player_1_card.block_reveals_of_my_cards)
        player_2_cards_revealed = max(0, player_2_card.my_front_cards_revealed + player_1_card.their_front_cards_revealed - player_2_card.block_reveals_of_my_cards)
        
        
        


class Display:
    #self, string, pixel count, pixel count
    def __init__(self, tile_file, tile_width, tile_height):
        self.tile_table = []
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.screen = pygame.display.set_mode((1024, 768))
        
        #populate tile table
        image = pygame.image.load(tile_file).convert()
        image_width, image_height = image.get_size()
        for tile_x in range(0, image_width//tile_width):
            line = []
            self.tile_table.append(line)
            for tile_y in range(0, image_height//tile_height):
                rect = (tile_x*tile_width, tile_y*tile_height, tile_width, tile_height)
                line.append(image.subsurface(rect))

        self.windows = []

    def draw(self):
        self.screen.fill((255, 255, 255))
        for x, row in enumerate(self.tile_table):
            for y, tile in enumerate(row):
                self.screen.blit(tile, (x*self.tile_width, y*self.tile_height))
        pygame.display.flip()


class Window:
    #self, position tuple
    def __init__(self, topleft):
        self.topleft = topleft









if __name__=='__main__':
    pygame.init()
    
    display = Display("pgame-tiled-tileset.png", 24, 16)
    display.draw()



    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
