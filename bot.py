from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="1"),
            InlineKeyboardButton("2", callback_data="2"),
            InlineKeyboardButton("3", callback_data="3"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=open("photo.jpg", "rb"),
        caption=(
            "Oi amor… você chegou até aqui 🥺\n"
            "Eu sou seu príncipe… faça parte do meu reino 💗\n"
            "Por R$12,90 você já pode me ter por um mês…\n"
            "Mas se quiser me manter por 3 inteiros por R$30… eu prometo ser todinho seu 👑✨\n\n"
            "Escolhe seu plano aqui embaixo…\n\n"
            "1 mês / R$ 12,90\n"
            "2 meses / R$ 20,00\n"
            "3 meses / R$ 30,00"
        ),
        reply_markup=reply_markup,
    )


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Remove os botões da mensagem
    await query.edit_message_reply_markup(reply_markup=None)

    if query.data == "1":
        await query.message.reply_text("Você escolheu 1 mês / R$ 12,90! 💗")
    elif query.data == "2":
        await query.message.reply_text("Você escolheu 2 meses / R$ 20,00! 💗")
    elif query.data == "3":
        await query.message.reply_text("Você escolheu 3 meses / R$ 30,00! 💗")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(responder))  # handler diferente para inline

app.run_polling()
