import networking
import messages
import game_io

team_name = input("Welcome.  Please input your team name: ")
me = game_io.player_from_team(team_name)

welcome_response = networking.wait_for_response(messages.MoreAboutMe(me=me))
me.player_number = welcome_response.player_number
me.team_number = welcome_response.team_number
