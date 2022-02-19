import gameplay
import gameflow

from dataclasses import dataclass
from typing import Optional, Type


@dataclass(eq=False)
class Message:
    def message_type(self):
        raise Exception("message_type called on Message superclass")

@dataclass(eq=False)
class MessageContainer:
    message: str
    message_type: str

@dataclass(eq=False)
class WelcomeRequest(Message):
    me: gameplay.Player

    def handle_on_server(self, server):
        server.players.append(self.me)
        player_number = len(server.players)
        print("Assigned a player number: " + str(len(server.players)))
        self.me.player_number = player_number
        self.me.team_number = player_number
        response = WelcomeResponse(player_number=player_number,
                                   team_number=player_number)
        return response

    def message_type(self):
        return "messages.WelcomeRequest"

@dataclass(eq=False)
class WelcomeResponse(Message):
    player_number: int
    team_number: int

    def message_type(self):
        return "messages.WelcomeResponse"

@dataclass(eq=False)
class StartGameRequest(Message):

    def handle_on_server(self, server):
        if (server.starting_gamestate == None):
            server.starting_gamestate = gameflow.first_arena(server.players)
        response = StartGameResponse()
        return response

    def message_type(self):
        return "messages.StartGameRequest"

@dataclass(eq=False)
class StartGameResponse(Message):
    def message_type(self):
        return "messages.StartGameResponse"

@dataclass(eq=False)
class GameStartPollRequest(Message):

    def handle_on_server(self, server):
        response = GameStartPollResponse(gamestate=server.starting_gamestate)
        return response

    def message_type(self):
        return "messages.GameStartPollRequest"

@dataclass(eq=False)
class GameStartPollResponse(Message):
    gamestate: Optional[gameplay.Gamestate]

    def message_type(self):
        return "messages.GameStartPollResponse"

@dataclass(eq=False)
class ReportTurnRequest(Message):
    gameturn: gameplay.Gameturn
    turn_index: int

    def handle_on_server(self, server):
        if (len(server.turns) == self.turn_index):
            server.turns.append(gameplay.build_gameturn([]))
        elif self.turn_index > len(server_turns):
            raise Exception("Turn index " + str(self.turn_index) + "is two " +
                            "or more turns into the future.")

        existing_turn = server.turns[self.turn_index]
        
        server.turns[self.turn_index] = gameplay.merge_turns([existing_turn,
                                                              self.gameturn])
        
        response = ReportTurnResponse()
        return response
    
    def message_type(self):
        return "messages.ReportTurnRequest"

@dataclass(eq=False)
class ReportTurnResponse(Message):
    def message_type(self):
        return "messages.ReportTurnResponse"

@dataclass(eq=False)
class TurnPollRequest(Message):
    turn_index: int

    def handle_on_server(self, server):
        turn = server.turns[self.turn_index]
        turn_complete = True
        for player in server.players:
            turn_complete = turn_complete and turn.contains_player(player)

        response_turn = response_turn if turn_complete else None
        
        response = TurnPollResponse(gameturn=response_turn,
                                    turn_index=turn_index)
        return response
    
    def message_type(self):
        return "messages.TurnPollRequest"

@dataclass(eq=False)
class TurnPollResponse(Message):
    gameturn: Optional[gameplay.Gameturn]
    turn_index: int
    
    def message_type(self):
        return "messages.TurnPollResponse"
