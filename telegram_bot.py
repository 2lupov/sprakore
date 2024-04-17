import telebot
from telebot import types
import re
import logging

TOKEN = '6279188443:AAEd-J_iclFx_418W20S-7t0PCGM3aprLQA'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = '5109895086'  # Замініть на ваш Telegram ID
AUTHORIZED_USERS = set()

logging.basicConfig(filename='bot_log.log', level=logging.INFO, format='%(asctime)s - %(message)s')

materials = {
    'Німецька': {
        'Середній': '/root/languages/Grammatik_aktiv_B1.pdf'
    }
}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Створення InlineKeyboardMarkup для меню
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Створення кнопок для меню
    materials_button = types.InlineKeyboardButton(text='Матеріали', callback_data='materials')
    register_button = types.InlineKeyboardButton(text='Реєстрація', callback_data='register')
    
    # Додавання кнопок до меню
    markup.add(materials_button, register_button)
    
    # Відправлення повідомлення з меню
    bot.send_message(message.chat.id, "Ласкаво просимо до бота!", reply_markup=markup)

@bot.message_handler(commands=['register'])
def register(message):
    choose_language(message)

@bot.message_handler(commands=['authorize'])
def authorize_user(message):
    if str(message.from_user.id) == ADMIN_ID:
        parts = message.text.split()
        if len(parts) > 1:
            user_id = parts[1]
            AUTHORIZED_USERS.add(user_id)
            bot.send_message(ADMIN_ID, f"Користувач з ID {user_id} авторизований.")
        else:
            bot.send_message(ADMIN_ID, "ID користувача не вказано.")
    else:
        bot.send_message(message.chat.id, "Ви не маєте права надавати авторизацію.")

@bot.message_handler(commands=['materials'])
def materials_handler(message):
    if str(message.from_user.id) not in AUTHORIZED_USERS:
        bot.send_message(message.chat.id, "Вибачте, але ви ще не зареєструвалися на заняття.")
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Німецька', 'Англійська', 'Французька', 'Норвезька')
    msg = bot.send_message(message.chat.id, "Оберіть мову:", reply_markup=markup)
    bot.register_next_step_handler(msg, select_level)

def choose_language(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('🇩🇪 Німецька', '🇬🇧 Англійська', '🇫🇷 Французька', '🇳🇴 Норвезька')
    msg = bot.send_message(message.chat.id, "Яку мову ви хочете вивчати?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_language_choice)

def select_level(message):
    language = message.text
    if language in materials:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        levels = materials[language].keys()
        for level in levels:
            markup.add(level)
        msg = bot.send_message(message.chat.id, f"Оберіть рівень для мови {language}:", reply_markup=markup)
        bot.register_next_step_handler(msg, send_materials, language)
    else:
        bot.send_message(message.chat.id, "Вибачте, але матеріали для обраної мови відсутні.")

def send_materials(message, language):
    level = message.text
    if language in materials and level in materials[language]:
        file_path = materials[language][level]
        file_url = upload_to_google_drive(file_path)
        bot.send_message(message.chat.id, f"Матеріали для {language} рівня {level}: {file_url}")
    else:
        bot.send_message(message.chat.id, "Вибачте, але матеріали для обраної мови та рівня відсутні.")

def ask_for_fullname(message, language):
    msg = bot.send_message(message.chat.id, "Будь ласка, введіть ваше ПІБ:")
    bot.register_next_step_handler(msg, process_fullname, language)

def process_fullname(message, language):
    fullname = message.text.strip()
    if not all(x.isalpha() or x.isspace() for x in fullname):
        msg = bot.send_message(message.chat.id, "Помилка: введіть коректне ПІБ (тільки літери та пробіли). Спробуйте ще раз:")
        bot.register_next_step_handler(msg, process_fullname, language)
        return
    ask_for_phone(message, language, fullname)

def ask_for_phone(message, language, fullname):
    msg = bot.send_message(message.chat.id, "Будь ласка, введіть ваш номер телефону:")
    bot.register_next_step_handler(msg, process_phone, language, fullname)

def process_phone(message, language, fullname):
    phone = message.text.strip()
    if not re.match(r'^\+?1?\d{9,15}$', phone):
        msg = bot.send_message(message.chat.id, "Помилка: введіть коректний номер телефону. Спробуйте ще раз:")
        bot.register_next_step_handler(msg, process_phone, language, fullname)
        return
    ask_for_email(message, language, fullname, phone)

def ask_for_email(message, language, fullname, phone):
    msg = bot.send_message(message.chat.id, "Будь ласка, введіть вашу електронну пошту:")
    bot.register_next_step_handler(msg, process_email, language, fullname, phone)

def process_email(message, language, fullname, phone):
    email = message.text.strip()
    if not re.match(r'^\S+@\S+\.\S+$', email):
        msg = bot.send_message(message.chat.id, "Помилка: введіть коректну електронну пошту. Спробуйте ще раз:")
        bot.register_next_step_handler(msg, process_email, language, fullname, phone)
        return
    registration_complete(message, language, fullname, phone, email)

def registration_complete(message, language, fullname, phone, email):
    # Відправлення інформації про нову реєстрацію до адміністратора з ID користувача
    bot.send_message(ADMIN_ID, f"Нова реєстрація: {language}\nПІБ: {fullname}\nТелефон: {phone}\nЕлектронна пошта: {email}\nUser ID: {message.from_user.id}")
    # Повідомлення користувачу, що його дані були відправлені
    bot.send_message(message.chat.id, "Дякуємо за реєстрацію! Ваші дані були відправлені.")
    logging.info(f"Registration completed for {fullname} with User ID: {message.from_user.id}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_message(message.chat.id, "Будь ласка, використовуйте кнопки для взаємодії з ботом.")

bot.polling()
