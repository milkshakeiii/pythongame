import gameplay
import gameflow

from dataclasses import dataclass
from typing import Optional

@dataclass(eq=False)
class Message:
    pass

@dataclass(eq=False)
class WelcomeRequest(Message):
    me: gameplay.Player

    def handle_on_server(self, server):
        server.players.append(self.me)
        player_number = len(server.players)
        print(len(server.players))
        self.me.player_number = player_number
        self.me.team_number = player_number
        response = WelcomeResponse(player_number=player_number,
                                   team_number=player_number)
        return response

@dataclass(eq=False)
class WelcomeResponse(Message):
    player_number: int
    team_number: int

@dataclass(eq=False)
class StartGameRequest(Message):

    def handle_on_server(self, server):
        server.starting_gamestate = gameflow.first_arena(server.players)
        response = StartGameResponse(gamestate=server.starting_gamestate)
        return response

@dataclass(eq=False)
class StartGameResponse(Message):
    pass

@dataclass(eq=False)
class GameStartPollRequest(Message):

    def handle_on_server(self, server):
        response = GameStartPollResponse(gamestate=server.starting_gamestate)
        return response

@dataclass(eq=False)
class GameStartPollResponse(Message):
    gamestate: Optional[gameplay.Gamestate]

@dataclass(eq=False)
class ReportTurnRequest(Message):
    pass
