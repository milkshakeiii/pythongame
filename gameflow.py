import copy

import gameplay
import game_io


class Gameflow:
    def __init__(self, turnsources):
        self.gamestates = [self.starting_gamestate()]
        self.turnsources = turnsources
        self.tick = 0

    '''
    return True iff the turn has been successfully advanced
    '''
    def try_to_advance_turn(self):
        self.tick += 1
        advance = (self.tick%1000 == 0)
        if advance:
            self.gamestates.append(self.most_recent_gamestate_copy())
        return advance

    def submit_local_turn(self, turn):
        pass

    def starting_gamestate(self):
        return test_gamestate()

    def most_recent_gamestate_copy(self):
        return copy.deepcopy(self.gamestates[-1])
        



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
