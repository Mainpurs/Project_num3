import requests
from transformers import AutoTokenizer
from pprint import pprint
from telebot.types import KeyboardButton, ReplyKeyboardMarkup
import json
import telebot
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

TOKEN = "6907816424:AAFtptMbHmk8FH4w39qBW7Zy1533IKPiPEM"
bot = telebot.TeleBot(TOKEN)

resize_keyboard = True
one_time_keyboard = True


def make_kb(text_1, text_2):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    # добавляем кнопочки с вариантами ответа
    answer_1 = KeyboardButton(text=text_1)
    answer_2 = KeyboardButton(text=text_2)
    keyboard.add(answer_1, answer_2)
    # возвращаем готовую клавиатуру с кнопочками
    return keyboard
# ----------------------------------------------------------------------------------------------------------------------


system_content = 'Ты - сборник фактов на русском языке, и должен рассказывать интересные и нестандартные факты на выбранную тему. Фактов должно быть не больше 10 в одном сообщении.'
assistant_content = 'Вот несколько фактов на вашу тему:'
user_content = ""
answer = ""
max_tokens_in_task = 2048
resp = None

URL = 'http://localhost:1234/v1/chat/completions'
HEADERS = {"Content-Type": "application/json"}

filename = "user_data.json"

# ----------------------------------------------------------------------------------------------------------------------


def load_data():
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    return data


def save_data(data):
    with open(filename, "w") as f:
        json.dump(data, f)

# ----------------------------------------------------------GPT---------------------------------------------------------


def get_answer_from_gpt(message, user_content):
    user_id = message.chat.id

    resp = requests.post(
        'http://localhost:1234/v1/chat/completions',
        headers={"Content-Type": "application/json"},
        json={
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content},
                {"role": "system", "content": system_content},
            ],
            "temperature": 1,
            "max_tokens": 1124
        }
    )

    if resp.status_code == 200 and 'choices' in resp.json():
        result = resp.json()['choices'][0]['message']['content']
        if result == "":
            bot.send_message(user_id, "Введите /continue чтобы продолжить или /solve_task чтобы оглавить новую тему.")
        else:
            bot.send_message(user_id, f'{result}')
            bot.send_message(user_id, "Введите /continue чтобы продолжить или /solve_task чтобы оглавить новую тему.")
    else:
        logging.error(f'Не удалось получить ответ от нейросети.\nЗапрос:\n{user_content}')
        bot.send_message(user_id, 'Не удалось получить ответ от нейросети')

    return answer

# ===================================================F_GPT==============================================================


def Fget_answer_from_gpt(message, user_content, assistant_content):
    user_id = message.chat.id

    Fresp = requests.post(
        'http://localhost:1234/v1/chat/completions',
        headers={"Content-Type": "application/json"},
        json={
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content},
                {"role": "system", "content": system_content},
            ],
            "temperature": 1,
            "max_tokens": 1124
        }
    )

    if Fresp.status_code == 200 and 'choices' in Fresp.json():
        result = Fresp.json()['choices'][0]['message']['content']
        if result == "":
            bot.send_message(user_id, "Введите /continue чтобы продолжить или /solve_task чтобы оглавить новую тему.")
        else:
            bot.send_message(user_id, f'{result}')
            bot.send_message(user_id, "Введите /continue чтобы продолжить или /solve_task чтобы оглавить новую тему.")
    else:
        logging.error(f'Не удалось получить ответ от нейросети.\nЗапрос:\n{user_content}')
        bot.send_message(user_id, 'Не удалось получить ответ от нейросети')

    return answer

# ------------------------------------------------------start-----------------------------------------------------------


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, 'Я бот-GPT который расскажет тебе много интересных фактов,\n на выбранную тему!')
    keyboard = make_kb('/solve_task', '/help')
    bot.send_message(user_id,
                     'Отправь команду /solve_task чтобы выбрать тему!',
                     reply_markup=keyboard)
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {}
    data[str(user_id)] = {'status': 0, 'admin': ''}
    save_data(data)

# --------------------------------------------------------Ffunc---------------------------------------------------------


@bot.message_handler(commands=['continue'])
def Fcontinue(message):
    user_id = message.chat.id
    data = load_data()
    global assistant_content

    # Retrieve conversation history from user data
    previous_answer = data[str(user_id)]['previous_answer']

    data[str(user_id)]['previous_answer'] = previous_answer + answer
    save_data(data)

    topic = data[str(user_id)]['previous_topic']

    assistant_content += previous_answer
    save_data(data)

    if data[str(user_id)]['status'] == 1 or data[str(user_id)]['status'] == 2:
        Fget_answer_from_gpt(message, user_content=topic, assistant_content=assistant_content)
    else:
        logging.warning("Пользователь еще не отправил первый запрос")
        bot.send_message(user_id, 'Вы еще не отправляли первый запрос. Воспользуйтесь /solve_task')


@bot.message_handler(commands=['debug'])
def Fdebug(message):
    user_id = message.chat.id
    data = load_data()
    if data[str(user_id)]['admin'] == 'T':
        try:
            with open("log_file.txt", "rb") as f:
                bot.send_document(message.chat.id, f)

        except FileNotFoundError:
            bot.send_message(user_id, 'Кажись у вас еще нету ошибок')
    else:
        bot.send_message(user_id, 'Вы не можете использовать эту команду.')

# --------------------------------------------------------pre-GPT-------------------------------------------------------
# обработка действий состояния "Обращение к GPT для решения новой задачи"


@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    user_id = message.chat.id
    data = load_data()
    data[str(user_id)] = {'status': 1, 'admin': 'F', 'previous_topic': '', 'previous_answer': ''}
    if str(user_id) == "5932532601":
        data[str(user_id)] = {'status': 1, 'admin': 'T', 'previous_answer': ''}
    save_data(data)
    bot.send_message(user_id, text="Следующим сообщением напиши тему для фактов")
    # регистрируем следующий "шаг"
    bot.register_next_step_handler(message, get_promt)


# обработка действий для состояния "Получение ответа"
def get_promt(message):
    user_id = message.chat.id
    data = load_data()

    if data[str(user_id)]['status'] == 0 or data[str(user_id)]['status'] == 1:
        # убеждаемся, что получили текстовое сообщение, а не что-то другое
        if message.content_type != "text":
            bot.send_message(user_id, text="Отправь промт текстовым сообщением")
            print(len(message.text))
            if len(message.text) > 5:
                # регистрируем следующий "шаг" на эту же функцию
                bot.send_message(user_id, 'Сообщение слишком длинное!')
                bot.register_next_step_handler(message, get_promt)
            return

    # получаем сообщение, которое и будет промтом
    user_content = message.text
    data[str(user_id)]['previous_topic'] = user_content
    save_data(data)
    bot.send_message(user_id, "Промт принят!")
    # дальше идет обработка промта и отправка результата
    get_answer_from_gpt(message, user_content)

# --------------------------------------------------------Help----------------------------------------------------------


@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = message.chat.id
    bot.send_message(user_id,
                     "Я рассказываю множество фактов на выбранную тему. Для того чтобы объявить первую тему: /solve_task Если отправишь команду /continue, я продолжу искать факты на уже выбранную тему, а для завершения диалога введи команду /stop.")


@bot.message_handler(content_types=['text'])
def base(message):
    user_id = message.chat.id
    user_message = message.text
    bot.send_message(user_id, f"Ты написал(а): '{user_message}'. Пожалуйста, воспользуйтесь - /help")


bot.infinity_polling()
