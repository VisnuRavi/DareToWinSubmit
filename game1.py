#19/05/2020

from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)

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
end_game = False
winning_score = 0
dare_num = 0
current_dare_points = 0
win_player_id = 0

def start(update, context):
    global start_state
    global winning_score
    try:
        if start_state is False:
            winning_score = int(context.args[0])
            start_state = True
            player_name = update.effective_user.first_name
            player_id = update.effective_user.id
            players[player_id] = [player_name, 0, False]
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
            players[player_id] = [player_name, 0, False]#place dare
            update.message.reply_text(player_name + " has /join -ed the game!\
                                      \nIf all players are here, /gamestart!")
        else:
            update.message.reply_text(player_name + " is already in the game!\
                                      \nWaiting for others to /join!")


def gamestart(update, context):
    global players_assembled
    if start_state is True and players_assembled is False:
        '''
        if len(players) == 1:
            update.message.reply_text("There is only 1 player in the game :(\
                                    \nPlease wait for more players to /join!\
                                    \nEnter /players to view all players!")
        '''
        players_assembled = True
        update.message.reply_text("Game start! Begin placing your dares!\
                                \nEnter your dare in the following format:\
                                \n/dare 'number of points it's worth' 'your dare'")


def input_dare(update, context):
    global dares_received
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name
    player_score = players[player_id][1]
    placed_dare = players[player_id][2]
    update.message.reply_text(str(players[player_id]) + ' ' + str(dares_received))
    try:
        if dares_received is False and not placed_dare:
            dare = ''
            points = int(context.args[0])
            for word in context.args[1:]:
                dare += word + ' '
            if not dare:
                raise ValueError("Invalid dare")
            dares[player_id] = [player_name, points, dare]
            players[player_id] = [player_name, player_score, True]
            update.message.reply_text(player_name + ', your dare has been placed!')
            
            if len(players) == len(dares):
                update.message.reply_text('All dares have been placed!\
                                            \nGet ready to receive your dare! type /getdare')
                dares_received = True
        else:
            update.message.reply_text(player_name + ', you have already placed a dare this round!')
    except ValueError:
        update.message.reply_text("Please enter your dare in the following format:\
                                \n/dare 'number of points it's worth' 'your dare'")




def get_dare(update, context):
    global dares_received
    global doing_dare
    global dare_num #if got assignment to global variabl(2nd last line) need this
    global current_dare_points
    if dares_received and not doing_dare:
        player_name = update.effective_user.first_name
        dare_num1 = 0
        for key,value in dares.items():
            if dare_num1 == dare_num:
                current_dare_points = value[1]
                dare = value[2]
                update.message.reply_text(player_name + ' dare is ' + dare + 'worth ' + 
                                         str(current_dare_points) + ', type /donedare after'
                                         'you have sent a video of doing the dare!')
                doing_dare = True
                break
            dare_num1 += 1
        dare_num += 1



def done_dare(update,context):
    global doing_dare
    global end_game
    global win_player_id
    global dares_received
    global dare_num
    if doing_dare:
        player = update.effective_user
        player_id = player.id
        player_name = player.first_name
        current_points = players[player_id][1]
        new_points = current_points + int(current_dare_points)#why typecast
        players[player_id][1] = new_points
        
        doing_dare = False
        if new_points >= int(winning_score):#typecast
            win_player_id = player_id
            update.message.reply_text("Oooh we have a winner! type /endgame to see!") 
            end_game = True

        elif dare_num == len(players):
            dares_received = False
            dares.clear()
            for key,value in players.items():
                players[key] = [value[0], value[1], False]#to go round

            dare_num = dare_num % len(players)
            update.message.reply_text('All dares have finished, but a winner has not been found.'
                                      ' Use /dare again so that everyone can input their dares for'
                                      ' the next round!')
        else:
            update.message.reply_text(player_name + ' has done the dare and now has ' + 
                                      str(new_points) + ' points'
                                  '\nNext player please enter /getdare to get a new dare')


def end_game(update, context):
    global end_game
    global win_player_id
    if end_game:
        win_player_name = players[int(win_player_id)][0]
        win_player_score = players[int(win_player_id)][1] 
        update.message.reply_text("Aaaaand the winner is " + win_player_name
                                    + ' with a score of ' + str(win_player_score))
        update.message.reply_text("Thanks for playing see you again, if you dare!!!")
        end_game = False
        dares.clear()
        players.clear()




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
