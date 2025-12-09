import logging
import re
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler

# Import states and constants
from config import TELEGRAM_TOKEN, GET_COLOR, GET_LOGO, GET_TEXT, INLINE_BACK_DATA, RESTART_BUTTON_TEXT, START_QR_CALLBACK_DATA 

# Import handlers and filters
from handlers import (
    start_custom_qr, get_color, prompt_for_logo, get_logo_and_prompt_text, 
    skip_logo, get_text_and_finish, cancel, go_back, 
    handle_photo_when_text_expected, handle_wrong_input, handle_new_start, 
    handle_restart_prompt
)
from filters import IMAGE_FILE_FILTER


# --- Setup ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Main Bot Setup ---
def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_custom_qr)],
        states={
            GET_COLOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_color),
                MessageHandler(filters.ALL & ~filters.TEXT & ~filters.COMMAND, handle_wrong_input)
            ],
            GET_LOGO: [
                CallbackQueryHandler(go_back, pattern=f"^{re.escape(INLINE_BACK_DATA)}$"), 
                CommandHandler("skip", skip_logo), 
                MessageHandler(IMAGE_FILE_FILTER, get_logo_and_prompt_text), 
                MessageHandler(filters.ALL, handle_wrong_input) 
            ],
            GET_TEXT: [
                CallbackQueryHandler(go_back, pattern=f"^{re.escape(INLINE_BACK_DATA)}$"), 
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_text_and_finish),
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_photo_when_text_expected), 
                MessageHandler(filters.ALL, handle_wrong_input) 
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.ALL, handle_wrong_input) 
        ],
    )

    application.add_handler(conv_handler)
    
    # --- Persistent Handlers ---
    # 🚨 FIX: Handler for the INLINE 'Start New QR' button press (CallbackQueryHandler)
    application.add_handler(
        CallbackQueryHandler(handle_new_start, pattern=f"^{re.escape(START_QR_CALLBACK_DATA)}$")
    )

    # General fallback for messages outside of conversation
    application.add_handler(
        MessageHandler(filters.ALL, handle_restart_prompt)
    )
    
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()