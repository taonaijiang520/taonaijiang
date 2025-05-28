import os
import logging
import requests
import sqlite3
import openai
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# 日志配置
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# 环境变量
BOT_TOKEN      = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
PORT           = int(os.getenv("PORT", 10000))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "").lstrip("@")

assert BOT_TOKEN and BOT_TOKEN.startswith("754"), "❌ BOT_TOKEN 未配置或格式不对"
assert WEBHOOK_DOMAIN and WEBHOOK_DOMAIN.startswith("https://"), "❌ WEBHOOK_DOMAIN 未配置或必须以 https:// 开头"

# SQLite 初始化
DB_PATH = "data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_keys (
  user_id TEXT PRIMARY KEY,
  api_key TEXT NOT NULL
)""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_logs (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id   TEXT,
  timestamp TEXT,
  message   TEXT,
  ip        TEXT
)""")
conn.commit()

# 支付方式映射
PAY_METHODS = {
    "alipay": {"label": "支付宝", "api": "ALIPAY"},
    "wechat": {"label": "微信",   "api": "WECHAT"},
    "bank":   {"label": "银行卡","api": "BANK_CARD"},
}

# 绑定 Webhook
def bind_webhook():
    url = f"{WEBHOOK_DOMAIN}/webhook"
    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": url},
        timeout=10
    )
    logging.info(f"Webhook 设置响应：{resp.status_code} → {resp.text}")

# 对话状态
STATE_BIND_KEY = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("📊 今日 USDT", callback_data="usdt_alipay")],
        [InlineKeyboardButton("🔑 绑定 ChatGPT Key", callback_data="bind_key")],
        [InlineKeyboardButton("❓ 帮助", callback_data="help")],
    ]
    if user.username == OWNER_USERNAME:
        kb.append([InlineKeyboardButton("⚙️ 开发者后台", callback_data="dev")])
    await update.message.reply_text(
        "🍑 桃奈酱欢迎你～\n\n请选择：",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = q.from_user
    data = q.data
    await q.answer()

    if data == "help":
        await q.edit_message_text(
            "• /start：返回主菜单\n"
            "• 🔑 绑定 ChatGPT Key\n"
            "• 📊 今日 USDT\n"
            "• 开发者可查看日志"
        )
        return

    if data == "bind_key":
        await q.edit_message_text(
            "请输入你的 OpenAI API Key：\n`sk-...`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return STATE_BIND_KEY

    if data.startswith("usdt_"):
        method = data.split("_", 1)[1]
        resp_data = requests.get(
            "https://www.okx.com/api/v5/asset-c2c/tradingOrders/book",
            params={
                "quoteCurrency": "CNY",
                "baseCurrency": "USDT",
                "tradeType": "buy",
                "payMethod": PAY_METHODS[method]["api"],
                "limit": 10
            }, timeout=10
        ).json().get("data", [])[:10]
        text = f"📊 USDT C2C 买入价（{PAY_METHODS[method]['label']}）\n\n"
        for i, r in enumerate(resp_data, 1):
            text += f"{i}. ¥{r['price']} (限额 {r['minTransAmount']}-{r['maxTransAmount']} CNY)\n"
        buttons = [
            InlineKeyboardButton(PAY_METHODS[m]["label"], callback_data=f"usdt_{m}")
            for m in PAY_METHODS if m != method
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([buttons]))
        return

    if data == "dev":
        if user.username != OWNER_USERNAME:
            await q.edit_message_text("❌ 无权限访问后台。")
        else:
            dev_kb = [
                [InlineKeyboardButton("📋 查看日志", callback_data="view_logs")],
                [InlineKeyboardButton("🧹 清理缓存", callback_data="clear_cache")],
            ]
            await q.edit_message_text("⚙️ 开发者后台：请选择操作", reply_markup=InlineKeyboardMarkup(dev_kb))
        return

    if data == "view_logs":
        rows = cursor.execute(
            "SELECT user_id,timestamp,message FROM user_logs ORDER BY id DESC LIMIT 20"
        ).fetchall()
        text = "\n".join(f"{r[1]} | {r[0]} | {r[2][:30]}…" for r in rows) or "（无日志）"
        await q.edit_message_text(f"🛠️ 最近交互日志：\n{text}")
        return

    if data == "clear_cache":
        cache_dir = "./temp_cache"
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, f))
        await q.edit_message_text("✅ 缓存已清理完成！")
        logging.info("应用缓存已清理。")
        return

async def receive_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = update.message.text.strip()
    uid = str(update.effective_user.id)
    cursor.execute(
        "INSERT OR REPLACE INTO user_keys(user_id,api_key) VALUES(?,?)",
        (uid, key)
    )
    conn.commit()
    await update.message.reply_text("✅ 已绑定你的 API Key！")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("已取消。", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    msg = update.message.text
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    cursor.execute(
        "INSERT INTO user_logs(user_id,timestamp,message,ip) VALUES(?,?,?,?)",
        (uid, ts, msg, "N/A")
    )
    conn.commit()
    row = cursor.execute(
        "SELECT api_key FROM user_keys WHERE user_id=?", (uid,)
    ).fetchone()
    if not row:
        await update.message.reply_text("❌ 未绑定 API Key，请先 /start 并绑定")
        return
    openai.api_key = row[0]
    for model in ["gpt-4o", "gpt-3.5-turbo"]:
        try:
            res = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role":"system","content":"你是“桃奈酱”，一个可爱软萌的贴贴 AI~"},
                    {"role":"user","content":msg}
                ],
                temperature=0.8
            )
            await update.message.reply_text(res.choices[0].message.content)
            return
        except Exception as e:
            logging.warning(f"{model} 调用失败：{e}")
    await update.message.reply_text("❌ ChatGPT 服务暂不可用，请稍后再试。")

def main():
    logging.info("正在设置 Webhook …")
    bind_webhook()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_button, pattern="^bind_key$")],
        states={STATE_BIND_KEY:[MessageHandler(filters.TEXT & ~filters.COMMAND, receive_key)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    logging.info("🍑 桃奈酱启动中，监听 Webhook …")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=f"{WEBHOOK_DOMAIN}/webhook",
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
