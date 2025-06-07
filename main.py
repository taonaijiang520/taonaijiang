print("TOKEN from env:", os.environ.get("TOKEN"))
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os

TOKEN = os.environ.get("TOKEN")
CHINESE_URL = "https://t.me/setlanguage/zhcncc"
BOT_USERNAME = "xlngchenBot"  # 桃奈酱机器人的用户名
OWNER_USERNAME = "baby_520"   # 你的 Telegram 用户名

WELCOME_TEXT = (
    "欧尼酱点开桃奈酱就是要换中文嘛？"
    "那…桃奈酱跪着求你点进去…"
    "里面好湿…是中文版啦♡"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 中文包", url=CHINESE_URL)],
        [InlineKeyboardButton("📨 双向（留言给主人）", url=f"https://t.me/{BOT_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_TEXT, reply_markup=reply_markup)

async def relay_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        sender = update.effective_user
        text = update.message.text
        await context.bot.send_message(chat_id=f"@{OWNER_USERNAME}",
            text=f"📨 来自 @{sender.username or sender.first_name} 的留言：

{text}")
        await update.message.reply_text("桃奈酱已经把你的话贴贴地送过去啦♡")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), relay_to_owner))
    app.run_polling()
