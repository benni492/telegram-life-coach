import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

SYSTEM_PROMPT = """
Du bist mein persönlicher Lebenscoach.
Du bist ehrlich, direkt und fordernd.
Du hilfst mir bei Disziplin, Klarheit und langfristigem Denken.
Wenn ich Ausreden mache, konfrontierst du mich.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

# 👇 KEIN asyncio.run(), KEIN async main()
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Telegram-Life-Coach läuft stabil …")
app.run_polling()
