from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv
import os
from payment import gerar_pagamento_pix

load_dotenv()

token = os.getenv("MP_ACCESS_TOKEN")
print(f">>> TOKEN: {token}")
TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("1 mês / R$ 12,90", callback_data="1"),
            InlineKeyboardButton("2 meses / R$ 20,00", callback_data="2"),
            InlineKeyboardButton("3 meses / R$ 30,00", callback_data="3"),
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
            "Escolhe seu plano aqui embaixo…"
        ),
        reply_markup=reply_markup,
    )


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Remove os botões para não poder clicar de novo
    await query.edit_message_reply_markup(reply_markup=None)

    user_id = query.from_user.id

    try:
        pagamento = gerar_pagamento_pix(query.data, user_id)

        await query.message.reply_text(
            f"💳 *Plano {pagamento['titulo']} — R$ {pagamento['valor']:.2f}*\n\n"
            f"Pague via PIX com o código abaixo:\n\n"
            f"`{pagamento['qr_code']}`\n\n"
            f"Após o pagamento, você receberá a confirmação aqui! 💗",
            parse_mode="Markdown"
        )

    except Exception as e:
        await query.message.reply_text(
            "😔 Ocorreu um erro ao gerar o pagamento. Tente novamente com /start"
        )
        print(f"Erro ao gerar pagamento: {e}")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(responder))

app.run_polling()