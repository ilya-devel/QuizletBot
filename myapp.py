import telebot
from classes import DataBase, User
from functions import get_token

token = get_token()
bot = telebot.TeleBot(token)

db = DataBase()

with open('img.png', 'rb') as f:
    welcome = f.read()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, welcome)
    user = db.get_user(message.chat.id)
    # print(user.chat_id)
    # print(user.status['answers'])

    if user.status['is_passing']:
        return

    db.set_user(message.chat.id, current_index=0, is_passing=True)
    post = get_question_message(user)
    if post is not None:
        bot.send_message(message.chat.id, post['text'], reply_markup=post['keyboard'])


@bot.message_handler(func=lambda msg: msg.text == 'Да' or 'Нет')
def answered(msg):
    user = db.get_user(msg.chat.id)
    # print(user.status['answers'])
    if user.status['is_passed'] or not user.status['is_passing']:
        return

    user.status['answers'].append(True if msg.text == 'Да' else False)
    user.status['current_index'] += 1
    post = get_question_message(user)
    if post is not None:
        # print(f'send message {msg.chat.id}')
        if post['keyboard'] == None:
            bot.send_message(msg.chat.id, post['text'], reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            bot.send_message(msg.chat.id, post['text'], reply_markup=post['keyboard'])


def get_question_message(user: User):
    if user.status['current_index'] == db.questions_count:
        result = user.get_character()
        db.users.remove(user)
        # print(db.users)
        return {'text': result, 'keyboard': None}
    question = db.get_question(user.status['current_index'])
    if question is None:
        return
    keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for ans in ['Да', 'Нет']:
        keyboard.add(telebot.types.InlineKeyboardButton(f'{ans}', callback_data=f'?ans&{ans}'))

    text = f'Вопрос №{user.status["current_index"] + 1}\n\n{question}'
    return {
        'text': text,
        'keyboard': keyboard
    }


def get_answered_message(user: User):
    text = f"Ваш ответ: {'Да' if user.status['answers'][user.status['current_index']] == True else 'Нет'}"
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton('Далее', callback_data='?next'))
    return {
        'text': text,
        'keyboard': keyboard
    }


bot.polling()
