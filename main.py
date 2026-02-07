import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI
from datetime import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

MEMORY_FILE = "/app/memory.json"

# =====================
# MEMORY (ROBUST)
# =====================
def load_data():
    if not os.path.exists(MEMORY_FILE):
        return {
            "profile": {
                "ziele": [],
                "probleme": [],
                "coach_stil": []
            },
            "chat_id": None
        }

    with open(MEMORY_FILE, "r") as f:
        data = json.load(f)

    # 🔑 ABSOLUT KRITISCHER FIX
    if "profile" not in data:
        data["profile"] = {
            "ziele": [],
            "probleme": [],
            "coach_stil": []
        }

    if "chat_id" not in data:
        data["chat_id"] = None

    return data

def save_data(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# MESSAGE HANDLER
# =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = update.message.text
    lower = msg.lower()

    # Chat-ID merken
    data["chat_id"] = update.message.chat_id

    # Profil-Gedächtnis
    if "sidehustle" in lower or "ki" in lower:
        if msg not in data["profile"]["ziele"]:
            data["profile"]["ziele"].append(msg)

    if "anfangen" in lower or "schwer" in lower:
        if msg not in data["profile"]["probleme"]:
            data["profile"]["probleme"].append(msg)

    if "sei" in lower:
        if msg not in data["profile"]["coach_stil"]:
            data["profile"]["coach_stil"].append(msg)

    save_data(data)

    system_message = f"""
Du bist mein persönlicher Lebenscoach.

Profil:
Ziele: {data["profile"]["ziele"]}
Probleme: {data["profile"]["probleme"]}
Coach-Stil: {data["profile"]["coach_stil"]}

Sei ehrlich, direkt und zwing mich zu EINER konkreten Aktion.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": msg}
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

# =====================
# PUSH JOBS (STABIL)
# =====================
async def morning_push(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if data["chat_id"]:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text="🌅 Was ist heute die *eine konkrete Aktion*, die dich deinem KI-Sidehustle näherbringt?"
        )

async def evening_push(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if data["chat_id"]:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text="🌙 Was hast du heute konkret getan? Wenn nichts: warum?"
        )

# =====================
# START BOT
# =====================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

job_queue = app.job_queue
job_queue.run_daily(morning_push, time=time(hour=8, minute=0))
job_queue.run_daily(evening_push, time=time(hour=21, minute=30))

print("🤖 Coach läuft stabil + Gedächtnis + Push")
app.run_polling()
