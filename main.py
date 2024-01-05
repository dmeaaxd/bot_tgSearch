import dotenv
import os
from sqlalchemy import create_engine, MetaData, Table, select
import telebot
from telebot import types

dotenv.load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_LOGIN = os.getenv('DB_LOGIN')
DB_PASSWORD = os.getenv('DB_PASSWORD')

db_url = f'postgresql://{DB_LOGIN}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine = create_engine(db_url)

metadata = MetaData()

metadata.reflect(engine)

# Получаем таблицы
accounts = Table('TgSearchAccounts', metadata, autoload=True, autoload_with=engine)
chats = Table('TelegramChats', metadata, autoload=True, autoload_with=engine)

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

connection = engine.connect()


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Введите /status для получения списка всех аккаунтов.")


@bot.message_handler(commands=['status'])
def handle_status(message):

    # список всех аккаунтов
    accounts_query = select(accounts)

    print(accounts_query)

    accounts_result = connection.execute(accounts_query)
    accounts_rows = accounts_result.fetchall()

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for account in accounts_rows:
        keyboard.add(types.KeyboardButton(f"{account.id}. {account.email}"))

    bot.send_message(message.chat.id, "Выберите аккаунт:", reply_markup=keyboard)

# выбор аккаунта
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        account_id = int(message.text.split('.')[0])
        account_query = accounts.select().where(accounts.c.id == account_id)
        account_result = connection.execute(account_query)
        account_row = account_result.fetchone()

        if account_row:
            bot.send_message(message.chat.id, f"*Статус аккаунта {account_row.email}:* {'Работает' if account_row.id else 'Не работает'}", parse_mode="Markdown")
            bot.send_message(message.chat.id, f"*Список ключевых слов:* {account_row.search_words}", parse_mode="Markdown")

            chats_query = chats.select().where(chats.c.owner_id == account_row.id)
            chats_result = connection.execute(chats_query)
            chat_rows = chats_result.fetchall()

            if chat_rows:
                bot.send_message(message.chat.id, "*Список групп:*", parse_mode="Markdown")
                for chat in chat_rows:
                    bot.send_message(message.chat.id, f"- {chat[3]}")
            else:
                bot.send_message(message.chat.id, "У аккаунта нет групп.")

        else:
            bot.send_message(message.chat.id, "Аккаунт не найден.")

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, выберите аккаунт из списка.")



# Запускаем бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
