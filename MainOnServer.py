#31/05/2020

from telegram.ext import (Updater, CommandHandler)

import random
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

"""
import os
PORT = int(os.environ.get('PORT', 5000))
"""
TOKEN = ''
games = {} # dict with key of chat id and value of game object

"""
A class that encapsulates the data needed for a game
of DareToWin in one Telegram group.
"""
class Game: 
    def __init__(self):
        self.players = {}
        self.dares = {}
        self.players_yet_to_play = []
        self.voters = []
        self.state = {
                'start_state': False,
                'players_assembled': False,
                'accept': False,
                'pass_dare': False,
                'pass_my_dare': False,
                'doing_dare': False,
                'collect_votes': False,
                'next_round': False,
                'end_game': False
            }
        self.current_player_id = 0
        self.yes = 0

    def change_state_true(self, state_list):
        for state_type in state_list:
            self.state[state_type] = True
    
    def change_state_false(self, state_list):
        for state_type in state_list:
            self.state[state_type] = False


"""
This function is tied to the /start command, 
which allows a user to start a game of DareToWin,
allowing others to join
"""
def start(update, context):
    chat_id = update.effective_chat.id
    player = update.effective_user
    player_id = player.id
    player_name = player.first_name
    if chat_id not in games.keys():
        games[chat_id] = Game()
    new_game = games[chat_id]
    if new_game.state['start_state'] == False:
        #games[chat_id].state['start_state'] = True
        games[chat_id].change_state_true(['start_state'])
        games[chat_id].players[player_id] = [player_name, 0, 0, False]
        context.bot.send_message(chat_id, 
                                player_name + " has started a game of DareToWin!\
                                \nPlease enter /join to join the game!\
                                \nEnter /gamestart when all players have joined!")

