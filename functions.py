from os.path import isfile, getsize


def get_token():
    """
    We check the existence of a file with a token and return its value, if it does not exist,
    we request a token from the user and return it by saving it to a file
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
