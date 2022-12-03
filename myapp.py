import telebot
import characters
from os.path import getsize, isfile


def get_token():
    """
    We check the existence of a file with a token and return its value, if it does not exist, we request a token from the user and return it by saving it to a file
    :return: token string
    """
    if isfile('bot.token') and getsize('bot.token') > 10:
        with open('bot.token', 'r') as f:
            return f.read()
    else:
        with open('bot.token', 'w') as f:
            token = input('Enter token for bot: ')
            f.write(token)
            return token


token = get_token()
bot = telebot.TeleBot(token)

users = []


class User:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.status = {
            'is_passing': False,
            'is_passed': False,
            'current_index': -1,
            'answers': []
        }

    def get_result(self):
        lears = sum([1 if (self.status['answers'][x] and x in (5, 23, 35)) or (
                not self.status['answers'][x] and x in (11, 17, 29, 41, 47, 53)) else 0 for x in
                     range(len(self.status['answers']))])
        extra = sum([1 if (self.status['answers'][x] and x in (0, 2, 7, 9, 12, 16, 21, 24, 26, 38, 43, 45, 48, 52)) or (
                not self.status['answers'][x] and x in (4, 14, 19, 28, 31, 33, 36, 40, 50)) else 0 for x in
                     range(len(self.status['answers']))])
        neuro = sum([1 if (self.status['answers'][x] and x in (
            1, 3, 6, 8, 10, 13, 15, 18, 20, 22, 25, 27, 30, 32, 34, 37, 39, 42, 44, 46, 49, 51, 54, 56)) else 0 for x in
                     range(len(self.status['answers']))])
        intro = sum([1 if (self.status['answers'][x] and x in (4, 14, 19, 28, 31, 33, 36, 40, 50)) else 0 for x in
                     range(len(self.status['answers']))])
        return {
            'lear': lears,
            'extravert': extra,
            'introvert': intro,
            'neurotism': neuro
        }

    def get_character(self):
        result = self.get_result()
        text = ''

        if result['lear'] > 4:
            text += f'Есть неискренность в ответах, свидетельствующая также о некоторой демонстративности поведения и' \
                    f' ориентированности на социальное одобрение. Рекомендуется пройти тестирование повторно\n '

        ex_in = result['extravert'] - result['introvert']

        if ex_in > 19:
            text += f'Вы яркий экстраверт '
        elif ex_in > 15:
            text += f'Вы экстраверт '
        elif ex_in > 12:
            text += f'У вас есть склонность к экстраверсии '
        elif ex_in == 12:
            text += f'У вас среднее значение между экстравертом и интровертом '
        elif ex_in > 9:
            text += f'У вас склонность к интроверсии '
        elif ex_in > 5:
            text += f'Вы интроверт '
        elif ex_in < 5:
            text += f'Вы глубокий интроверт '

        if result['neurotism'] > 19:
            text += f'+ очень высокий уровень нейротизма\n'
        elif result['neurotism'] > 13:
            text += f'+ высокий уровень нейротизма\n'
        elif 9 <= result['neurotism'] <= 13:
            text += f'+ среднее значение нейротизма\n'
        elif result['neurotism'] < 9:
            text += f'+ низкий уровень нейротизма\n'

        text += '\nОбщая оценка вашего характера:\n\n'
        if (9 <= result['neurotism'] <= 13) and (ex_in == 12):
            text += 'Ваш характер золотая середина, а значит встречаются черты всех четырёх типов (сагвиника, ' \
                    'холерика, флегматика и меланхолика) '
        elif (result['neurotism'] < 13) and (ex_in > 12):
            text += characters.characters['holer']
        elif (result['neurotism'] > 9) and (ex_in > 12):
            text += characters.characters['sang']
        elif (result['neurotism'] < 13) and (ex_in < 12):
            text += characters.characters['melan']
        elif (result['neurotism'] > 9) and (ex_in < 12):
            text += characters.characters['flegm']

        return text


class DataBase:
    def __init__(self):
        global users
        self.users = users
        self.questions = []
        with open('question_list.txt', 'r') as f:
            self.questions = [x.strip() for x in f.readlines()]
        self.questions_count = len(self.questions)

    def get_user(self, chat_id):
        for user in self.users:
            if user.chat_id == chat_id:
                return user
        user = User(chat_id)
        self.users.append(user)
        return user

    def set_user(self, chat_id, **kwargs):
        for user in self.users:
            if user.chat_id == chat_id:
                for key in kwargs.keys():
                    user.status[key] = kwargs[key]

    def get_question(self, index):
        return self.questions[index]


db = DataBase()


@bot.message_handler(commands=['start'])
def start(message):
    user = db.get_user(message.chat.id)
    # if user.status['is_passed']:
    #     bot.send_message(message.chat.id, "Вы уже прошли эту викторину. Второй раз пройти нельзя 😥")
    #     return

    if user.status['is_passing']:
        return

    db.set_user(message.chat.id, current_index=0, is_passing=True)
    post = get_question_message(user)
    if post is not None:
        bot.send_message(message.chat.id, post['text'], reply_markup=post['keyboard'])


@bot.callback_query_handler(func=lambda query: query.data.startswith('?ans&'))
def answered(query):
    user = db.get_user(query.message.chat.id)
    if user.status['is_passed'] or not user.status['is_passing']:
        return

    user.status['answers'].append(True if query.data.split('&')[1] == 'Да' else False)

    post = get_answered_message(user)
    if post is not None:
        bot.edit_message_text(post['text'], query.message.chat.id, query.message.id, reply_markup=post['keyboard'])


@bot.callback_query_handler(func=lambda query: query.data == '?next')
def next(query):
    user = db.get_user(query.message.chat.id)
    if user.status['is_passed'] or not user.status['is_passing']:
        return
    user.status['current_index'] += 1

    post = get_question_message(user)
    if post is not None:
        bot.edit_message_text(post['text'], query.message.chat.id, query.message.id, reply_markup=post['keyboard'])


def get_question_message(user: User):
    if user.status['current_index'] == db.questions_count:
        result = user.get_character()
        db.set_user(user.chat_id, is_passed=True, is_passing=False)
        return {'text': result, 'keyboard': None}
    question = db.get_question(user.status['current_index'])
    if question is None:
        return
    keyboard = telebot.types.InlineKeyboardMarkup()
    for ans in ['Да', 'Нет']:
        keyboard.row(telebot.types.InlineKeyboardButton(f'{ans}', callback_data=f'?ans&{ans}'))

    text = f'Вопрос №{user.status["current_index"] + 1}\n\n{question}'
    return {
        'text': text,
        'keyboard': keyboard
    }


def get_answered_message(user: User):
    question = db.get_question(user.status['current_index'])
    text = f"Вопрос №{user.status['current_index'] + 1}\n\n{question}\n" \
           f"Ваш ответ: {'Да' if user.status['answers'][user.status['current_index']] == True else 'Нет'}"

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(telebot.types.InlineKeyboardButton('Далее', callback_data='?next'))
    return {
        'text': text,
        'keyboard': keyboard
    }


bot.polling()
