import networking
import messages
import game_io
import game

import time

team_name = input("Welcome.  Please input your team name: ")
me = game_io.player_from_team(team_name)

welcome_response = networking.wait_for_response(messages.WelcomeRequest(me=me))
me.player_number = welcome_response.player_number
me.team_number = welcome_response.team_number

gameflow = None

while True:
    answer = input("Start game? (Y/N) ")
    if answer in ["Y", "y", "yes", "Yes"]:
        networking.wait_for_response(messages.StartGameRequest())

    poll_response = networking.wait_for_response(messages.GameStartPollRequest())
    if poll_response.gamestate != None:
        gameflow = gameflow.Gameflow(me.player_number)
        break
        
game.run_game(gameflow)
