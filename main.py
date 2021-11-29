from multiprocessing import Process
from datetime import datetime
import time

from pymongo import MongoClient
import telebot
import schedule
from config import * # config.py


bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_url)

db = client.botDB
pull_remind = db.pull_remind
history = db.history
try: db.command('serverStatus')
except Exception as e: print(e)
else: print('---Connect to DB: successful')

def check_remind():
    start = datetime.now()

    if start.minute > 57:
        end = datetime.now().replace(hour=start.hour+1,minute=1,
                                     second=0,
                                     microsecond=0)
    else:
        end = datetime.now().replace(minute=start.minute+2,
                                     second=start.second,
                                     microsecond=0)

    print(f'Find by date end: {type(end)}: {end}')
    
    filter = {'datetime': {'$gt': start, '$lt': end},
              'reminded': 0}
    data = pull_remind.find_one(filter)

    return data

def insert_data_remind(user_id, username, text, timestamp):
    data = {
        'user_id': user_id,
        'username': username,
        'text': text,
        'datetime': timestamp,
        'reminded': 0,
        'Created_At': datetime.now(),
    }
    status = pull_remind.insert_one(data)
    print(f'---Insert_one: status: OK, updated: {status}')
    
    return 'Ok'

def check():
    print('---Checking')
    data = check_remind()

    if data: 
        print('---Find')
        bot.send_message(data['user_id'], data['text'])
        update_data = {'$set': {'reminded': 1}}
        filter = {'_id': data['_id']}
        pull_remind.update_one(filter, update_data)
        print('---Reminded:\nUser\t' + str(data['user_id']) +\
              '\nText:\t' + str(data['text']))

def wait():
    schedule.every(1).minutes.do(check)

    while True:
        schedule.run_pending()
        time.sleep(1)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Bot-reminder. Hello, {message.from_user.first_name}.')
    bot.send_message(message.from_user.id,
                    'Format massage: Remember, 2021-11-04 01:32:00 Text...')

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, '''Help: This bot it`s a pet-project developed by 
        Melnyk M.S., Marchenko V.O. and Vereschak P.V, 
        from group СЗ-382Б in National Aviation.''')
    
@bot.message_handler(content_types=['text'])
def get_message(message):
    data = {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'text': message.text,
        'Created_At': datetime.now(),
    }
    history.insert_one(data)
    if message.from_user.id in ADMIN_ID:
        if 'Remember' in message.text:
            data = message.text.split()
            
            n_date, n_time = data[1:3]
            n_text = ' '.join(data[3:])
            n_date = [int(i) for i in n_date.split('-')]
            n_time = [int(i) for i in n_time.split(':')]
            n_datetime = datetime(year=n_date[0], month=n_date[1],
                                  day=n_date[2], hour=n_time[0],
                                  minute=n_time[1], second=n_time[2])

            print(f'Insert end date: {type(n_datetime)}: {n_datetime}')

            query_result = insert_data_remind(message.from_user.id, message.from_user.username,
                n_text, n_datetime)
            if query_result == 'Ok':
                bot.send_message(message.from_user.id,
                                 'I`m remember that. NEXT')

        elif 'check' in message.text:
            check()


if __name__ == '__main__':
    p = Process(target=wait)
    p.start()

    while True: 
        try: 
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)

        time.sleep(1)
