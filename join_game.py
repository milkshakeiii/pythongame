import networking
import messages
import game_io
import game
import gameflow

import time

import crochet

crochet.setup()

team_name = input("Welcome.  Please input your team name: ")
me = game_io.player_from_team(team_name)
        
welcome_response = networking.wait_for_response(messages.WelcomeRequest(me=me))
me.player_number = welcome_response.player_number
me.team_number = welcome_response.team_number

internet_gameflow = None

while True:
    answer = input("Start game? (Y/N) ")
    if answer in ["Y", "y", "yes", "Yes"]:
        networking.wait_for_response(messages.StartGameRequest())

    poll_response = networking.wait_for_response(
        messages.GameStartPollRequest())
    gamestate = poll_response.gamestate
    if gamestate != None:
        gamestate.gameboard.prune_transporter_clones()
        internet_gameflow = gameflow.Gameflow(me.player_number,
                                              gamestate)
        print("Player number: " + str(me.player_number))
        game.run_game(internet_gameflow, gamestate)
        break
