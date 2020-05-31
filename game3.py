from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)

import random

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

players = {} #dictionary to store all players who have joined the game and their data
players_yet_to_play = [] #list of player_ids to determine who still haven't had their turns
dares = {} #dictionary to store the dares that the players have come up with for the round
voters = [] #list of player_ids to store valid voters, ie those not doing the dare
start_state = False #boolean flag to indicate if a user has started a game of DareToWin, through /start, for others to /join
players_assembled = False #boolean flag to indicate that /gamestart is called and game will be starting
"""
boolean flag to indicate that every player has entered their dares through /dare.
also toggled to ensure no other player can effectively input commands during the current player's turn.
refer to get_dare, pass_my_dare and check_rest functions.
"""
dares_received = False
accept = False #boolean flag to indicate that a player has accepted their dare
pass_dare = False #boolean flag to indicate that a player has passed their dare to its creator
doing_dare = False #boolean flag to indicate that a player is currently performing their dare
collect_votes = False #boolean flag to indicate that other players are currently voting for the current player's dare
next_round = False #boolean flag to indicate that players intend to go for another round of the game
end_game = False #boolean flag to indicate that players intend to end the game and determine a winner
group_id = 0 #id number of the Telegram group that is playing the game
#dare_num = 0 #num of dares done, replaced by players_yet_to_play :(
current_player_id = 0 #id of the player who is currently having their turn
#votes = 0 #num of votes, replaced by voters :(
yes = 0 #num of /vote yes-es received

"""
this function is tied to the /start command, which allows a user to start a game of DareToWin,
allowing others to join
"""
def start(update, context):
    global start_state
    global winning_score
    global group_id
    try:
        if start_state is False:
            group_id = update.effective_chat.id
            start_state = True
            player_name = update.effective_user.first_name
            player_id = update.effective_user.id
            players[player_id] = [player_name, 0, 0, False]#index 2 is now the dareId, id of dare creator of
                                                           #dare assigned to this player in input_dare random part
                                                           #index 3 is True if got own dare from pass function
            update.message.reply_text(player_name + " has started a game of DareToWin!\
                                    \nPlease enter /join to join the game!\
                                    \nEnter /gamestart when all players have joined!")
    except:
        update.message.reply_text('Please enter a winning score after /start')

        
"""
this function is tied to the /join command which allows other users in the group to join the game
after someone else has started it with /start
"""
def join(update, context):
    if start_state is True:
        player_name = update.effective_user.first_name
        player_id = update.effective_user.id
        if player_id not in players.keys():
            players[player_id] = [player_name, 0, 0, False]#place dare
            update.message.reply_text(player_name + " has /join -ed the game!\
                                      \nIf all players are here, /gamestart!")
        else:
            update.message.reply_text(player_name + " is already in the game!\
                                      \nWaiting for others to /join!\
                                      \nIf all players are here, /gamestart!")


"""
this function is tied to the /gamestart command, which allows the group to finalise its
players and begin the game
"""
def gamestart(update, context):
    global players_assembled
    global players_yet_to_play
    if start_state is True and players_assembled is False:
        if len(players) == 1:
            update.message.reply_text("There is only 1 player in the game :(\
                                    \nPlease wait for more players to /join!\
                                    \nEnter /players to view all players!")
        else:
            players_assembled = True
            players_yet_to_play = list(players.keys())
            update.message.reply_text("Game start! Begin placing your dares!\
                                    \nEnter your dare in the following format:\
                                    \n/dare 'number of points it's worth' 'your dare'")
            #all_dares_in(update, context)


"""
don't think this is used anymore?
"""
def all_dares_in(update, context):
    global dares_received
    #update.message.reply_text('in check if all dares in')
    while True:
        if dares_received:
            break
    update.message.reply_text('All dares are in, enter /getdare to get your dare!')
    

"""
this function is tied to the /dare command, which allows players to enter the number of points their dares are worth
and the dares themselves.
after every player has placed their dares, they will be randomly allocated another player's dare.
"""
def input_dare(update, context):
    global dares_received
    global group_id
    player_id = update.effective_user.id
    try:
        if players_assembled is True and dares_received is False and player_id in players.keys():
            player_id = update.effective_user.id
            player_name = update.effective_user.first_name
            if player_id not in dares.keys():
                dare = ''
                points = int(context.args[0])
                for word in context.args[1:]:
                    dare += word + ' '
                if not dare:
                    raise ValueError("Invalid dare")
                dares[player_id] = [player_name, points, dare]
            update.message.reply_text('{}, your dare has been placed!'.format(player_name))

            if len(players) == len(dares):
                players_ids = list(players.keys())
                dares_ids = list(dares.keys())
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
                    value_player = players[player_id]
                    value_player[2] = dare_id
                dares_received = True
                #update.message.reply_text(players)
                context.bot.send_message(group_id, "All dares have been placed, enter /getdare "
                                          "to get your dare!")
    except (ValueError, IndexError): #need IndexError to account for empty context.args
        update.message.reply_text("Please enter your dare in the following format:\
                                \n/dare 'number of points it's worth' 'your dare'")


