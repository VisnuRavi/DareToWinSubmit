#25/05/2020

from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)

import random

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

players = {}
dares = {}
start_state = False
players_assembled = False
dares_received = False
doing_dare = False
winning_score = 0


def start(update, context):
    global start_state
    #global winning_score
    #try:
    if start_state is False:
            #winning_score = int(context.args[0])
        start_state = True
        player_name = update.effective_user.first_name
        player_id = update.effective_user.id
        players[player_id] = [player_name, 0, '', 0] #added more fields to store active dare and its points
        update.message.reply_text("{} has started a game of DareToWin with a winning score of {}!\
                                    \nPlease enter /join to join the game!\
                                    \nEnter /gamestart when all players have joined!"
                                    .format(player_name, winning_score))
    #except:
    #   update.message.reply_text('Please enter a winning score after /start')

def join(update, context):
    if start_state is True:
        player_name = update.effective_user.first_name
        player_id = update.effective_user.id
        if player_id not in players.keys():
            players[player_id] = [player_name, 0, '', 0] #added more fields to store active dare and its points
            update.message.reply_text("{} has /join -ed the game!\
                                      \nIf all players are here, /gamestart!"
                                      .format(player_name))
        else:
            update.message.reply_text(player_name + " is already in the game!\
                                      \nWaiting for others to /join!\
                                      \nIf all players are here, /gamestart!")


def gamestart(update, context):
    global players_assembled
    player_id = update.effective_user.id
    if start_state is True and players_assembled is False and player_id in players.keys():
        if len(players) == 1:
            update.message.reply_text("There is only 1 player in the game :(\
                                    \nPlease wait for more players to /join!\
                                    \nEnter /players to view all players!")
        else:
            players_assembled = True
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
                dares[player_id] = [player_name, points, dare, False]
                #added boolean flag to denote if dare has been assigned
                update.message.reply_text('{}, your dare has been placed!'.format(player_name))
                if len(players) == len(dares): #all dares placed, shuffling dares
                    loop_counter = 0
                    for key, value in players.items():
                        loop_counter += 1
                        player_is_assigned_dare = value[2]
                        while not player_is_assigned_dare:
                            player_ids = list(players.keys())
                            player_ids.remove(key)
                            assigned_player_id = random.choice(player_ids)
                            assigned_player_name = dares[assigned_player_id][0]
                            dare_is_assigned = dares[assigned_player_id][3]
                            assigned_dare = dares[assigned_player_id][2]
                            assigned_dare_points = dares[assigned_player_id][1]
                            if not dare_is_assigned:
                                value[2] = assigned_dare
                                value[3] = assigned_dare_points
                                dares[assigned_player_id][3] = True
                                player_is_assigned_dare = True
                            elif len(players) % 2 != 0 and loop_counter == len(players) and not dares[key][3]:
                                temp_dare = players[assigned_player_id][2]
                                temp_points = players[assigned_player_id][3]
                                players[assigned_player_id][2] = dares[key][2]
                                value[2] = temp_dare
                                value[3] = temp_points
                                dares[key][3] = True
                                player_is_assigned_dare = True
                    update.message.reply_text('All dares have been placed!\
                                            \nGet ready to receive your dare! Type /getdare')
                    dares_received = True
            else:
                update.message.reply_text('{}, you have already placed a dare!'.format(player_name))
    except (ValueError, IndexError):
        update.message.reply_text("Please enter your dare in the following format:\
                                \n/dare 'number of points it's worth' 'your dare'")


def get_dare(update, context):
    player_id = update.effective_user.id
    if dares_received is True and player_id in players.keys():
        player_name = update.effective_user.first_name
        assigned_dare = players[player_id][2]
        assigned_dare_points = players[player_id][3]
        update.message.reply_text("{}, your dare is '{}', worth {} points"
                                  .format(player_name, assigned_dare, assigned_dare_points))


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


def end_game(update, context):
    win_player_id = 0
    for key, value in players.items():
        if value[1] >= winning_score:
            win_player_id = key

    win_player_name = players[win_player_id][0]
    win_player_score = players[win_player_id][1]
    update.message.reply_text("Aaaaand the winner is " + win_player_name
                                + ' with a score of ' + str(win_player_score))
    update.message.reply_text("Thanks for playing see you again, if you dare!!!")
    return ConversationHandler.END


def cancel(update, context):
    global start_state
    global players_assembled
    global dares_received
    if start_state == True:
        start_state = False
        players_assembled = False
        dares_received = False
        dares.clear()
        players.clear()
        update.message.reply_text("The game has been cancelled!\
                                \nThanks for playing!")


def all_dares(update, context):
    alldares = ''
    for value in dares.values():
        alldares += value[0] +': ' + value[2] + '\n'
    if not alldares: ##Checks if alldares is empty
        update.message.reply_text('There are no dares yet :(')
    else:
        update.message.reply_text(alldares)


def main():
    updater = Updater("TOKEN", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('join', join))
    dp.add_handler(CommandHandler('gamestart', gamestart))
    dp.add_handler(CommandHandler('dare', input_dare))
    dp.add_handler(CommandHandler('getdare', get_dare))
    dp.add_handler(CommandHandler('cancel', cancel))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('rules', rules))
    dp.add_handler(CommandHandler('players', all_players))
    dp.add_handler(CommandHandler('alldares', all_dares))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
