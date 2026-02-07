import os
import time
import psycopg2
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

# =====================
# ENV
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

client = OpenAI(api_key=OPENAI_KEY)

# =====================
# DATABASE (robust)
# =====================
def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )

def init_db():
    for _ in range(10):  # Retry bis DB bereit ist
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT,
                    value TEXT
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("DB nicht erreichbar")

def get_memory():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM memory")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    memory = {
        "ziele": [],
        "probleme": [],
        "coach_stil": [],
        "wichtige_infos": []
    }

    for k, v in rows:
        if k in memory:
            memory[k].append(v)

    return memory

def save_memory(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO memory (key, value) VALUES (%s, %s)",
        (key, value)
    )
    conn.commit()
    cur.close()
    conn.close()

# =====================
# MESSAGE HANDLER
# =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lower = user_message.lower()

    if "sidehustle" in lower or "ziel" in lower or "ki" in lower:
        save_memory("ziele", user_message)

    if "schwer" in lower or "anfangen" in lower or "problem" in lower:
        save_memory("probleme", user_message)

    if "sei" in lower and ("direkt" in lower or "streng" in lower):
        save_memory("coach_stil", user_message)

    memory = get_memory()

    system_message = f"""
Du bist mein persönlicher Lebenscoach.

WICHTIGE INFOS ÜBER MICH:
Ziele: {memory["ziele"]}
Probleme: {memory["probleme"]}
Coach-Stil: {memory["coach_stil"]}

Dein Stil:
- ehrlich
- direkt
- handlungsorientiert
- zwing mich zu konkreten Aktionen
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

# =====================
# START BOT
# =====================
init_db()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Coach läuft stabil mit DB")
app.run_polling()