"""
this function is tied to the /getdare command, which allows players to receive the dare allocated to them.
this also locks them into their turn such that no other player can receive their dare until this player
has finished their turn.
"""
def get_dare(update, context):
    global dares_received #Toggled to ensure only one player playing the turn
    global current_player_id
    global voters
    global accept
    global pass_dare
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name
#    update.message.reply_text(player_name + ' in get_dare ' + str(players_yet_to_play))

    if dares_received is True and player_id in players_yet_to_play:
        accept = True
        pass_dare = True
        current_player_id = player_id
        dare_id = players[player_id][2]
        assigned_dare = dares[dare_id][2]
        assigned_dare_points = dares[dare_id][1]
        dares_received = False #Toggled off to ensure only this player is playing his turn
        players_yet_to_play.remove(current_player_id)
 #       update.message.reply_text(players_yet_to_play)
        #goes to either accept or pass
        update.message.reply_text(player_name + ' dare is ' + assigned_dare + 'worth ' + 
                                  str(assigned_dare_points) + ', enter /accept if you accept'
                                  ' or /pass if you want to pass the dare to its creator to do it!')


"""
this function is tied to the /accept command, which allows players, currently playing their turn, 
to accept the dare and commit to performing it.
"""
def accept(update, context):
    global doing_dare
    global accept
    global pass_dare
    global voters
    global current_player_id
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name
    if accept and player_id == current_player_id:
        doing_dare = True
        accept = False
        pass_dare = False
        voters = list(players.keys())
        voters.remove(current_player_id)
        update.message.reply_text(player_name + ' has accepted the dare! Enter /donedare after you have '
                                  ' sent a video of yourself doing the dare, ' + player_name)

        
"""
this function is tied to the /pass command, which allows players, currently playing their turn,
to pass the dare to its original creator.
"""
def pass_dare(update,context):
    global doing_dare
    global accept
    global pass_dare
    global voters
    global current_player_id
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name
    if pass_dare and player_id == current_player_id:
        doing_dare = True
        accept = False
        dare_id = players[player_id][2]
        current_player_id = dare_id
        players[current_player_id][3] = True #got own dare so set to true
        dare_creator_name = players[current_player_id][0]
        voters = list(players.keys())
        voters.remove(current_player_id)
        update.message.reply_text(player_name + ' has passed the dare, now the dare has fallen'
                                  ' to its creator, ' + dare_creator_name + '. ' + dare_creator_name +
                                  ' please send a video of yourself doing your dare, and then enter /donedare.'
                                  ' However, if you cant/dont even want to attempt your own dare, enter'
                                  ' /passmydare')


"""
this function is tied to the /passmydare command, which allows the creator of a dare,
when their own dare has been passed back to them during another player's turn,
to pass up on doing it.
"""
def pass_my_dare(update, context):
    global doing_dare
    global pass_dare
    global voters
    global dares_received
    global end_game
    global next_round
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name
    own_dare = players[player_id][3]
    if pass_dare and own_dare:
        players[player_id][3] = False
        doing_dare = False
        pass_dare = False
        voters.clear() #since no voting as completely passed this dare
        current_score = players[player_id][1]
        new_score = current_score - 2
        players[player_id][1] = new_score
        update.message.reply_text(player_name + ' has chickened out of his/her dare and has lost 2 points, to'
                                  ' now have ' + str(new_score) + ' points!')
        dares_received = True #Toggled for next player's turn
        if not players_yet_to_play:#able to go to 2 functions depending on input
            end_game = True
            next_round = True
            update.message.reply_text('This round has now finished, enter /nextround to go'
                                      ' another round, or enter /endgame to finish the game'
                                      ' and see who the winner is')
        else:
            update.message.reply_text('Next player please enter /getdare to get a new dare')

                                  
