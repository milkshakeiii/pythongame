import gameplay

from dataclasses import dataclass

@dataclass(eq=False)
class Message:
    pass

@dataclass(eq=False)
class WelcomePlayerNumber(Message):
    player_number: int
    team_number: int

@dataclass(eq=False)
class BeginGameEveryone(Message):
    pass

@dataclass(eq=False)
class MoreAboutMe(Message):
    me: gameplay.Player

    def handle_on_server(self, server):
        server.players.append(self.me)
        player_number = len(server.players)
        self.me.player_number = player_number
        self.me.team_number = player_number
        response = WelcomePlayerNumber(player_number=player_number,
                                       team_number=player_number)
        return response
        
    

@dataclass(eq=False)
class ReportTurn(Message):
    pass
