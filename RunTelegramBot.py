import telebot
import time
import json
import os
from threading import Lock
import hashlib

# Загрузка переменных окружения
BOT_TOKEN = "8125648329:AAEZoJxUF0XmzKwDobFhYmpsJLcKN_OE7mY"
ADMINS_FILE = "TelegramData/admins.txt" # Если не задана, по умолчанию admins.txt

# Путь к файлу blacklist
BLACKLIST_FILE = 'TelegramData/blacklist.json'
VERIFIED_FILE = 'TelegramData/verified.json'
REPORT_COOLDOWN = 0
VERIFY_COOLDOWN = 0

# Словарь для отслеживания времени последнего использования команд
last_command_times = {}

# Блокировка для доступа к данным
data_lock = Lock()

# Словарь для хранения данных callback (хэш: данные)
callback_data_store = {}

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Загрузка администраторов из файла
def load_admins():
    try:
        with open(ADMINS_FILE, 'r') as f:
            return [int(line.strip()) for line in f]
    except FileNotFoundError:
        return []

# Сохранение администраторов в файл
def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        for admin_id in admins:
            f.write(str(admin_id) + '\n')

# Загрузка данных blacklist из файла
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"blockUsers": [], "blockVideos": []}
    except json.JSONDecodeError:
      print("Error: Could not decode blacklist.json. Check if the file is valid JSON. Creating empty blacklist.")
      return {"blockUsers": [], "blockVideos": []}

# Сохранение данных blacklist в файл
def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f, indent=2)

# Загрузка данных verified из файла
def load_verified():
    try:
        with open(VERIFIED_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"verifiedUsers": []}
    except json.JSONDecodeError:
      print("Error: Could not decode verified.json. Check if the file is valid JSON. Creating empty verified list.")
      return {"verifiedUsers": []}

# Сохранение данных verified в файл
def save_verified(verified):
    with open(VERIFIED_FILE, 'w') as f:
        json.dump(verified, f, indent=2)

# Проверка, является ли пользователь администратором
def is_admin(user_id):
    admins = load_admins()
    return user_id in admins

# Проверка, может ли пользователь отправлять команду (с учетом кулдауна)
def can_send_command(user_id, command_name, cooldown):
    current_time = time.time()
    if user_id in last_command_times and command_name in last_command_times[user_id]:
        time_diff = current_time - last_command_times[user_id][command_name]
        if time_diff < cooldown:
            return False, cooldown - int(time_diff)
    return True, 0

# Обновление времени последнего использования команды
def update_last_command_time(user_id, command_name):
  with data_lock:
    current_time = time.time()
    if user_id not in last_command_times:
        last_command_times[user_id] = {}
    last_command_times[user_id][command_name] = current_time

# Функция для создания хэша из данных
def generate_hash(data):
  return hashlib.sha256(data.encode()).hexdigest()[:10]

# Сохранение данных в callback_data_store
def store_callback_data(data):
    data_hash = generate_hash(str(data))
    callback_data_store[data_hash] = data
    return data_hash

# Получение данных из callback_data_store
def get_callback_data(data_hash):
    return callback_data_store.get(data_hash)

# Удаление данных из callback_data_store
def remove_callback_data(data_hash):
   if data_hash in callback_data_store:
        del callback_data_store[data_hash]

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    report_button = telebot.types.KeyboardButton('/report')
    verify_button = telebot.types.KeyboardButton('/verify')
    markup.add(report_button, verify_button)
    bot.send_message(message.chat.id, "Этот бот для марафона Cacto0o и здесь вы можете отправить жалобу на пользователя командой /report или про верифицировать свой аккаунт командой /verify и с вами свяжутся для подтверждения того, что вы являетесь автором аккаунта.", reply_markup=markup)

# Обработчик команды /report
@bot.message_handler(commands=['report'])
def report_handler(message):
    user_id = message.from_user.id
    can_send, remaining_time = can_send_command(user_id, 'report', REPORT_COOLDOWN)

    if not can_send:
        bot.send_message(message.chat.id, f"Вы сможете отправить жалобу через {remaining_time} секунд.")
        return
    
    update_last_command_time(user_id, 'report')
    
    sent_msg = bot.send_message(message.chat.id, "Пожалуйста, введите никнейм или ссылку на пользователя/видео, на которого вы хотите пожаловаться. Можно скопировать с @ или без, например: /report @username или /report tiktok.com/@username или /report tiktok.com/@username/video/VIDEOID")

    bot.register_next_step_handler(sent_msg, process_report_text)