"""
this function is tied to the /donedare command, which allows players, who are currently playing their turn,
to indicate that they have completed their dare.
"""
def done_dare(update, context):
    global collect_votes
    #global dare_num
    global doing_dare
    global pass_dare
    player = update.effective_user
    player_id = player.id
    player_name = player.first_name
    if doing_dare and player_id == current_player_id:
        pass_dare = False
        doing_dare = False
        collect_votes = True
        update.message.reply_text(player_name + ' has done the dare! Now the rest will decide'
                                  ' if ' + player_name + ' has done it properly!'
                                  '\nEnter /vote followed by yes if dare has been done properly'
                                  ', and /vote followed by no if dare was not done properly, or'
                                  ' if you are EEEVIIIL MUAHAHAHA!!!')
    elif doing_dare and player_id != current_player_id:
        update.message.reply_text("{}, it is not your turn!".format(player_name))



'''
check_rest can be called to collect all the votes after a player submits dare.
If more than half of the remaining players vote yes, the current player gets the
points allocated to the dare. If more than half of the remaining players vote no,
and if current player is the one who created the dare, he gets 2 points minused off,
otherwise he gets 1 point minused off. Then the next player is allowed to call
get_dare, and get his dare, or if all players have finished this round, players can
either choose to go another round or end the game.

'''
#comes here for vote checking
def check_rest(update, context):
    global dares_received #Toggled to ensure only one player playing the turn
    global end_game
    #global dare_num
    global next_round
    global collect_votes
    global current_player_id
    global voters
    global yes
    if collect_votes:
        player = update.effective_user
        player_id = player.id
        player_name = player.first_name
        current_player_name = players[current_player_id][0]
        if player_id == current_player_id:
            update.message.reply_text('Yea nice try to game the system ' + player_name
                                      + ' but its not gonna work. You cant vote for yourself!')
        elif player_id in voters:
            try:
                if context.args[0] == 'yes':
                    voters.remove(player_id)
                    yes += 1
                    update.message.reply_text("{} has acknowledged {}'s dare!"
                                            .format(player_name, current_player_name))
                elif context.args[0] == 'no':
                    voters.remove(player_id)
                    update.message.reply_text("{} stares disapprovingly at {}"
                                            .format(player_name, current_player_name))
                else:
                    raise Exception("Invalid vote")
            except Exception:
                update.message.reply_text("{}, please enter '/vote yes' if \
                                          \nthe dare was done properly,\
                                          \nor '/vote no' if the dare was not done properly!"
                                          .format(player_name))

            #all votes collected
            if not voters:
                collect_votes = False
                current_points = players[current_player_id][1]
                current_player_name = players[current_player_id][0]
                own_dare = players[current_player_id][3]
                #get points
                if yes >= ((len(players) - 1)/2):
                    dare_id = 0
                    if own_dare:
                        dare_id = current_player_id
                    else:
                        dare_id = players[current_player_id][2]
                    dare_points = dares[dare_id][1]
                    new_points = current_points + dare_points
                    players[current_player_id][1] = new_points
                    update.message.reply_text(current_player_name + ' has done the dare well and now has ' +
                                              str(new_points) + ' points! Good job!')
                #minus points unless already at rock bottom aka 0
                else:
                    new_points = 0
                    if own_dare:
                        new_points = current_points - 2
                    else:
                        new_points = current_points - 1
                    players[current_player_id][1] = new_points
                    update.message.reply_text(current_player_name + ' has failed the dare and now has ' +
                                              str(new_points) + ' points :C, better luck next time!')
                yes = 0
                players[player_id][3] = False
                dares_received = True #Toggled for next player's turn

                if not players_yet_to_play:#able to go to 2 functions depending on input
                    end_game = True
                    next_round = True
                    update.message.reply_text('This round has now finished, enter /nextround to go'
                                              ' another round, or enter /endgame to finish the game'
                                              ' and see who the winner is')
                else:
                    update.message.reply_text('Next player please enter /getdare to get a new dare')

'''
next_round allows players to go to a new round of the game, while retaining their scores
'''
def next_round(update,context):
    global dares_received
    global dare_num
    global next_round
    global end_game
    global players_yet_to_play
    if next_round:
        end_game = False
        dares_received = False
        dares.clear()
        players_yet_to_play = list(players.keys())
        for key,value in players.items():
            players[key] = [value[0], value[1], 0, False]#to go round
        update.message.reply_text('Next round has started, use /dare again so that everyone can'
                                  ' input their dares for the next round!')
        #all_dares_in()

