# telegrambot.py
import os
os.environ["PYTHONUTF8"] = "1"

import joblib
from groq import Groq
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

# load your DBS model
model = joblib.load("dbs.jl")
# init Groq client
client = Groq()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Send me any question to chat, or /predict USD/SGD to get a DBS share‐price prediction."
    )

async def predict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /predict 1.35")
    try:
        rate = float(context.args[0])
        pred = model.predict([[rate]])[0]
        await update.message.reply_text(f"Predicted DBS share price: {pred:.2f}")
    except Exception as e:
        err = str(e).encode("ascii", "ignore").decode("ascii")
        await update.message.reply_text(f"[Error] Could not parse rate: {err}")

async def chat_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}],
        )
        raw = resp.choices[0].message.content
        clean = raw.encode("ascii", "ignore").decode("ascii")
        await update.message.reply_text(clean)
    except Exception as e:
        # remove any non-ASCII before sending
        err = str(e).encode("ascii", "ignore").decode("ascii")
        await update.message.reply_text(f"Error: {err}")


if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_msg))

    app.run_polling()  # long‐polling for local/dev
