from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

players = {}
dares = {}
winning_score = 0
dare_num = 0
current_dare_points = 0
START, INPUT, GETDARE, DONEDARE, ENDGAME = range(5)


def start(update, context):
    player_name = update.effective_user.first_name
    player_id = update.effective_user.id
    global winning_score
    winning_score = context.args[0]
    players[player_id] = [player_name, 0]
    update.message.reply_text(player_name + " has started a game of DareToWin!\
                              \nPlease enter /join to join the game!\
                              \nEnter /gamestart when all players have joined!")
    return START


def help(update, context):
    update.message.reply_text('/rules: explains the rules of the game\
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
    if players:
        for key, value in players.items():
            player_name = value[0]
            player_score = value[1]
            result += player_name + ': ' + str(player_score) + '\n'
    update.message.reply_text(result)
    


def join(update, context):
    player_name = update.effective_user.first_name
    player_id = update.effective_user.id
    if player_id not in players.keys():
        players[player_id] = [player_name, 0]
        update.message.reply_text(player_name + " has joined the game!")
        return START
    else:
        update.message.reply_text(player_name + " is already in the game!")
        return START


def gamestart(update, context):
    player_name = update.effective_user.first_name
    '''
    if len(players) == 1:
        update.message.reply_text(player_name + ", you're the only player in the game :(\
                                  \nPlease wait for more players to join!")
        return START
    '''
    update.message.reply_text('Game start! Begin placing your dares!\
                              \nType /dare before your dare!')
    return INPUT


def input_dares(update, context):
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name
    if player_id not in dares.keys():
        dare = ''
        points = context.args[0]
        dare_list = context.args
        #dare_list.pop[0] not working tho?
        for word in dare_list:
            dare += word + ' '
        dares[player_id] = [player_name, points, dare]
        update.message.reply_text(player_name + ', your dare has been placed!')
        if len(players) == len(dares):
            update.message.reply_text('All dares have been placed!\
                                      \nGet ready to receive your dare! type /getdare')
        return GETDARE

    else:
        update.message.reply_text(player_name + ', you have already placed a dare!')
        return INPUT


def get_dare(update, context):
    player_name = update.effective_user.first_name
    global dare_num
    dare_num1 = 0
    for key,value in dares.items():
        
        if dare_num1 == dare_num:
            global current_dare_points
            current_dare_points = value[1]
            dare = value[2]
            update.message.reply_text(player_name + ' dare is ' + dare + ', type '
                                     '/donedare after you have sent a video of doing '
                                     'the dare!')
            break
        dare_num1 += 1

    dare_num += 1
    return DONEDARE



def done_dare(update,context):
    player = update.effective_user
    player_id = player.id
    player_name = player.first_name
    current_points = players[player_id][1]
    #global current_dare_points
    new_points = current_points + int(current_dare_points)#why typecast
    players[player_id][1] = new_points
    update.message.reply_text(player_name + ' has done the dare and now has ' + str(new_points) + ' points\n'
                              'type /getdare after 1 round of the game has completed to get a new dare')
    #global winning_score
    if new_points >= int(winning_score):#typecast
            update.message.reply_text("Oooh we have a winner! type /endgame to see!") 
            return ENDGAME

    return GETDARE  #need to input new dares but can think about it later


def end_game(update, context):
    win_player_id = 0
    for key, value in players.items():
        if value[1] >= int(winning_score):#typecast
            win_player_id = key
            break

    win_player_name = players[win_player_id][0]
    win_player_score = players[win_player_id][1] 
    update.message.reply_text("Aaaaand the winner is " + win_player_name
                                + ' with a score of ' + str(win_player_score))
    update.message.reply_text("Thanks for playing see you again, if you dare!!!")
    dares.clear()
    players.clear()
    return ConversationHandler.END



def cancel(update, context):
    dares.clear()
    players.clear()
    update.message.reply_text("The game has been cancelled!\
                              \nThanks for playing!")
    return ConversationHandler.END

def all_dares(update, context):
    daress = ''
    if dares:
        for value in dares.values():
            daress += value[0] +': ' + value[2] + ' worth ' + value[1] + 'points\n'
    update.message.reply_text(daress)


def main():
    updater = Updater("TOKEN", use_context=True)
    dp = updater.dispatcher
    game_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('join', join)],
        states={
            START: [CommandHandler('join', join),
                    CommandHandler('gamestart', gamestart)],
            #INPUT: [MessageHandler(Filters.regex(r'/dare'), input_dares)]
            INPUT: [CommandHandler('dare', input_dares)],
            GETDARE: [CommandHandler('getdare', get_dare)],
            DONEDARE:[CommandHandler('donedare', done_dare)],
            ENDGAME: [CommandHandler('endgame', end_game)]

        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(game_handler)
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('rules', rules))
    dp.add_handler(CommandHandler('players', all_players))
    dp.add_handler(CommandHandler('alldares', all_dares))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
