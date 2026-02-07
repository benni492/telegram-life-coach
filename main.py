import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

# ===============================
# ENVIRONMENT
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

# ===============================
# MEMORY (einfach & stabil)
# ===============================
MEMORY_FILE = "memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "ziele": [],
            "probleme": [],
            "coach_stil": [],
            "wichtige_infos": []
        }

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

# ===============================
# MESSAGE HANDLER
# ===============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    memory = load_memory()

    # ---------
    # einfache Heuristik: was merken?
    # ---------
    lower = user_message.lower()

    if "ziel" in lower or "sidehustle" in lower or "ki" in lower:
        if user_message not in memory["ziele"]:
            memory["ziele"].append(user_message)

    if "schwer" in lower or "problem" in lower or "anfangen" in lower:
        if user_message not in memory["probleme"]:
            memory["probleme"].append(user_message)

    if "sei" in lower and ("direkt" in lower or "streng" in lower or "nett" in lower):
        if user_message not in memory["coach_stil"]:
            memory["coach_stil"].append(user_message)

    save_memory(memory)

    # ---------
    # SYSTEM PROMPT MIT GEDÄCHTNIS
    # ---------
    system_message = f"""
Du bist mein persönlicher Lebenscoach.

WICHTIGE INFOS ÜBER MICH:
Ziele: {memory["ziele"]}
Probleme: {memory["probleme"]}
Coach-Stil: {memory["coach_stil"]}
Sonstiges: {memory["wichtige_infos"]}

Dein Stil:
- ehrlich
- direkt
- handlungsorientiert
- nicht nett, wenn ich ausweiche

Wenn ich nur nachdenke oder zögere, zwing mich zu EINER konkreten nächsten Aktion.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

# ===============================
# BOT START
# ===============================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Telegram-Life-Coach läuft mit Gedächtnis …")
app.run_polling()