def process_report_text(message):
    report_text = message.text.strip()

    if not report_text:
      bot.send_message(message.chat.id, "Необходимо ввести никнейм или ссылку на пользователя/видео.")
      return

    # Разбор текста и проверка, является ли это ником или ссылкой
    if 'tiktok.com' in report_text:
        if '/video/' in report_text:
           report_type = 'video'
           url_to_report = report_text
        elif '@' in report_text:
           report_type = 'user_by_url'
           url_to_report = report_text
        else:
          bot.send_message(message.chat.id, "Неправильный формат ссылки. Пожалуйста, введите корректную ссылку.")
          return

    elif '@' in report_text:
      report_type = 'user'
      username_to_report = report_text.replace('@','')
      url_to_report = f"https://www.tiktok.com/@{username_to_report}"
    else:
       report_type = 'user'
       username_to_report = report_text
       url_to_report = f"https://www.tiktok.com/@{username_to_report}"

    with data_lock:
      blacklist = load_blacklist()
      if report_type == 'user':
          if username_to_report in blacklist['blockUsers']:
            bot.send_message(message.chat.id, "Данный пользователь уже заблокирован.")
            return
      elif report_type == 'user_by_url' or report_type == 'video':
         if url_to_report in blacklist['blockVideos']:
              bot.send_message(message.chat.id, "Данное видео/пользователь уже заблокировано.")
              return

    report_msg = f"Новая жалоба:\n"
    if report_type == 'user':
      report_msg += f"Никнейм: {username_to_report} \nСсылка: {url_to_report}"
    elif report_type == 'user_by_url':
      report_msg += f"Ссылка на пользователя: {url_to_report}"
    elif report_type == 'video':
       report_msg += f"Ссылка на видео: {url_to_report}"

    report_msg += "\n#report #несмотрели"


    markup = telebot.types.InlineKeyboardMarkup()
    data_to_store = {
        'report_type': report_type,
        'url_to_report': url_to_report if report_type in ('user_by_url', 'video') else username_to_report
    }
    callback_hash = store_callback_data(data_to_store)
    yes_button = telebot.types.InlineKeyboardButton("Да", callback_data=f"report_yes|{callback_hash}")
    no_button = telebot.types.InlineKeyboardButton("Нет", callback_data=f"report_no|{callback_hash}")
    markup.add(yes_button, no_button)
    
    admins = load_admins()
    for admin_id in admins:
        try:
            bot.send_message(admin_id, report_msg, reply_markup=markup)
        except Exception as e:
            print(f"Error sending report message to admin {admin_id}: {e}")

    bot.send_message(message.chat.id, "Жалоба отправлена администраторам.")

@bot.message_handler(commands=['verify'])
def verify_handler(message):
    user_id = message.from_user.id
    can_send, remaining_time = can_send_command(user_id, 'verify', VERIFY_COOLDOWN)

    if not can_send:
        bot.send_message(message.chat.id, f"Вы сможете отправить запрос на верификацию через {remaining_time} секунд.")
        return
    
    update_last_command_time(user_id, 'verify')
    
    sent_msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте ссылку на ваш аккаунт в TikTok, или просто ваш никнейм с @. Пример: tiktok.com/@username или @username")
    bot.register_next_step_handler(sent_msg, process_verify_link)