'''
end_game allows players to end the game to see who won the game and got the highest score
amongst the players
'''
def end_game(update, context):
    global end_game
    #global win_player_id
    if end_game:
        highest_score = players[current_player_id][1]#definitely will have the last person with this score
        winning_player_ids = []
        for value in players.values():
            player_score = value[1]
            if player_score > highest_score:
                highest_score = player_score

        for key, value in players.items():
            if value[1] == highest_score:
                winning_player_ids.append(key)
        result = ''
        grammar = ''
        if len(winning_player_ids) == 1:
            grammar = ' winner is '
            player_data = players[winning_player_ids[0]]
            result += player_data[0] + ' with a score of ' + str(player_data[1])
        else:
            grammar = ' winners are\n'
            for each_id in winning_player_ids:
                result += players[each_id][0] + ' with a score of '+ str(players[each_id][1]) + '\n'
        update.message.reply_text("Aaaaand the" + grammar + result)
        update.message.reply_text("Thanks for playing! See you again, if you dare!!!")
        #end_game = False #if wanna continue after end? everything need
        dares.clear()
        players.clear()
        players_yet_to_play.clear() #probably unnecessary as it should already be empty

'''
help allows players to see the commands that can be used to start the game, the rules of
the game, current players of the game together with their score, and to cancel the current game 
'''
def help(update, context):
    update.message.reply_text('/start: enter this to start the game\
                              \n/rules: explains the rules of the game\
                              \n/players: lists all the players in the game\
                              \nalong with their score\
                              \n/cancel: cancels the game')

'''
rules allow players to get a grasp of how the game is to be played
'''
def rules(update, context):
    update.message.reply_text("1. You and your friends will each suggest a dare.\
                              \n(If nothing comes to mind, we will provide you with our own dares)\
                              \n2. A dare suggested by your friends will be randomly allocated to you.\
                              \n3. When it is your turn, you can perform your dare or pass.\
                              \n4. If you accept, your friends will vote whether\
                              \nyou performed your dare satisfactorily.\
                              \n5. You will receive points based on majority vote.\
                              \n6. If you pass, the creator of the dare has to do it!")

'''
all_players allows players to see the current players in the game and their respective scores
'''
def all_players(update, context):
    result = ''
    for key, value in players.items():
        player_name = value[0]
        player_score = value[1]
        result += player_name + ': ' + str(player_score) + '\n'
    if not result:
        update.message.reply_text('There are no players yet :(')
    else:
        update.message.reply_text(result)

'''
cancel allows players to cancel the game halfway if they need to quickly end the game
'''
def cancel(update, context):
    global start_state
    global players_assembled
    global dares_received
    global doing_dare
    if start_state == True:
        start_state = False
        players_assembled = False
        dares_received = False
        doing_dare = False
        dares.clear()
        players.clear()
        players_yet_to_play.clear()
        update.message.reply_text("The game has been cancelled!\
                                \nThanks for playing!")

'''
all_dares can be used to see what are the dare that have been placed. However, this is more
of a debugging function, and players will not have this function in the actual game
'''
def all_dares(update, context):
    alldares = ''
    for value in dares.values():
        alldares += value[0] +': ' + str(value[2]) + '\n'
    if not alldares: ##Checks if alldares is empty
        update.message.reply_text('There are no dares yet :(')
    else:
        update.message.reply_text(alldares)

'''
main allows the various commands to be directed to the various functions
'''
def main():
    updater = Updater("TOKEN", use_context=True)
    dp = updater.dispatcher
    """
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CommandHandler('join', join),
                    CommandHandler('gamestart', gamestart)],
            INPUT: [CommandHandler('dare', input_dares)],
            GETDARE: [CommandHandler('getdare', get_dare)],
            ENDGAME: [CommandHandler('endgame', end_game)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    """
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('join', join))
    dp.add_handler(CommandHandler('gamestart', gamestart))
    dp.add_handler(CommandHandler('dare', input_dare))
    dp.add_handler(CommandHandler('getdare', get_dare))
    dp.add_handler(CommandHandler('accept', accept))
    dp.add_handler(CommandHandler('pass', pass_dare))
    dp.add_handler(CommandHandler('passmydare', pass_my_dare))
    dp.add_handler(CommandHandler('donedare', done_dare))
    dp.add_handler(CommandHandler('vote', check_rest))
    dp.add_handler(CommandHandler('nextround', next_round))
    dp.add_handler(CommandHandler('endgame', end_game))
    dp.add_handler(CommandHandler('cancel', cancel))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('rules', rules))
    dp.add_handler(CommandHandler('players', all_players))
    dp.add_handler(CommandHandler('alldares', all_dares))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

