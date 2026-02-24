# Bibliotecas para servidor FastAPI 
import asyncio
import uvicorn
from fastapi import FastAPI, Request

# Bibliotecas para Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Biblioteca para ngrok exposição da máquina e comunicação webhook
from pyngrok import ngrok

# Biblioteca para comunicação com Mercado Pago
import mercadopago
from payment import gerar_pagamento_pix

# Biblioteca para carregar variáveis de ambiente
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# FastAPI para receber webhook do Mercado Pago
fastapi_app = FastAPI()

# Guarda o chat_id de cada pagamento {payment_id: chat_id}
pagamentos_pendentes = {}

# App do Telegram
app = ApplicationBuilder().token(TOKEN).build()


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
    await query.edit_message_reply_markup(reply_markup=None)

    user_id = query.from_user.id
    chat_id = query.message.chat_id

    try:
        pagamento = gerar_pagamento_pix(query.data, user_id)

        # Salva o chat_id para notificar quando pagar
        pagamentos_pendentes[str(pagamento["id"])] = chat_id

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


# Webhook do Mercado Pago
@fastapi_app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(f"Webhook recebido: {data}")

    if data.get("type") == "payment":
        payment_id = str(data["data"]["id"])

        # Consulta o pagamento no Mercado Pago
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        result = sdk.payment().get(payment_id)
        payment = result["response"]

        if payment["status"] == "approved":
            chat_id = pagamentos_pendentes.get(payment_id)
            if chat_id:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Pagamento confirmado! Seja bem-vindo ao reino 👑💗\n\nEm breve você receberá o acesso!"
                )
                del pagamentos_pendentes[payment_id]

    return {"status": "ok"}


async def main():
    # Inicia o ngrok
    tunnel = ngrok.connect(8000)
    url_publica = tunnel.public_url
    print(f"URL pública: {url_publica}/webhook")
    print("Cole essa URL no Mercado Pago em: Configurações > Notificações > Webhooks")

    # Roda FastAPI e Telegram juntos
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        app.run_polling(),
    )


if __name__ == "__main__":
    asyncio.run(main())
