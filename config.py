# config.py

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# --- Configuration ---
TELEGRAM_TOKEN = "BOT_TOKEN" 

# --- Global Constants ---
RESTART_BUTTON_TEXT = "Start New QR"
START_QR_CALLBACK_DATA = "/start_qr_reset" # Hidden data to trigger the command reset

PERSISTENT_REPLY_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(RESTART_BUTTON_TEXT, callback_data=START_QR_CALLBACK_DATA)]
])

# Inline Keyboard for message-bonded 'Go Back'
BACK_BUTTON_TEXT = "⬅️ Go Back" 
INLINE_BACK_DATA = "GO_BACK"
INLINE_BACK_KEYBOARD = InlineKeyboardMarkup([[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data=INLINE_BACK_DATA)]])

COLOR_HEX_MAP = {
    "red": "#FF0000", "blue": "#0000FF", "green": "#008000", 
    "yellow": "#FFFF00", "orange": "#FFA500", "grey": "#808080", 
    "black": "#000000", "pink": "#FFC0CB" 
}
VALID_COLORS = list(COLOR_HEX_MAP.keys())

# --- Conversation States ---
GET_COLOR, GET_LOGO, GET_TEXT = range(3)

# --- Initial Reply Keyboard (Color Selection) ---
COLOR_KEYBOARD = [
    [KeyboardButton("Red"), KeyboardButton("Blue"), KeyboardButton("Green")],
    [KeyboardButton("Yellow"), KeyboardButton("Orange"), KeyboardButton("Pink")],
    [KeyboardButton("Grey"), KeyboardButton("Black")],
]
COLOR_REPLY_MARKUP = ReplyKeyboardMarkup(COLOR_KEYBOARD, one_time_keyboard=True, resize_keyboard=True)