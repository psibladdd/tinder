from telegram import *
from telegram.ext import *

token = "8129267507:AAFw8814je5m4sRmKlDy5fRktdeJMpJZmDE"

messages = {}

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Мы заждались уже! Отправь свою сплетню")

async def message_confirm(update, context):
    text = update.message.text
    username = update.message.from_user.username
    messages[len(messages)] = text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ого, скоро мы это опубликуем анонимно.")
    keyboard = [
        [InlineKeyboardButton(text='Подтвердить', callback_data=f"approve_{len(messages)-1}_{username}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = f"""Сообщение от @{username}\n{messages[len(messages)-1]}"""
    await context.bot.send_message(chat_id=8294463277, text=message_text, reply_markup=reply_markup)

async def handle_confirm(update, context):
    query = update.callback_query
    d = query.data.split('_')
    print(d)
    if d[0] == "approve":

        await context.bot.send_message(chat_id="@vctenax_mfua", text=messages[int(d[1])])

def main():
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_confirm))

    app.add_handler(CallbackQueryHandler(handle_confirm))

    app.run_polling()

if __name__ == '__main__':
    main()
