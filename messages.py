from dataclasses import dataclass

@dataclass(eq=False)
class Message:
    pass

@dataclass(eq=False)
class WelcomePlayerNumber(Message):
    pass

@dataclass(eq=False)
class BeginGameEveryone(Message):
    pass

@dataclass(eq=False)
class MoreAboutMe(Message):
    pass

@dataclass(eq=False)
class ReportTurn(Message):
    pass