def process_verify_link(message):
    tiktok_link = message.text.strip()
    user_id = message.from_user.id
    tg_username = f"@{message.from_user.username}"

    if not tiktok_link:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте ссылку на ваш аккаунт в TikTok, или просто ваш никнейм с @.")
        return

    if 'tiktok.com' in tiktok_link and '@' in tiktok_link:
        username = tiktok_link.split('@')[-1].split('/')[0]
    elif '@' in tiktok_link:
        username = tiktok_link.replace('@', '')
    else:
        username = tiktok_link
    
    if username.startswith('@'):
       username = username.replace('@', '')

    with data_lock:
        verified_data = load_verified()
        
        if any(user['tiktokUsername'] == username for user in verified_data['verifiedUsers']):
            bot.send_message(message.chat.id, "Этот аккаунт уже верифицирован.")
            return
    
    verify_msg = f"Новый запрос на верификацию от пользователя: {tg_username} ({message.from_user.id})\n"
    verify_msg += f"Ссылка на аккаунт: tiktok.com/@{username}\n#verify #несмотрели"

    markup = telebot.types.InlineKeyboardMarkup()
    callback_hash = store_callback_data({'tiktokUsername':username, 'tgUsername':tg_username})
    yes_button = telebot.types.InlineKeyboardButton("Да", callback_data=f"verify_yes|{callback_hash}")
    no_button = telebot.types.InlineKeyboardButton("Нет", callback_data=f"verify_no|{callback_hash}")
    markup.add(yes_button, no_button)

    admins = load_admins()
    for admin_id in admins:
        try:
            bot.send_message(admin_id, verify_msg, reply_markup=markup)
        except Exception as e:
            print(f"Error sending verify message to admin {admin_id}: {e}")
    bot.send_message(message.chat.id, "Ваш запрос на верификацию отправлен администраторам.")

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
def callback_report_handler(call):
    
    action, callback_hash = call.data.split('|')
    admins = load_admins()

    if call.from_user.id not in admins:
        bot.answer_callback_query(call.id, "У вас нет прав для выполнения данного действия.")
        return
    
    stored_data = get_callback_data(callback_hash)

    if not stored_data:
      bot.answer_callback_query(call.id, "Истекло время действия кнопки.")
      return
    
    report_type = stored_data.get('report_type')
    report_target = stored_data.get('url_to_report')

    with data_lock:
        blacklist = load_blacklist()
        if action == 'report_yes':
            if report_type == 'user':
                 blacklist['blockUsers'].append(report_target)
                 report_status = "#одобрили"
            elif report_type == 'user_by_url' or report_type == 'video':
               blacklist['blockVideos'].append(report_target)
               report_status = "#одобрили"
            save_blacklist(blacklist)

        elif action == 'report_no':
              report_status = "#неодобрили"
        
        try:
          if report_type == 'user':
              link = f"https://www.tiktok.com/@{report_target}"
              bot.edit_message_text(f"Новая жалоба:\nНикнейм: {report_target}\nСсылка: {link}\n#report {report_status}",
                                 chat_id=call.message.chat.id,
                                 message_id=call.message.message_id,
                                 reply_markup=None)
          elif report_type == 'user_by_url':
              bot.edit_message_text(f"Новая жалоба:\nСсылка на пользователя: {report_target}\n#report {report_status}",
                                 chat_id=call.message.chat.id,
                                 message_id=call.message.message_id,
                                 reply_markup=None)
          elif report_type == 'video':
             bot.edit_message_text(f"Новая жалоба:\nСсылка на видео: {report_target}\n#report {report_status}",
                                 chat_id=call.message.chat.id,
                                 message_id=call.message.message_id,
                                 reply_markup=None)
          bot.answer_callback_query(call.id, "Действие выполнено.")
        except Exception as e:
            print(f"Error editing message: {e}")
        finally:
            remove_callback_data(callback_hash)

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def callback_verify_handler(call):
    action, callback_hash = call.data.split('|')
    admins = load_admins()

    if call.from_user.id not in admins:
        bot.answer_callback_query(call.id, "У вас нет прав для выполнения данного действия.")
        return
    
    stored_data = get_callback_data(callback_hash)

    if not stored_data:
      bot.answer_callback_query(call.id, "Истекло время действия кнопки.")
      return
    
    tiktok_username = stored_data.get('tiktokUsername')
    tg_username = stored_data.get('tgUsername')

    with data_lock:
        verified_data = load_verified()
        if action == 'verify_yes':
            verified_data['verifiedUsers'].append({'tiktokUsername': tiktok_username, 'tgUsername': tg_username})
            save_verified(verified_data)
            verify_status = "#одобрили"
        elif action == 'verify_no':
              verify_status = "#неодобрили"

        try:
             bot.edit_message_text(f"Новый запрос на верификацию от пользователя: {tg_username} ({call.message.from_user.id})\nСсылка на аккаунт: tiktok.com/@{tiktok_username}\n#verify {verify_status}",
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=None)
             bot.answer_callback_query(call.id, "Действие выполнено.")
        except Exception as e:
          print(f"Error editing message: {e}")
        finally:
            remove_callback_data(callback_hash)
          
@bot.message_handler(func=lambda message: True)
def funcname(message):
    bot.reply_to(message, "Непонимаю о чем ты говоришь. Введи /start для начала работы")
# Запуск бота
if __name__ == '__main__':
    print("Starting bot...")
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is not set in environment variables.")
        exit(1)
    # Создание файлов, если они не существуют
    if not os.path.exists(ADMINS_FILE):
        open(ADMINS_FILE, 'w').close()
    if not os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump({"blockUsers": [], "blockVideos": []}, f)
    if not os.path.exists(VERIFIED_FILE):
         with open(VERIFIED_FILE, 'w') as f:
            json.dump({"verifiedUsers": []}, f)
    load_blacklist()
    load_verified()
    bot.polling(none_stop=True)