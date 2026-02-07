import os
import json
import time
import threading
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

MEMORY_FILE = "/app/memory.json"

def load_data():
    if not os.path.exists(MEMORY_FILE):
        return {
            "profile": {
                "ziele": [],
                "probleme": [],
                "coach_stil": []
            },
            "chat_id": None,
            "last_morning": None,
            "last_evening": None
        }
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = update.message.text
    lower = msg.lower()

    data["chat_id"] = update.message.chat_id

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

Sei ehrlich, direkt und zwing mich zu konkreten Aktionen.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": msg}
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

def push_loop(app):
    while True:
        data = load_data()
        now = datetime.now()
        today = now.date().isoformat()

        if data["chat_id"]:
            # MORGEN 08:00
            if now.hour == 8 and data["last_morning"] != today:
                app.bot.send_message(
                    chat_id=data["chat_id"],
                    text="🌅 Was ist heute die EINE konkrete Aktion, die dich deinem Sidehustle oder KI-Ziel näherbringt?"
                )
                data["last_morning"] = today
                save_data(data)

            # ABEND 21:30
            if now.hour == 21 and now.minute >= 30 and data["last_evening"] != today:
                app.bot.send_message(
                    chat_id=data["chat_id"],
                    text="🌙 Was hast du heute konkret getan? Wenn nichts: warum?"
                )
                data["last_evening"] = today
                save_data(data)

        time.sleep(30)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

threading.Thread(target=push_loop, args=(app,), daemon=True).start()

print("🤖 Coach läuft + schreibt dich aktiv an")
app.run_polling()
