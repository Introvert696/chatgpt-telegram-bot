import openai
import telebot
import logging
import os
import time
import datetime
import re
from telebot.types import InputFile
import log_utils


# получение настроек


def getOpenAiToken():
    f = open(OPENAI_TOKEN_PATH, "r")
    openaitoken = f.readlines()
    f.close()
    return openaitoken[0]


def getTgbotToken():
    f = open(TGBOT_TOKEN_PATH, "r")
    bottoken = f.readlines()
    f.close()
    return bottoken[0]


def getAdminList():
    f = open(ADMIN_LIST_PATH, "r")
    adminlist = f.readlines()
    f.close()
    return adminlist


# константы путей до файлов
WHITE_LIST_PATH = "cfg/whitelist.txt"
LOG_DB_PATH = "log/log.db"
ADMIN_LIST_PATH = "cfg/adminlist.txt"
OPENAI_TOKEN_PATH = "cfg/openaitoken.txt"
TGBOT_TOKEN_PATH = "cfg/tgbottoken.txt"

# присвойка токенов
openai_token = getOpenAiToken()
admin_list = getAdminList()
telgram_bot_token = getTgbotToken()

welcome_message = "Привет, это Бот ChatGPT. Здесь вы можете задать любой вопрос и получить на него ответ. Так же вы можете сгенерировать картику командой /image (текст запроса) . "
message_for_not_white_list_users = " . Вас нету в вайтлисте, обратитесь к https://t.me/Bojlodya чтобы получить доступ"

openai.api_key = openai_token
bot = telebot.TeleBot(telgram_bot_token)

# функция для генерации ответа


def generate_response(prompt):
    try:
        response = completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])

        return completion.choices[0].message.content
    except Exception as ex:
        log_utils.inlog('ERROR', 'SERVER', 0,
                        'Ошибка при генерации ответа, подробнее - '+str(ex))
        return "Опача, а ботик-то, реально помер. Попробуйте попозже написать, может поднимется"


# функция для генерации фото
def generate_image(prompt):
    try:
        image_resp = openai.Image.create(
            prompt=prompt, n=1, size="512x512")
        image_link = image_resp.data[0]["url"]
        return image_link
    except Exception as ex:

        log_utils.inlog('ERROR', 'SERVER', 0,
                        'Ошибка при генерации ошибки, ошибка - '+str(ex))
        return "Ошибка, ваш запрос непрошел. Попробуйте ввести другой запрос!"

# Функция для проверки человека в вайт листе


def white_list_protected(user_id):
    f = open(WHITE_LIST_PATH, "r")
    whitelist = f.readlines()
    f.close()
    for i in range(whitelist.__len__()):
        # print()
        if user_id == int(whitelist[i]):
            return True
    return False


# отправка файла лога
@bot.message_handler(commands=['log'])
def command_message(message):

    if message.from_user.id in admin_list:

        log_utils.inlog("Запрос лога", message.from_user.username,
                        message.from_user.id, message.text)
        bot.send_document(message.from_user.id, InputFile(LOG_DB_PATH))

        log_utils.inlog("Отправка лога", "SERVER", 0, "Файл успешно отправлен")
    else:
        bot.send_message(
            message.from_user.id, "Ура, вы нашли команду лога =-), молодец, но увы, вы не админ =-(! ")

        log_utils.inlog("Отправка лога", "SERVER", 0,
                        "Файл не отправлен, т.к. юзер не админ")


@bot.message_handler(commands=['anonc'])
def command_message(message):
    if message.from_user.id in admin_list:

        f = open(WHITE_LIST_PATH, "r")
        whitelist = f.readlines()
        f.close()
        content = message.text.replace("/anonc ", "")

        log_utils.inlog("Анонс", message.from_user.username,
                        message.from_user.id, message.text)
        for i in range(whitelist.__len__()):
            bot.send_message(whitelist[i], content)

# старт нового диалога


@bot.message_handler(commands=['start'])
def send_welcome(message):

    log_utils.inlog('/start', message.from_user.username,
                    message.from_user.id, message.text)
    bot.reply_to(
        message, welcome_message)


# добавление новых пользователей (для админов)

@bot.message_handler(commands=["adduser"])
def command_message(message):
    if message.from_user.id in admin_list:
        f = open(WHITE_LIST_PATH, "a")
        userid = re.search("[0-9]+", message.text)
        f.write(str(userid[0]) + "\n")
        f.close()
        bot.reply_to(message, "Кентик успешно добавлен")

        log_utils.inlog("Добавление пользователя", message.from_user.username,
                        message.from_user.id, message.text)
    else:
        bot.reply_to(message, "Вы не админ =-(")
        log_utils.inlog("ERROR", "SERVER", 0,
                        "Ошибка добавления пользователя, юзер не админ")


# удаление пользователя из вайтлиста (для админов)
@bot.message_handler(commands=["deleteuser"])
def command_message(message):
    f = open(WHITE_LIST_PATH, "r+")
    users = f.readlines()
    user_for_delete = re.search("[0-9]+", message.text)

    try:
        user_index = users.index(str(user_for_delete[0]) + "\n")
        users.pop(user_index)
        f.seek(0)
        f.truncate()
        for i in range(len(users)):
            users[i] = users[i].strip()
            if (str(users[i]) != "\n"):
                f.write(str(users[i])+"\n")

        bot.reply_to(message, "Кентик удален")
        log_utils.inlog("Удаление из Whitelist", message.from_user.username,
                        message.from_user.id, message.text)

    except Exception as ex:
        bot.reply_to(message, "Кентик не найден")

        log_utils.inlog("Удаление из Whitelist", message.from_user.username,
                        message.from_user.id, "Ошибка удаления из whitelist, подробнее - "+str(ex))
    f.close()


# генерация фоток


@bot.message_handler(commands=['image'])
def command_message(message):
    protect = white_list_protected(message.from_user.id)

    if (protect):
        log_utils.inlog("Генерация фото", message.from_user.username,
                        message.from_user.id, message.text)
        prompt = message.text
        image = generate_image(prompt)
        bot.reply_to(message, text=image)

        log_utils.inlog("Генерация фото", "SERVER",
                        0, "Фото успешно сгенерено пользователю - "+str(message.from_user.id))

    else:

        log_utils.inlog("ERROR", "SERVER", 0, "Пользователь не в whitelist-e")
        bot.reply_to(message, text=message_for_not_white_list_users)

# обработка сообщений


@bot.message_handler(func=lambda _: True)
def handle_message(message):
    protect = white_list_protected(message.from_user.id)

    # print(message.from_user)
    if (protect):
        log_utils.inlog("Текстовый запрос", message.from_user.username,
                        message.from_user.id, message.text)
        prompt = message.text
        response = generate_response(prompt)
        bot.send_message(chat_id=message.from_user.id, text=response)

        log_utils.inlog("Текстовый запрос", "SERVER", 0,
                        "Бот ответил пользователю - "+str(message.from_user.id))
    else:
        bot.send_message(chat_id=message.from_user.id,
                         text="Ваш id - "+str(message.from_user.id)+message_for_not_white_list_users)


if __name__ == "__main__":

    while True:
        try:
            print('ChatGPT Telegram bot - is working')
            log_utils.inlog("BOT START", "SERVER", 0, "Сервер запустился")
            bot.polling()
        except Exception as e:
            print(str(datetime.datetime.now()) +
                  'ChatGPTBOT  - УПАЛ, ошибка - '+str(e))

            log_utils.inlog("ERROR", "SERVER", 0,
                            "Сервер упал, подробнее - "+str(e))
