from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)

import random

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

players = {}
players_yet_to_play = [] #list of player_ids to determine who still haven't had their turns
dares = {}
voters = [] #list of player_ids to store valid voters, ie those not doing the dare
start_state = False
players_assembled = False
dares_received = False
doing_dare = False
end_game = False
collect_votes = False
#dare_num = 0 #num of dares done, replaced by players_yet_to_play :(
current_player_id = 0 #current player who has done dare
#votes = 0 #num of votes, replaced by voters :(
yes = 0 #num of /vote yes-es received

def start(update, context):
    global start_state
    global winning_score
    try:
        if start_state is False:
            #winning_score = int(context.args[0])
            start_state = True
            player_name = update.effective_user.first_name
            player_id = update.effective_user.id
            players[player_id] = [player_name, 0, '', 0]
            update.message.reply_text(player_name + " has started a game of DareToWin!\
                                    \nPlease enter /join to join the game!\
                                    \nEnter /gamestart when all players have joined!")
    except:
        update.message.reply_text('Please enter a winning score after /start')

def join(update, context):
    if start_state is True:
        player_name = update.effective_user.first_name
        player_id = update.effective_user.id
        if player_id not in players.keys():
            players[player_id] = [player_name, 0, '', 0]#place dare
            update.message.reply_text(player_name + " has /join -ed the game!\
                                      \nIf all players are here, /gamestart!")
        else:
            update.message.reply_text(player_name + " is already in the game!\
                                      \nWaiting for others to /join!\
                                      \nIf all players are here, /gamestart!")


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



def input_dare(update, context):
    global dares_received
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
                #added boolean flag to denote if dare has been assigned
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
                    value_dare = dares[dare_id]
                    value_player[2] = value_dare[2]
                    value_player[3] = value_dare[1]
                dares_received = True
                update.message.reply_text(players)
                update.message.reply_text("All dares have been placed, enter /getdare "
                                          "to get your dare!")
    except (ValueError, IndexError): #need IndexError to account for empty context.args
        update.message.reply_text("Please enter your dare in the following format:\
                                \n/dare 'number of points it's worth' 'your dare'")



def get_dare(update, context):
    global dares_received #Toggled to ensure only one player playing the turn
    global doing_dare
    global current_player_id
    global voters
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name
    if dares_received is True and player_id in players_yet_to_play:
        current_player_id = player_id
        players_yet_to_play.remove(player_id)
        voters = list(players.keys())
        voters.remove(current_player_id)
        assigned_dare = players[player_id][2]
        assigned_dare_points = players[player_id][3]
        doing_dare = True
        dares_received = False #Toggled off to ensure only this player is playing his turn
        update.message.reply_text(players_yet_to_play)
        update.message.reply_text('{}, your dare is {}, worth {} point(s).\
                                  \nEnter /donedare after you have sent a video of yourself doing the dare!'
                                  .format(player_name, assigned_dare, assigned_dare_points))


def done_dare(update, context):
    global collect_votes
    #global dare_num
    global doing_dare
    player = update.effective_user
    player_id = player.id
    player_name = player.first_name
    if doing_dare and player_id == current_player_id:
        doing_dare = False
        collect_votes = True
        update.message.reply_text("{} has done the dare! Now the rest will decide if {} has done it properly!\
                                  \nEnter '/vote yes' if the dare was done properly,\
                                  \nor '/vote no' if the dare was not done properly!"
                                  .format(player_name, player_name))
    elif doing_dare and player_id != current_player_id:
        update.message.reply_text("{}, it is not your turn!".format(player_name))


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
                #get points
                if yes >= ((len(players) - 1)/2):
                    dare_points = players[current_player_id][3]
                    new_points = current_points + dare_points
                    players[current_player_id][1] = new_points
                    update.message.reply_text(current_player_name + ' has done the dare well and now has ' +
                                              str(new_points) + ' points! Good job!')
                #minus points unless already at rock bottom aka 0
                else:
                    new_points = 0
                    if current_points > 0:
                        new_points = current_points - 1
                    players[current_player_id][1] = new_points
                    update.message.reply_text(current_player_name + ' has failed the dare and now has ' +
                                              str(new_points) + ' points :C, better luck next time!')
                yes = 0
                dares_received = True #Toggled for next player's turn

                if not players_yet_to_play:#able to go to 2 functions depending on input
                    end_game = True
                    next_round = True
                    update.message.reply_text('This round has now finished, enter /nextround to go'
                                              ' another round, or enter /endgame to finish the game'
                                              ' and see who the winner is')
                else:
                    update.message.reply_text('Next player please enter /getdare to get a new dare')


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
            players[key] = [value[0], value[1], '', 0]#to go round
        dare_num = dare_num % len(players)
        update.message.reply_text('Next round has started, use /dare again so that everyone can'
                                  ' input their dares for the next round!')


def end_game(update, context):
    global end_game
    #global win_player_id
    if end_game:
        highest_score = 0
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


def help(update, context):
    update.message.reply_text('/start: enter this along with a winning score to\
                              \nstart the game\
                              \n/rules: explains the rules of the game\
                              \n/players: lists all the players in the game\
                              \nalong with their score\
                              \n/cancel: cancels the game')


def rules(update, context):
    update.message.reply_text("1. You and your friends will each suggest a dare.\
                              \n(If nothing comes to mind, we will provide you with our own dares)\
                              \n2. A dare suggested by your friends will be randomly allocated to you.\
                              \n3. When it is your turn, you can perform your dare or pass.\
                              \n4. If you accept, your friends will vote whether\
                              \nyou performed your dare satisfactorily.\
                              \n5. You will receive points based on majority vote.")


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


def all_dares(update, context):
    alldares = ''
    for value in dares.values():
        alldares += value[0] +': ' + str(value[2]) + '\n'
    if not alldares: ##Checks if alldares is empty
        update.message.reply_text('There are no dares yet :(')
    else:
        update.message.reply_text(alldares)


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