"""
This function is tied to the /join command,
which allows other users in the group to join the game
after someone else has started it with /start
"""
def join(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['start_state']:
        game = games[chat_id]
        if player_id not in game.players.keys():
            games[chat_id].players[player_id] = [player_name, 0, 0, False]
            context.bot.send_message(chat_id, 
                                    player_name + " has /join -ed the game!\
                                    \nIf all players are here, /gamestart!")
        else:
            context.bot.send_message(chat_id, 
                                    player_name + " is already in the game!\
                                    \nWaiting for others to /join!\
                                    \nIf all players are here, /gamestart!")


"""
This function is tied to the /gamestart command, 
which allows the group to finalise its
players and begin the game
"""
def gamestart(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['start_state'] and \
        player_id in games[chat_id].players.keys():
        game = games[chat_id]
        if len(game.players) == 1:
            context.bot.send_message(chat_id, 
                                    "There is only 1 player in the game :(\
                                    \nPlease wait for more players to /join!\
                                    \nEnter /players to view all players!")
        else:
            #games[chat_id].state['start_state'] = False
            #games[chat_id].state['players_assembled'] = True
            games[chat_id].change_state_false(['start_state'])
            games[chat_id].change_state_true(['players_assembled'])
            games[chat_id].players_yet_to_play = list(game.players.keys())
            context.bot.send_message(chat_id, 
                                    "Game start! Begin placing your dares!\
                                    \nEnter your dare in the following format:\
                                    \n/dare 'number of points it's worth' 'your dare'\
                                    \nIf you are stuck, enter /finddare to get a dare \
                                    \nfrom the dare pool!")


"""
This function updates the chat with the next player's dare.
Used in input_dares, pass_my_dare and check_rest functions.
"""
def next_turn(chat_id, context):
    game = games[chat_id]
    next_player_id = game.players_yet_to_play[0]
    starting_player_name = game.players[next_player_id][0]
    games[chat_id].current_player_id = next_player_id
    games[chat_id].players_yet_to_play.remove(next_player_id)
    dare_id = game.players[next_player_id][2]
    assigned_dare = game.dares[dare_id][2]
    assigned_dare_points = game.dares[dare_id][1]
    #games[chat_id].state['accept'] = True
    #games[chat_id].state['pass_dare'] = True
    games[chat_id].change_state_true(['accept', 'pass_dare'])
    context.bot.send_message(chat_id, 
                            "{}'s dare is {}, worth {} point(s), enter /accept\
                            if you are DARING or /pass if you want to pass the dare\
                            to its creator to do it!"
                            .format(starting_player_name, assigned_dare, assigned_dare_points))


"""
This function is tied to the /dare command, 
which allows players to enter the number of points their dares are worth 
and the dares themselves. After every player has placed their dares, 
the first player will be randomly allocated another player's dare.
"""
def input_dare(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    try:
        if chat_id in games.keys() and games[chat_id].state['players_assembled'] and \
            player_id in games[chat_id].players.keys():
            game = games[chat_id]
            
            if player_id not in game.dares.keys():
                dare = ''
                points = int(context.args[0])
                for word in context.args[1:]:
                    dare += word + ' '
                if not dare:
                    raise ValueError("Invalid dare")
                if points <= 0:
                    raise ValueError("Dare points must be more than 0")
                game.dares[player_id] = [player_name, points, dare]
                update.message.reply_text('{}, your dare has been placed!'
                                        .format(player_name))
            
            if len(game.players) == len (game.dares):
                #games[chat_id].state['players_assembled'] = False
                games[chat_id].change_state_false(['players_assembled'])
                players_ids = list(game.players.keys())
                dares_ids = list(game.dares.keys())
                random.shuffle(dares_ids)
                counter = 0
                for each_player_id, each_dare_id in zip(players_ids, dares_ids):
                    if each_player_id == each_dare_id:
                        a = 1
                        if counter == (len(players_ids) - 1):
                            a = -1
                        temp_id = dares_ids[counter]
                        dares_ids[counter] = dares_ids[counter + a]
                        dares_ids[counter + a] = temp_id
                        continue
                    counter += 1
                for dare_id,player_id in zip(dares_ids, players_ids):
                    value_player = game.players[player_id]
                    value_player[2] = dare_id
                context.bot.send_message(chat_id, 
                                        "All dares have been placed!")
                #Informing players on order
                numbering = 1
                order = ""
                for player in game.players_yet_to_play:
                    order += "{}. {}\n".format(numbering, game.players[player][0])
                    numbering += 1
                context.bot.send_message(chat_id, 
                                        "Here is the order of turns:\n{}\
                                        \nEnter /order anytime to know when your turn is coming up!"
                                        .format(order))
                #First player begins turn
                next_turn(chat_id, context)
    except (ValueError, IndexError): #need IndexError to account for empty context.args
        update.message.reply_text("Please enter your dare in the following format:\
                                \n/dare 'number of points it's worth' 'your dare'\
                                \nNote that dare points must be more than 0")


"""
This function is tied to the /accept command, 
which allows players, currently playing their turn, 
to accept the dare and commit to performing it.
"""
def accept(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['accept'] \
        and player_id == games[chat_id].current_player_id:
        game = games[chat_id]
        #games[chat_id].state['doing_dare'] = True
        #games[chat_id].state['accept'] = False
        #games[chat_id].state['pass_dare'] = False
        games[chat_id].change_state_true(['doing_dare'])
        games[chat_id].change_state_false(['accept', 'pass_dare'])
        games[chat_id].voters = list(game.players.keys())
        games[chat_id].voters.remove(game.current_player_id)
        context.bot.send_message(chat_id, 
                                player_name + ' has accepted the dare! Enter /donedare after you have '
                                  ' sent a video of yourself doing the dare, ' + player_name)

        
"""
This function is tied to the /pass command, 
which allows players, currently playing their turn,
to pass the dare to its original creator.
"""
def pass_dare(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['pass_dare'] \
        and player_id == games[chat_id].current_player_id:
        game = games[chat_id]
        #games[chat_id].state['doing_dare'] = True
        #games[chat_id].state['pass_my_dare'] = True
        #games[chat_id].state['accept'] = False
        #games[chat_id].state['pass_dare'] = False
        games[chat_id].change_state_true(['doing_dare', 'pass_my_dare'])
        games[chat_id].change_state_false(['accept', 'pass_dare'])
        dare_id = game.players[player_id][2] #dare creator's id
        dare_creator_name = game.players[dare_id][0]
        games[chat_id].current_player_id = dare_id
        games[chat_id].players[dare_id][3] = True #own dare set to true
        games[chat_id].voters = list(game.players.keys())
        games[chat_id].voters.remove(dare_id)
        context.bot.send_message(chat_id, 
                                player_name + ' has passed the dare, now the dare has fallen'
                                ' to its creator, ' + dare_creator_name + '. ' + dare_creator_name +
                                ' please send a video of yourself doing your dare, and then enter /donedare.'
                                ' However, if you cant/dont even want to attempt your own dare, enter'
                                ' /passmydare')


"""
This function is tied to the /passmydare command, which allows the creator of a dare,
when their own dare has been passed back to them during another player's turn,
to pass up on doing it. If all players have finished this round, players can
either choose to go another round or end the game.
"""
def pass_my_dare(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and  games[chat_id].state['pass_my_dare']\
        and games[chat_id].players[player_id][3]:
        game = games[chat_id]
        games[chat_id].players[player_id][3] = False #reset own dare flag
        #games[chat_id].state['pass_my_dare'] = False
        #games[chat_id].state['done_dare'] = False
        games[chat_id].change_state_false(['pass_my_dare', 'doing_dare'])
        games[chat_id].voters.clear()
        dare_points = game.dares[player_id][1] 
        current_score = game.players[player_id][1]
        new_score = current_score - (2 * dare_points) #Double penalty
        games[chat_id].players[player_id][1] = new_score
        context.bot.send_message(chat_id, 
                                player_name + ' has chickened out of his/her dare and has lost ' + str(dare_points * 2) + ' points, to'
                                ' now have ' + str(new_score) + ' points!')
        if not game.players_yet_to_play:
            #games[chat_id].state['end_game'] = True
            #games[chat_id].state['next_round'] = True
            games[chat_id].change_state_true(['next_round', 'end_game'])
            context.bot.send_message(chat_id, 
                                    'This round has now finished, enter /nextround to go'
                                    ' another round, or enter /endgame to finish the game'
                                    ' and see who the winner is')
        else:
            #Next player's turn
            next_turn(chat_id, context)

"""
This function is tied to the /donedare command, 
which allows players, who are currently playing their turn,
to indicate that they have completed their dare.
"""
def done_dare(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['doing_dare'] \
        and player_id == games[chat_id].current_player_id:
        game = games[chat_id]
        #games[chat_id].state['pass_my_dare'] = False
        #games[chat_id].state['doing_dare'] = False
        #games[chat_id].state['collect_votes'] = True
        games[chat_id].change_state_false(['pass_my_dare', 'doing_dare'])
        games[chat_id].change_state_true(['collect_votes'])
        context.bot.send_message(chat_id, 
                                player_name + ' has done the dare! Now the rest will decide'
                                ' if ' + player_name + ' has done it properly!'
                                '\nEnter /vote followed by yes if dare has been done properly'
                                ', and /vote followed by no if dare was not done properly, or'
                                ' if you are EEEVIIIL MUAHAHAHA!!!')


"""
This function is tied to the /vote command,
which allows players to vote after the current player has done the dare.
If more than half of the remaining players vote yes, the current player gets the
points allocated to the dare. If more than half of the remaining players vote no,
and if current player is the one who created the dare, the player is deducted half
the points allocated to the dare. Special case if the current player fails the dare
he created himself, in which he is deducted the full points allocated to the dare.
If all players have finished this round, players can
either choose to go another round or end the game.
"""
def check_rest(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['collect_votes']:
        game = games[chat_id]
        if player_id == game.current_player_id:
            context.bot.send_message(chat_id, 
                                    "Yea nice try gaming the system " + player_name
                                    + " but its not gonna work. You can't vote for yourself!")
        elif player_id in game.voters:
            try:
                if context.args[0] == 'yes':
                    games[chat_id].voters.remove(player_id)
                    games[chat_id].yes += 1
                    context.bot.send_message(chat_id, 
                                            "{} has acknowledged {}'s dare!"
                                            .format(player_name, game.players[game.current_player_id][0]))
                elif context.args[0] == 'no':
                    games[chat_id].voters.remove(player_id)
                    context.bot.send_message(chat_id, 
                                            "{} stares disapprovingly at {}"
                                            .format(player_name, game.players[game.current_player_id][0]))
                else:
                    raise Exception("Invalid Vote")
            except Exception:
                context.bot.send_message(chat_id, 
                                        "{}, please enter '/vote yes' if\
                                        \nthe dare was done properly,\
                                        \nor '/vote no' if the dare was not done properly!"
                                        .format(player_name))

            #all votes collected
            if not game.voters: #may be wrong ref
                #games[chat_id].state['collect_votes'] = False
                games[chat_id].change_state_false(['collect_votes'])
                current_points = game.players[game.current_player_id][1]
                current_player_name = game.players[game.current_player_id][0]
                own_dare = game.players[game.current_player_id][3]
                if game.yes >= ((len(game.players) - 1)/2):
                    dare_id = 0
                    if own_dare:
                        dare_id = game.current_player_id
                    else:
                        dare_id = game.players[game.current_player_id][2]
                    dare_points = game.dares[dare_id][1]
                    new_points = current_points + dare_points
                    games[chat_id].players[game.current_player_id][1] = new_points
                    context.bot.send_message(chat_id, 
                                            current_player_name + ' has done the dare well and now has ' +
                                            str(new_points) + ' points! Good job!')
                else:
                    new_points = 0
                    dare_id = 0
                    if own_dare:
                        dare_id = game.current_player_id
                        dare_points = game.dares[dare_id][1]
                        new_points = current_points - dare_points #Full penalty
                    else:
                        dare_id = game.players[game.current_player_id][2]
                        dare_points = game.dares[dare_id][1]
                        new_points = current_points - (dare_points / 2) #Half penalty
                    games[chat_id].players[game.current_player_id][1] = new_points
                    context.bot.send_message(chat_id, 
                                            current_player_name + ' has failed the dare and now has ' +
                                            str(new_points) + ' points :C, better luck next time!')
                
                games[chat_id].yes = 0
                games[chat_id].players[game.current_player_id][3] = False #reset own dare flag

                if not game.players_yet_to_play:
                    #games[chat_id].state['next_round'] = True
                    #games[chat_id].state['end_game'] = True
                    games[chat_id].change_state_true(['next_round', 'end_game'])
                    context.bot.send_message(chat_id, 
                                            'This round has now finished, enter /nextround to go'
                                            ' another round, or enter /endgame to finish the game'
                                            ' and see who the winner is')
                else:
                    #Next player's turn
                    next_turn(chat_id, context)

"""
This function is tied to the /nextround command,
which allows players to go to a new round of the game, 
while retaining their scores.
"""
def next_round(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['next_round'] \
        and player_id in games[chat_id].players.keys():
        game = games[chat_id]
        #games[chat_id].state['next_round'] = False
        #games[chat_id].state['end_game'] = False
        #games[chat_id].state['players_assembled'] = True
        games[chat_id].change_state_false(['next_round', 'end_game']) 
        games[chat_id].change_state_true(['players_assembled']) 
        games[chat_id].dares.clear()
        games[chat_id].players_yet_to_play = list(game.players.keys())
        for key, value in game.players.items():
            games[chat_id].players[key] = [value[0], value[1], 0, False]
        context.bot.send_message(chat_id, 
                                'Next round has started, use /dare again so that everyone can'
                                ' input their dares for the next round!')

"""
This function is tied to the /endgame command,
which allows players to end the game to see who won the game 
and got the highest score amongst the players.
"""
def end_game(update, context):
    player = update.effective_user
    player_name = player.first_name
    player_id = player.id
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].state['end_game'] \
        and player_id in games[chat_id].players.keys():
        game = games[chat_id]
        highest_score = game.players[game.current_player_id][1]#definitely will have the last person with this score
        winning_player_ids = []
        for value in game.players.values():
            player_score = value[1]
            if player_score > highest_score:
                highest_score = player_score
        for key, value in game.players.items():
            if value[1] == highest_score:
                winning_player_ids.append(key)
        result = ''
        grammar = ''
        if len(winning_player_ids) == 1:
            grammar = ' winner is '
            player_data = game.players[winning_player_ids[0]]
            result += player_data[0] + ' with a score of ' + str(player_data[1])
        else:
            grammar = ' winners are\n'
            for each_id in winning_player_ids:
                result += game.players[each_id][0] + ' with a score of ' \
                    + str(game.players[each_id][1]) + '\n'
        context.bot.send_message(chat_id, 
                                "Aaaaand the" + grammar + result)
        context.bot.send_message(chat_id, 
                                "Thanks for playing! See you again, if you dare!!!")
        del games[chat_id]

"""
This function is tied to the /order command, 
which allows players to see who is currently having their turn
and in what order the turns are played.
"""
def order(update, context):
    chat_id = update.effective_chat.id
    if chat_id in games.keys() and games[chat_id].current_player_id:
        game = games[chat_id]
        current_player_name = game.players[game.current_player_id][0]
        numbering = 1
        order = ""
        for player in game.players_yet_to_play:
            if numbering < len(game.players_yet_to_play):
                order += "{}. {}\n".format(numbering, game.players[player][0])
                numbering += 1
            else:
                order += "{}. {}".format(numbering, game.players[player][0])
        if game.players_yet_to_play:
            context.bot.send_message(chat_id, 
                                    "Current player: {}\
                                    \nHere is the order of turns:\n{}"
                                    .format(current_player_name, order))
        else:
            context.bot.send_message(chat_id, 
                                    "Current player: {}"
                                    .format(current_player_name))


"""
This function is tied to the /cancel function, 
which allows players to cancel the game while it
is still ongoing.
"""
def cancel(update, context):
    chat_id = update.effective_chat.id
    player = update.effective_user
    player_id = player.id
    if chat_id in games.keys() and player_id in games[chat_id].players.keys():
        games[chat_id] = Game()
        context.bot.send_message(chat_id,
                                "The game has been cancelled!\
                                \nThanks for playing!")

"""
This function is tied to the /players command,
which allows players to see the current players in the game 
and their respective scores.
"""
def all_players(update, context):
    result = ''
    chat_id = update.effective_chat.id
    if chat_id in games.keys():
        for key, value in games[chat_id].players.items():
            player_name = value[0]
            player_score = value[1]
            result += player_name + ': ' + str(player_score) + '\n'
        if not result:
            context.bot.send_message(chat_id,
                                    'There are no players yet :(')
        else:
            context.bot.send_message(chat_id, result)


"""
This function is tied to the /help command,
which allows players to see all the commands needed
to get started with the game.
"""
def help(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id,
                            '/start: enter this to start the game\
                            \n/rules: explains the rules of the game\
                            \n/players: lists all the players in the game\
                            \nalong with their scores\
                            \n/cancel: cancels the game')

"""
This function is tied to the /rules command,
which allow players to get a grasp of how the game is to be played.
"""
def rules(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id,
                            "1. You and your friends will each suggest a dare.\
                            \n(If nothing comes to mind, we will provide you with our own dares)\
                            \n2. A dare suggested by your friends will be randomly allocated to you.\
                            \n3. When it is your turn, you can perform your dare or pass.\
                            \n4. If you accept, your friends will vote whether\
                            \nyou performed your dare satisfactorily.\
                            \n5. You will receive points based on majority vote.\
                            \n6. If you pass, the creator of the dare has to do it!")


"""
This function allows the various commands 
to be directed to the various functions.
"""
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('join', join))
    dp.add_handler(CommandHandler('gamestart', gamestart))
    dp.add_handler(CommandHandler('players', all_players))
    dp.add_handler(CommandHandler('cancel', cancel))
    dp.add_handler(CommandHandler('dare', input_dare))
    dp.add_handler(CommandHandler('accept', accept))
    dp.add_handler(CommandHandler('pass', pass_dare))
    dp.add_handler(CommandHandler('passmydare', pass_my_dare))
    dp.add_handler(CommandHandler('donedare', done_dare))
    dp.add_handler(CommandHandler('vote', check_rest))
    dp.add_handler(CommandHandler('nextround', next_round))
    dp.add_handler(CommandHandler('endgame', end_game))
    dp.add_handler(CommandHandler('order', order))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('rules', rules))

    updater.start_polling()
    """
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://damp-woodland-11141.herokuapp.com/' + TOKEN)
    """
    updater.idle()


if __name__ == '__main__':
    main()
