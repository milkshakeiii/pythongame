import copy

import gameplay
import game_io


class Turnsource:
    def __init__(self):
        self.player_number = None # gets set when added to a gameflow

    def turn_ready(self):
        return NotImplemented

    def get_turn(self):
        return NotImplemented

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

# game creation flow:
# host game, build gameflow, LocalTurnsource is set and local player number is 0
# others join, call add_turnsource on network turnsources, send them back their
# player numbers based on order of joining.  self.turnsources is populated.
# start game, call start_game_host, first game state is built.  Send game state
# to other players.  Also send list of all players.
# 
# Non host players now build game flow with correct local player numbers, and
# start_game_non_host using the received gamestate.
#
# play proceeds with players submitting local turns and sending the turns to
# all players.  game will stay in sync naturally, all players are now peers
# and there is no host.
class Gameflow:
    def __init__(self, local_player_number):
        self.local_turnsource = LocalTurnsource()
        self.turnsources = set()
        self.add_turnsource(self.local_turnsource)

        self.gamestates = []
        self.tick = 0

    def start_game_host(self):
        self.gamestates = [self.starting_gamestate()]

    def start_game_non_host(self, starting_gamestate):
        self.gamestates = [starting_gamestate]

    '''
    returns player number of new player
    '''
    def add_turnsource(self, turnsource):
        player_number = len(self.turnsources)
        self.turnsources.add(turnsource)
        turnsource.player_number = player_number
        return player_number

    def get_local_player(self, gamestate):
        for player in gamestate.players:
            if player.player_number == self.local_turnsource.player_number:
                return player
        raise Exception("Local player player number not found.")

    '''
    return True iff the turn has been successfully advanced
    '''
    def try_to_advance_turn(self):
        turnsources_ready = [turnsource.turn_ready() for
                             turnsource in self.turnsources]
        ready = all(turnsources_ready)
        if ready:
            turns = [turnsource.get_turn() for turnsource in self.turnsources]
            merged_turn = gameplay.merge_turns(turns)
            old_gamestate = self.most_recent_gamestate_copy()
            new_gamestate = gameplay.advance_gamestate_via_mutation(
                old_gamestate, merged_turn)
            self.gamestates.append(new_gamestate)
            return True
        return False

    def submit_local_turn(self, turn):
        self.local_turnsource.submit_turn(turn)

    def starting_gamestate(self):
        return test_gamestate() # TODO

    def most_recent_gamestate_copy(self):
        return copy.deepcopy(self.gamestates[-1])
        



def test_gamestate():
    gameboard = gameplay.Gameboard(squares=dict())
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

    test_player = gameplay.Player(player_number=0,
                                  team_number=0,
                                  unit_prototypes=test_army,
                                  resource_amount=20,
                                  research_amount=0)

    return gameplay.Gamestate(gameboard=gameboard, players=[test_player])
