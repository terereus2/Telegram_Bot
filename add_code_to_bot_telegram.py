import datetime
import subprocess
import json
import sqlite3
import time
import os
import logging
import telebot
import threading
import requests
import shutil
import re
from bs4 import BeautifulSoup
from telebot import types

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read().strip()

bot = telebot.TeleBot(TOKEN)


# обработчик команд
@bot.message_handler(commands=['start'])
def all_commands(message):
    list_command = 'List of commands:\n\n' \
                   '/problem - Daily problem\n' \
                   '/toprank - Top rank professional players\n\n'\
                   ' Отправляйте партию в формате SGF, и получайте анализ партии.(анализ игр на форе от 2 камней будет искажен) (убидитесь что коми указано в диапазоне от -150 до 150)\n\n'\
                   ' Напишите свое имя (можно ввести не полное имя) и узнаете свой рейтинг в Rating list of european players.'
    bot.send_message(message.chat.id, list_command)

# рейтинг топ професиональных игроков
@bot.message_handler(commands=['toprank'])
def top_10_rating_players(message):
    print(555)
    url = 'https://www.go4go.net/go/players/rank'
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    headers = {
        'User-Agent': user_agent
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    list_players = soup.find_all('td', limit=5)

    img_players = []
    for elem in list_players:
        img_players.append(elem.find('img')['src'])

    name_players = []
    for elem in list_players:
        name_players.append(elem.find('img')['title'])

    rating_players = []
    for elem in list_players:
        rating_players.append(elem.text[-8:])

    zip_list_players = zip(img_players, name_players, rating_players)

    for photo,name,rating in zip_list_players:
        text = f'{name}\n{rating}'
        bot.send_photo(message.chat.id,photo,text)







# обработчик команд
@bot.message_handler(commands=['problem'])
def button_daily_problem(message):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_replay = types.KeyboardButton(text='Daily problem')
    markup_replay.add(btn_replay)
    bot.send_message(message.chat.id, 'A new problem every day', reply_markup=markup_replay)


# обработчик входящего сообщения
@bot.message_handler(content_types=['text'])
def daily_problem(message):
    folder_path = 'G:\programming\Bot\problems'
    file_list = sorted(os.listdir(folder_path), key=lambda x: int(x.rstrip('.jpg')))
    current_unix_time = int(time.time())
    five = current_unix_time // 300
    remainder = five % (len(file_list) + 1)
    print(remainder)

    if message.text == 'Daily problem':
        photo = open(f'problems/{file_list[remainder]}', 'rb')
        bot.send_photo(message.chat.id, photo)

        photo.close()
        markup_replay = types.InlineKeyboardMarkup()
        btn_replay = types.InlineKeyboardButton(text="Solution", callback_data=remainder)
        markup_replay.add(btn_replay)
        bot.send_message(message.chat.id, 'Daily problem', reply_markup=markup_replay)

    else:
        url = 'https://www.europeangodatabase.eu/EGD/createalleuro3.php?country=**&dgob=false'
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        headers = {
            'User-Agent': user_agent
        }
        responce = requests.get(url, headers=headers)
        soup = BeautifulSoup(responce.text, 'html.parser')
        text = soup.get_text()
        patern = r"\d+\s*[A-Z].*[+-]"
        matches = re.findall(patern, text)
        split_list = [elem.split(' ') for elem in matches]
        final_list = [[elem for elem in element if elem and elem != '+'] for element in split_list]

        name_list = [elem[1] + ' ' + elem[2] for elem in final_list]
        dict_names = dict(zip(name_list,final_list))
        count = 0
        for elem in name_list:
            if message.text.lower() in(elem.lower()):
                print(message.text)
                print(elem)
                list = dict_names.get(elem)
                t = f'<b>Place:</b> {list[0]}\n<b>Name:</b> {list[1]} {list[2]}\n<b>Country:</b> {list[3]}\n<b>Rank:</b> {list[4]}\n<b>Rating:</b> {list[5]}'
                if count <5:
                   bot.send_message(message.chat.id,t,parse_mode='HTML')
                   count+=1








# ответ на задачу
@bot.callback_query_handler(func=lambda call: call.data)
def answer(call):
    folder_path = 'G:\programming\Bot\solutions'
    file_list = sorted(os.listdir(folder_path), key=lambda x: int(x.rstrip('.jpg')))
    photo = open(f'solutions/{file_list[int(call.data)]}', 'rb')
    bot.send_photo(call.message.chat.id, photo)
    photo.close()




# создание таблицы в базе данных
conn = sqlite3.connect('games.db')
cur = conn.cursor()
cur.execute(""" CREATE TABLE IF NOT EXISTS users (
   user_id INTEGER PRIMARY KEY,
   date TEXT,
   user_name TEXT,
   chat_id INTEGER,
   message_id INTEGER,
   file       TEXT
);
""")
conn.close()


count_send_file = {}

# получение файла sgf от юзера
@bot.message_handler(content_types=['document'])
def get_file_svg(message):
    if message.document.mime_type != 'application/x-go-sgf':
        bot.reply_to(message, 'Файл должен быть в формате SGF.')
    else:
        if (message.document.mime_type == 'application/x-go-sgf' and (not count_send_file.get(message.chat.id))):
            count_send_file[message.chat.id] = 1

            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = message.document.file_id[-10:] +'_' + message.document.file_name
            chat_id = message.chat.id
            records_path = f'G:\programming\Bot\GoGameRecords\{file_name}'

            # запись полученого файла в папку GoGameRecords
            with open(records_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                bot.reply_to(message, f'файл {message.document.file_name} \n <b>успешно отправлен</b>', parse_mode='HTML')

            rec_list_path = f'G:\programming\Bot\GoGamesRecords_SendUsers'

            def analyze_sgf_file(file_path):
                # Используем полный путь к analyze-sgf.cmd
                command = [r"C:\Users\Вова\AppData\Roaming\npm\analyze-sgf.cmd", file_path]

                # Запуск команды через subprocess
                result = subprocess.run(command, capture_output=True, text=True)

                # Вывод результата выполнения команды
                print("Stdout:", result.stdout)
                print("Stderr:", result.stderr)

                if result.returncode == 0:
                    print(f"Файл {file_path} успешно проанализирован!")

                else:
                    print(f"Произошла ошибка при анализе файла {file_path}")

            # Пример использования
            analyze_sgf_file(records_path)

            def send_file_to_user():
                while True:
                    list_games = records_path.replace('.sgf', '-analyzed.sgf')  # может так надо... срезы еще подумай
                    # Проверяем, что records_path заканчивается на ".sgf", и заменяем его на "-analyzed.sgf"
                    if list_games.endswith("-analyzed.sgf"):
                        # Проверяем, существует ли файл с окончанием "-analyzed.sgf
                        print(f"Отправляю файл: {list_games}")
                        print(f'имя файла {file_name}')

                        # Открываем файл для отправки
                        with open(list_games, 'rb') as fa:
                            print(f'F файл {list_games}')
                            bot.send_document(chat_id, fa)
                            count_send_file[message.chat.id] = 0

                            # Удаляем файлы после успешной отправки

                        os.remove(records_path)
                        os.remove(list_games)
                    else:
                        print(f"Файл {list_games} не найден. Ожидание...")


                    # Ждем перед повторной проверкой
                        time.sleep(20)

            threading.Thread(target=send_file_to_user).start()


        else:
            bot.reply_to(message, 'Ожидайте ответа на предыдущий файл перед отправкой следующего.')


while True:
    logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="w",
                        format="%(asctime)s %(levelname)s %(message)s")
    try:

        bot.polling(none_stop=True)

    except Exception as e:
        logging.error(e)


