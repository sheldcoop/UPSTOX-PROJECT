import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ai_service import AIService

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load Environment
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN or TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
    logger.warning(
        "TELEGRAM_BOT_TOKEN is missing or default. Bot will not start correctly."
    )

# Initialize AI Service
try:
    ai_service = AIService()
    logger.info("AI Service connected successfully.")
except Exception as e:
    logger.error(f"Failed to initialize AI Service: {e}")
    ai_service = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I am your Upstox Trading Assistant.\n"
        "Ask me about market 'Gainers', your 'Holdings', or stock prices!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    await update.message.reply_text(
        "Try asking: 'What are the top gainers today?' or 'Show my portfolio holdings'."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    user_text = update.message.text

    if not ai_service:
        await update.message.reply_text(
            "Sorry, the AI service is currently unavailable."
        )
        return

    # Indicate processing
    status_msg = await update.message.reply_text("Thinking...")

    try:
        # Run synchronous AI call in a separate thread to avoid blocking the async loop
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, ai_service.send_message, user_text)

        # Edit the status message with the response (or send new if too long, but edit is nicer)
        # Telegram limit is 4096 chars.
        if len(response) > 4000:
            for x in range(0, len(response), 4000):
                await update.message.reply_text(response[x : x + 4000])
            await status_msg.delete()
        else:
            await status_msg.edit_text(
                response
            )  # Parse mode markdown optional, stick to text for safety

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await status_msg.edit_text(
            "Sorry, something went wrong while processing your request."
        )


def main() -> None:
    """Start the bot."""
    if not TOKEN or TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Error: TELEGRAM_BOT_TOKEN not configured in .env")
        return

    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Run the bot
    print("Starting Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
