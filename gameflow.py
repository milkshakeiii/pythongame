import copy
import time

from uuid import uuid4

import gameplay
import game_io
import networking
import messages


class Turnsource:
    def __init__(self):
        self.player_number = None # gets set when added to a gameflow

    def turn_ready(self, turn_index):
        raise Exception("turn_ready called on Turnsource superclass.")

    def get_turn(self):
        raise Exception("get_turn called on Turnsource superclass.")

class LocalTurnsource(Turnsource):
    def submit_turn(self, turn, turn_index):
        self.turn = turn
        networking.send_message(
            messages.ReportTurnRequest(gameturn=turn,
                                       turn_index=turn_index))

    def turn_ready(self, turn_index):
        return self.turn != None

    def get_turn(self):
        return self.turn

class InternetTurnsource(Turnsource):    
    def __init__(self):
        self.response_protocol = None
        self.last_request_time = 0

    def turn_ready(self, turn_index):
        if (self.response_protocol != None
            and self.response_protocol.response != None
            and self.response_protocol.response.gameturn != None):
            return True
        
        if (self.response_protocol != None
            and self.response_protocol.response != None
            and self.response_protocol.response.gameturn == None):
            self.response_protocol = None
        
        if ((time.time() - self.last_request_time) > 5
             and self.response_protocol == None):
            self.response_protocol = networking.send_message(
                messages.TurnPollRequest(turn_index=turn_index))
            self.last_request_time = time.time()

        return False

    def get_turn(self):
        turn = self.response_protocol.response.gameturn
        self.response_protocol = None
        return turn

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

        self.gamestate_record = [copy.deepcopy(starting_gamestate)]
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
        next_index = len(self.gamestate_record)-1
        turnsources_ready = [turnsource.turn_ready(next_index) for
                             turnsource in self.turnsources]
        ready = all(turnsources_ready)
        if ready:
            turns = [turnsource.get_turn() for turnsource in self.turnsources]
            merged_turn = gameplay.merge_turns(turns)
            gameplay.advance_gamestate_via_mutation(gamestate, merged_turn)
            self.gamestate_record.append(copy.deepcopy(gamestate))
            return True
        return False

    def submit_local_turn(self, turn):
        next_index = len(self.gamestate_record)-1
        self.local_turnsource.submit_turn(turn, next_index)



def first_arena(players):
    if len(players) != 2:
        raise Exception("Exactly two players required.  Found " +
                        str(len(players)) + ".")
    
    gameboard = gameplay.Gameboard(squares=dict())
    mothership_one = None
    mothership_two = None
    player_one = None
    player_two = None
    for player in players:
        if player.player_number == 1:
            player_one = player
            mothership_one = gameplay.get_mothership(player)
        if player.player_number == 2:
            player_two = player
            mothership_two = gameplay.get_mothership(player)

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
    test_resource = game_io.resource_pile_factory((6,7), 400)
    gameboard.add_to_board(test_resource)
    test_resource = game_io.resource_pile_factory((12,7), 100)
    gameboard.add_to_board(test_resource)

    test_player = game_io.player_from_team("monsters_1")
    test_player.resource_amount = 100

    test_unit = gameplay.get_mothership(test_player)
    test_unit.coords = (5, 5)
    gameboard.add_to_board(test_unit)

    return gameplay.Gamestate(gameboard=gameboard, players=[test_player])
