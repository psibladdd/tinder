import random
from telegram.ext import *
from telegram import *
import sqlite3

bot_token = '8490866962:AAGFY-WLbp9RhNIWotFnBdb9HSdcplCOrWg'
conn = sqlite3.connect('tinder.db', check_same_thread=False)
c = conn.cursor()

# Создаем таблицы если их нет
c.execute('''CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    username TEXT,
    name TEXT,
    age INTEGER,
    info TEXT,
    photo TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER,
    to_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_id, to_id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER,
    user2_id INTEGER,
    notified BOOLEAN DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user1_id, user2_id)
)''')
conn.commit()

NAME, AGE, ABOUT, PHOTO = range(4)
REACTION = range(1)


async def start(update, context):
    context.user_data.clear()

    # Проверяем есть ли анкета
    c.execute('SELECT * FROM people WHERE id = ?', (update.effective_user.id,))
    existing_profile = c.fetchone()

    if existing_profile:
        # Если анкета есть, показываем главное меню
        keyboard = [[KeyboardButton("Начать поиск"),
             KeyboardButton("Показать профиль")],
             [KeyboardButton("Редактировать профиль"),KeyboardButton("Удалить профиль")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(

            "С возвращением! Что хочешь сделать?",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    else:
        # Если анкеты нет, начинаем создание
        await update.message.reply_text(
            '''Привет! 

Кажется, пора найти свой мэтч на ВожАке 💜

Я — бот для знакомств: почти как Tinder, но гораздо лучше. Я помогу тебе узнать самых крутых, ярких, заряженных вожатых со всей России. Но никак не справлюсь без твоей помощи.

Для начала уточни, как к тебе можно обращаться?''',
            reply_markup=ForceReply(selective=True),
        )
        return NAME


async def age(update, context):
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        f'У тебя классное имя, {update.message.text}! А сколько тебе лет?',
        reply_markup=ForceReply(selective=True),
    )
    return AGE


async def about(update, context):
    context.user_data['age'] = update.message.text
    await update.message.reply_text(
        f'''Отличный возраст для познания себя и мира вокруг!

Мне уже не терпится узнать тебя поближе. Расскажи о себе что-нибудь интересное!

Например, какой это для тебя по счёту ВожАк? 
Какие мероприятия и мастер-классы хочешь посетить? Какие навыки хотел бы развить здесь? 
А, кстати, какое у тебя хобби? И как любишь проводить вечера?''',
        reply_markup=ForceReply(selective=True),
    )
    return ABOUT


async def photo(update, context):
    context.user_data['about'] = update.message.text
    await update.message.reply_text(
        '''Вау, я уже чувствую, что поймал с тобой мэтч! 🥰

Мне кажется, я даже знаю, как ты выглядишь. Хочу подтвердить свои догадки, поэтому, пожалуйста, пришли свою фотографию.''',
        reply_markup=ForceReply(selective=True),
    )
    return PHOTO


async def save_profile(update, context):
    if update.message.photo:
        photo = await update.message.photo[-1].get_file()
        path = f"{update.message.from_user.id}.jpg"
        await photo.download_to_drive(path)

        name = context.user_data.get('name', '')
        age = context.user_data.get('age', '')
        about = context.user_data.get('about', '')

        c.execute('INSERT OR REPLACE INTO people (id, username, name, age, info, photo) VALUES (?,?,?,?,?,?) ',
                  (update.message.from_user.id, update.message.from_user.username, name, age, about, path))
        conn.commit()

        keyboard = [
            [KeyboardButton("Начать поиск"),
             KeyboardButton("Показать профиль")],
             [KeyboardButton("Редактировать профиль"),KeyboardButton("Удалить профиль")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            '''Огонь! 

Я тебя таким и представлял. Уже задумываюсь о том, чтобы никому не показывать твою анкету и оставить такое сокровище себе... 😁

Но ладно: сегодня я всё-таки в настроении помочь найти твой мэтч на Поларе!''',
            reply_markup=reply_markup
        )

        return ConversationHandler.END
    else:
        await update.message.reply_text(
            'Пожалуйста, отправь фото для завершения анкеты',
            reply_markup=ForceReply(selective=True),
        )
        return PHOTO


async def show_profile(update, context):
    user_id = update.effective_user.id
    c.execute('SELECT * FROM people WHERE id = ?', (user_id,))
    user = c.fetchone()

    if user:
        profile_text = f"{user[2]}, {user[3]}\n\n"
        profile_text += f"{user[4]}"

        # Показываем мэтчи
        c.execute('''
            SELECT p.username, p.name 
            FROM matches m 
            JOIN people p ON (p.id = m.user1_id OR p.id = m.user2_id)
            WHERE (m.user1_id = ? OR m.user2_id = ?) AND p.id != ?
        ''', (user_id, user_id, user_id))

        matches = c.fetchall()
        if matches:
            profile_text += "\n\n🎉 *Ваши мэтчи:*\n"
            for match in matches:
                profile_text += f"• {match[1]} - @{match[0]}\n"
        keyboard = [[KeyboardButton("Начать поиск"),
             KeyboardButton("Показать профиль")],
             [KeyboardButton("Редактировать профиль"),KeyboardButton("Удалить профиль")]]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        if user[5]:
            try:
                with open(user[5], 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=profile_text,
                        reply_markup=reply_markup
                    )
            except:
                await update.message.reply_text(profile_text)
        else:
            await update.message.reply_text(profile_text)
    else:
        await update.message.reply_text("Профиль не найден. Начни с команды /start")


async def start_match(update, context):
    user_id = update.effective_user.id

    # Получаем список пользователей, которых уже лайкали
    c.execute('SELECT to_id FROM likes WHERE from_id = ?', (user_id,))
    liked_users = [row[0] for row in c.fetchall()]

    # Получаем всех пользователей кроме себя и тех, кого уже лайкали
    exclude_ids = [user_id] + liked_users
    placeholders = ','.join('?' for _ in exclude_ids)

    query = f'''
        SELECT * FROM people 
        WHERE id NOT IN ({placeholders})
        ORDER BY RANDOM() 
        LIMIT 1
    '''

    c.execute(query, exclude_ids)
    current = c.fetchone()

    if not current:
        # Если все пользователи просмотрены
        keyboard = [[KeyboardButton("Начать поиск"),
             KeyboardButton("Показать профиль")],
             [KeyboardButton("Редактировать профиль"),KeyboardButton("Удалить профиль")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "Ты просмотрел все анкеты!",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # Сохраняем текущего пользователя в контексте
    context.user_data['current_profile'] = current
    context.user_data['current_id'] = current[0]

    keyboard = [
        [KeyboardButton('❤️'), KeyboardButton('👎')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    profile_text = f"{current[2]}, {current[3]}\n\n"
    profile_text += f"{current[4]}"

    if current[5]:
        try:
            with open(current[5], 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=profile_text,
                    reply_markup=reply_markup
                )
        except:
            await update.message.reply_text(profile_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(profile_text, reply_markup=reply_markup)

    return REACTION


async def process_reaction(update, context):
    user_id = update.effective_user.id
    target_id = context.user_data.get('current_id')
    reaction = update.message.text

    if reaction == "❤️":
        # Сохраняем лайк
        try:
            c.execute('INSERT OR IGNORE INTO likes (from_id, to_id) VALUES (?, ?)',
                      (user_id, target_id))
            conn.commit()

            # Проверяем на взаимный лайк (матч)
            c.execute('SELECT 1 FROM likes WHERE from_id = ? AND to_id = ?',
                      (target_id, user_id))
            mutual_like = c.fetchone()

            if mutual_like:
                # Создаем запись о мэтче
                user1_id = min(user_id, target_id)
                user2_id = max(user_id, target_id)

                c.execute('INSERT OR IGNORE INTO matches (user1_id, user2_id) VALUES (?, ?)',
                          (user1_id, user2_id))
                conn.commit()

                # Получаем юзернеймы обоих пользователей
                c.execute('SELECT username FROM people WHERE id = ?', (user_id,))
                user1_username = c.fetchone()[0]

                c.execute('SELECT username FROM people WHERE id = ?', (target_id,))
                user2_username = c.fetchone()[0]

                c.execute('SELECT name FROM people WHERE id = ?', (target_id,))
                target_name = c.fetchone()[0]

                # Отправляем уведомление обоим пользователям о мэтче
                # Текущему пользователю
                await update.message.reply_text(
                    f'''ЭТО МЭТЧ 🔥

У меня аж дыхание перехватило от такой совместимости! Скорее знакомьтесь поближе: @{user2_username}'''
                )

                # Второму пользователю (если он сейчас в боте)
                # Для этого нужно использовать application.bot
                from telegram.ext import Application
                app = Application.builder().token(bot_token).build()

                try:
                    await app.bot.send_message(
                        chat_id=target_id,
                        text=f"🎉 У вас мэтч с {update.effective_user.full_name}! 💕\n"
                             f"Напиши @{user1_username} и договорись о встрече на ВожАке!"
                    )
                except Exception as e:
                    print(f"Не удалось отправить уведомление пользователю {target_id}: {e}")

            else:
                await update.message.reply_text("❤️ Лайк отправлен!")

        except Exception as e:
            print(f"Ошибка при обработке лайка: {e}")
            await update.message.reply_text("Что-то пошло не так...")

    elif reaction == "👎":
        # Просто сохраняем лайк (дизлайк) чтобы не показывать снова
        try:
            c.execute('INSERT OR IGNORE INTO likes (from_id, to_id) VALUES (?, ?)',
                      (user_id, target_id))
            conn.commit()
            await update.message.reply_text("👎 Запомнили твой выбор")
        except Exception as e:
            print(f"Ошибка при обработке дизлайка: {e}")

    # Показываем следующего пользователя
    await start_match(update, context)
    return REACTION


async def handle_buttons(update, context):
    text = update.message.text

    if text == "Начать поиск":
        # Запускаем ConversationHandler для поиска
        await start_match(update, context)
        return REACTION
    elif text == "Показать профиль":
        await show_profile(update, context)

    elif text == "Редактировать профиль":
        context.user_data.clear()
        await update.message.reply_text(
            "Давай обновим твой профиль! Как тебя зовут?",
            reply_markup=ForceReply(selective=True),
        )
        return NAME
    elif text == "Удалить профиль":
        c.execute('DELETE FROM people WHERE id = ?',(update.effective_user.id,))
        conn.commit()
        await update.message.reply_text(
            "Профиль удален!",
            reply_markup=ForceReply(selective=True),
        )



async def cancel_search(update, context):
    keyboard = [
        [[KeyboardButton("Начать поиск"),
          KeyboardButton("Показать профиль")],
         [KeyboardButton("Редактировать профиль"), KeyboardButton("Удалить профиль")]]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Поиск завершен!",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(bot_token).build()

    # ConversationHandler для создания анкеты
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),MessageHandler(filters.Text("Редактировать профиль"), handle_buttons),],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, about)],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, save_profile)],
        },
        fallbacks=[CommandHandler('cancel', cancel_search)]
    )

    # ConversationHandler для поиска
    search_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text("Начать поиск"), start_match),
            CommandHandler('search', start_match)
        ],
        states={
            REACTION: [MessageHandler(filters.Text(["❤️", "👎"]), process_reaction)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_search),
            MessageHandler(filters.Text("Показать профиль"), handle_buttons)
        ],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(search_handler)
    app.add_handler(MessageHandler(filters.Text(["Показать профиль", "Редактировать профиль", "Удалить профиль"]), handle_buttons))
    app.add_handler(CommandHandler('profile', show_profile))
    app.add_handler(CommandHandler('search', start_match))

    print("Бот запущен...")
    app.run_polling()


if __name__ == '__main__':
    main()
