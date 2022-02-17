import copy

import gameplay
import game_io


class Turnsource:
    def __init__(self):
        self.player_number = None # gets set when added to a gameflow

    def turn_ready(self):
        raise Exception("turn_ready called on Turnsource superclass.")

    def get_turn(self):
        raise Exception("get_turn called on Turnsource superclass.")

class LocalTurnsource(Turnsource):
    def submit_turn(self, turn):
        self.turn = turn

    def turn_ready(self):
        return self.turn != None

    def get_turn(self):
        return self.turn

class InternetTurnsource(Turnsource):
    def __init__(self):
        pass

    def turn_ready(self):
        return True

    def get_turn(self):
        return gameplay.build_gameturn([])

class Gameflow:
    def __init__(self, local_player_number, starting_gamestate):
        self.local_turnsource = LocalTurnsource()
        self.local_turnsource.player_number = local_player_number
        self.turnsources = set([self.local_turnsource])

        for player in starting_gamestate.players:
            if (player.player_number != local_player_number):
                new_turnsource = InternetTurnsource()
                new_turnsource.player_number = player.player_number
                self.turnsources.add(new_turnsource)                

        self.gamestates = [starting_gamestate]
        self.tick = 0


    def get_local_player(self, gamestate):
        for player in gamestate.players:
            if player.player_number == self.local_turnsource.player_number:
                return player
        raise Exception("Local player player number not found.")

    '''
    return True iff the turn has been successfully advanced
    '''
    def try_to_advance_turn(self, gamestate):
        turnsources_ready = [turnsource.turn_ready() for
                             turnsource in self.turnsources]
        ready = all(turnsources_ready)
        if ready:
            turns = [turnsource.get_turn() for turnsource in self.turnsources]
            merged_turn = gameplay.merge_turns(turns)
            gameplay.advance_gamestate_via_mutation(gamestate, merged_turn)
            self.gamestates.append(copy.deepcopy(gamestate))
            return True
        return False

    def submit_local_turn(self, turn):
        self.local_turnsource.submit_turn(turn)

    def most_recent_gamestate(self):
        return self.gamestates[-1]


def first_arena(players):
    if len(players) != 2:
        raise Exception("Exactly two players required.  Found " +
                        str(len(players)) + ".")

    def get_mothership(player):
        for unit in player.unit_prototypes:
            if unit.research_threshhold == 0 and unit.production_cost == 0:
                return copy.deepcopy(unit)
    
    gameboard = gameplay.Gameboard(squares=dict())
    mothership_one = None
    mothership_two = None
    player_one = None
    player_two = None
    for player in players:
        if player.player_number == 1:
            player_one = player
            mothership_one = get_mothership(player)
        if player.player_number == 2:
            player_two = player
            mothership_two = get_mothership(player)

    if not all([variable != None for variable in [mothership_one,
                                                  mothership_two,
                                                  player_one,
                                                  player_two]]):
        raise Exception("Player or mothership not found.")

    mothership_one.coords = (4, 15)
    mothership_two.coords = (35, 15)
    gameboard.add_to_board(mothership_one)
    gameboard.add_to_board(mothership_two)

    for x in range(4, 6):
        for y in range(4, 6):            
            resource = game_io.resource_pile_factory((x, y), 25)
            gameboard.add_to_board(resource)
    for x in range(35, 37):
        for y in range(24, 26):            
            resource = game_io.resource_pile_factory((x, y), 50)
            gameboard.add_to_board(resource)
    for x in range(4, 6):
        for y in range(24, 26):            
            resource = game_io.resource_pile_factory((x, y), 25)
            gameboard.add_to_board(resource)
    for x in range(35, 37):
        for y in range(24, 26):            
            resource = game_io.resource_pile_factory((x, y), 50)
            gameboard.add_to_board(resource)
    for x in range(20, 26):
        for y in range(13,17):            
            resource = game_io.resource_pile_factory((x, y), 90)
            gameboard.add_to_board(resource)
    

    return gameplay.Gamestate(gameboard=gameboard, players=players)
            



def test_gamestate():
    gameboard = gameplay.Gameboard(squares=dict())
    test_resource = game_io.resource_pile_factory((6,6), 50)
    gameboard.add_to_board(test_resource)
    test_resource = game_io.resource_pile_factory((6,7), 4)
    gameboard.add_to_board(test_resource)
    test_resource = game_io.resource_pile_factory((12,7), 100)
    gameboard.add_to_board(test_resource)
    test_unit = game_io.unit_prototype_from_file("test_team_1", "mothership_1")
    test_unit.coords = (5, 5)
    gameboard.add_to_board(test_unit)
    test_unit_2 = game_io.unit_prototype_from_file("test_team_1", "small_1")
    test_unit_2.coords = (10, 15)
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

    test_player = gameplay.Player(player_number=0,
                                  team_number=0,
                                  unit_prototypes=test_army,
                                  resource_amount=100,
                                  research_amount=1000)

    return gameplay.Gamestate(gameboard=gameboard, players=[test_player])
