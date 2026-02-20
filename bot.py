from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

# Buscando Token do arquivo .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Criando Função para o comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Olá! Eu sou seu bot!")

# Criando Função para o comando /bomdia
async def bomdia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌞 Bom dia! Que seu dia seja produtivo!")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("bomdia", bomdia))

app.run_polling()
