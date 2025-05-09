import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ——— CONFIG ———
BOT_TOKEN = "8017549984:AAF62dNKpx40l0DX9bPnPNBOmObO2TqndsE"
BINLIST_URL = "https://lookup.binlist.net/{}"
# ——————————

# Enable logging (optional, but great for debugging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a greeting and brief help when /start is issued."""
    await update.message.reply_text(
        "👋 Hi! Send me the first 6 digits of a card (the BIN), "
        "and I'll look up its issuer info for you."
    )


async def check_bin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message that looks like a BIN and reply with lookup info."""
    text = update.message.text.strip()
    if not text.isdigit() or len(text) not in (6, 8):
        return await update.message.reply_text(
            "⚠️ Please send just the first 6 (or 8) digits of the card."
        )

    bin_number = text
    url = BINLIST_URL.format(bin_number)
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()

            # Safe access for card level info
            card_level = data.get('card', {}).get('type', 'n/a') if 'card' in data else 'n/a'

            # Build a nice reply with error checks
            reply = (
                f"🔍 BIN Lookup for *{bin_number}*\n\n"
                f"• Scheme: `{data.get('scheme', 'n/a')}`\n"
                f"• Brand: `{data.get('brand', 'n/a')}`\n"
                f"• Type: `{data.get('type', 'n/a')}`\n"
                f"• Card level: `{card_level}`\n"
                f"• Bank: `{data.get('bank', {}).get('name', 'n/a')}`\n"
                f"• Country: `{data.get('country', {}).get('name', 'n/a')}`\n"
            )
            await update.message.reply_markdown(reply)
        elif resp.status_code == 429:
            await update.message.reply_text("⏳ Rate limit exceeded—please wait a bit.")
        else:
            await update.message.reply_text("❌ BIN not found or service error.")
    except requests.RequestException as e:
        logger.error("Error fetching BIN info: %s", e)
        await update.message.reply_text("⚠️ Network error—please try again later.")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start command
    app.add_handler(CommandHandler("start", start))

    # Any text → BIN check
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_bin))

    print("🤖 BIN-check bot is running…")
    app.run_polling()
