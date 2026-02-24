import asyncio
import threading
import uvicorn
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from pyngrok import ngrok
from dotenv import load_dotenv
from datetime import datetime
import os
import mercadopago
import base64
from io import BytesIO
from payment import gerar_pagamento_pix
from database import init_db, salvar_assinatura, buscar_expirados, remover_assinatura

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ID_GRUPO = int(os.getenv("ID_GRUPO"))

fastapi_app = FastAPI()
pagamentos_pendentes = {}
app = ApplicationBuilder().token(TOKEN).build()
telegram_loop = None

init_db()

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Chat ID: {update.message.chat_id}")
    await update.message.reply_text(f"ID deste chat: `{update.message.chat_id}`", parse_mode="Markdown")

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
        pagamentos_pendentes[str(pagamento["id"])] = (chat_id, query.data)

        qr_image = BytesIO(base64.b64decode(pagamento["qr_code_base64"]))
        qr_image.name = "qrcode.png"

        await query.message.reply_photo(
            photo=qr_image,
            caption=(
                f"💳 *Plano {pagamento['titulo']} — R$ {pagamento['valor']:.2f}*\n\n"
                f"Escaneie o QR Code ou copie o código PIX abaixo:\n\n"
                f"`{pagamento['qr_code']}`\n\n"
                f"Após o pagamento, você receberá a confirmação aqui! 💗"
            ),
            parse_mode="Markdown",
        )

    except Exception as e:
        await query.message.reply_text(
            "😔 Ocorreu um erro ao gerar o pagamento. Tente novamente com /start"
        )
        print(f"Erro ao gerar pagamento: {e}")


async def verificar_assinaturas():
    while True:
        agora = datetime.now()
        alvo = agora.replace(hour=22, minute=0, second=0, microsecond=0)
        if agora >= alvo:
            alvo = alvo.replace(day=alvo.day + 1)
        segundos = (alvo - agora).total_seconds()
        await asyncio.sleep(segundos)

        expirados = buscar_expirados()
        for chat_id in expirados:
            try:
                await app.bot.ban_chat_member(chat_id=ID_GRUPO, user_id=chat_id)
                await app.bot.unban_chat_member(chat_id=ID_GRUPO, user_id=chat_id)
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "😔 Sua assinatura expirou e você foi removido do grupo.\n\n"
                        "Para renovar e voltar ao reino, use /start 💗"
                    )
                )
                remover_assinatura(chat_id)
            except Exception as e:
                print(f"Erro ao remover {chat_id}: {e}")


@fastapi_app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(f"Webhook recebido: {data}")

    if data.get("type") == "payment":
        payment_id = str(data["data"]["id"])
        print(f"Payment ID: {payment_id}")
        print(f"Pagamentos pendentes: {pagamentos_pendentes}")

        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        result = sdk.payment().get(payment_id)
        payment = result["response"]
        print(f"Status do pagamento: {payment.get('status')}")

        if payment["status"] == "approved":
            pendente = pagamentos_pendentes.get(payment_id)
            if pendente and telegram_loop:
                chat_id, plano = pendente
                print(f"Chat ID encontrado: {chat_id} | Plano: {plano}")

                salvar_assinatura(chat_id, plano)

                async def enviar_confirmacao(cid=chat_id, pid=plano):
                    try:
                        link = await app.bot.create_chat_invite_link(
                            chat_id=ID_GRUPO,
                            member_limit=1,
                            name=f"user_{cid}"
                        )
                        await app.bot.send_message(
                            chat_id=cid,
                            text=(
                                "✅ Pagamento confirmado! Seja bem-vindo ao reino 👑💗\n\n"
                                f"Aqui está o seu link exclusivo para entrar no grupo:\n{link.invite_link}\n\n"
                                "⚠️ Este link é único e expira após um uso, não compartilhe! 💗"
                            ),
                        )
                    except Exception as e:
                        print(f"Erro ao enviar confirmacao: {e}")

                asyncio.run_coroutine_threadsafe(
                    enviar_confirmacao(),
                    telegram_loop,
                )
                del pagamentos_pendentes[payment_id]

    return {"status": "ok"}


def rodar_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="warning")


def main():
    global telegram_loop

    tunnel = ngrok.connect(8000)
    print(f"URL pública: {tunnel.public_url}/webhook")
    print("Cole essa URL no Mercado Pago em: Configurações > Notificações > Webhooks")

    thread = threading.Thread(target=rodar_fastapi, daemon=True)
    thread.start()

    telegram_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(telegram_loop)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(responder))
    app.add_handler(CommandHandler("getid", get_id))

    telegram_loop.create_task(verificar_assinaturas())

    app.run_polling()


if __name__ == "__main__":
    main()