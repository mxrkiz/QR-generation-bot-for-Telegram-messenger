import io
import logging
import re
from PIL import Image
import qrcode
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Import constants from config
from config import (
    GET_COLOR, GET_LOGO, GET_TEXT,
    INLINE_BACK_DATA, INLINE_BACK_KEYBOARD, 
    COLOR_REPLY_MARKUP, VALID_COLORS, PERSISTENT_REPLY_MARKUP,
    COLOR_HEX_MAP, RESTART_BUTTON_TEXT 
)

logger = logging.getLogger(__name__)

# --- Helper Function: The Core QR Generator ---
def create_custom_qr(data: str, fill_color: str = 'black', logo_bytes: bytes | None = None):
    """Generates a fully customized QR code with stable color and an optional logo."""
    
    hex_code = COLOR_HEX_MAP.get(fill_color.lower(), "#000000")
    
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H, 
        box_size=100, 
        border=3,    
    )
    qr.add_data(data)
    qr.make(fit=True) 

    img = qr.make_image(fill_color=hex_code, back_color="white").convert("RGB") 

    if logo_bytes:
        try:
            logo_pil = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            img_size = img.size[0]
            logo_max_size = img_size // 4
            logo_pil.thumbnail((logo_max_size, logo_max_size))
            logo_pos = ((img_size - logo_pil.width) // 2, (img_size - logo_pil.height) // 2)
            img.paste(logo_pil, logo_pos, mask=logo_pil)
        except Exception as e:
            logger.error(f"Failed to add logo to QR code: {e}")

    final_buffer = io.BytesIO()
    final_buffer.name = "qrcode.png"
    img.save(final_buffer, format="PNG")
    final_buffer.seek(0)
    
    return final_buffer

# --- Navigation Logic ---

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Go Back' callback query."""
    
    query = update.callback_query
    await query.answer()

    current_state = context.user_data.get('current_state')

    if current_state == GET_LOGO:
        logger.info(f"User {query.from_user.id} navigating back from GET_LOGO to GET_COLOR.")
        
        context.user_data.pop('color', None)
        context.user_data['current_state'] = GET_COLOR

        keyboard = [
            [KeyboardButton("Red"), KeyboardButton("Blue"), KeyboardButton("Green")],
            [KeyboardButton("Yellow"), KeyboardButton("Orange"), KeyboardButton("Pink")],
            [KeyboardButton("Grey"), KeyboardButton("Black")],
        ]
        color_reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await query.edit_message_text("You went back. Choose a color from the panel below.", reply_markup=None)
        await query.message.reply_text("Color menu:", reply_markup=color_reply_markup)
        
        return GET_COLOR
    
    elif current_state == GET_TEXT:
        logger.info(f"User {query.from_user.id} navigating back from GET_TEXT to GET_LOGO.")
        
        context.user_data.pop('logo', None)
        context.user_data['current_state'] = GET_LOGO
        
        await query.edit_message_text(
            f"You went back. Color is still: {context.user_data.get('color', 'black').title()}\n\n"
            "Now, send me an image for the middle logo (optional), or send /skip.",
            reply_markup=INLINE_BACK_KEYBOARD 
        )
        return GET_LOGO

    else:
        logger.warning(f"User {query.from_user.id} pressed back with unclear state {current_state}. Restarting.")
        await query.edit_message_text("Flow error. Please /start again.", reply_markup=PERSISTENT_REPLY_MARKUP)
        return ConversationHandler.END


# --- Conversation Handlers ---

async def start_custom_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and sets up the Reply Keyboard for color selection."""
    context.user_data.clear()
    context.user_data['active_qr_session'] = True
    context.user_data['current_state'] = GET_COLOR
    
    await update.message.reply_text("Starting new QR...", reply_markup=ReplyKeyboardRemove())
    
    keyboard = [
        [KeyboardButton("Red"), KeyboardButton("Blue"), KeyboardButton("Green")],
        [KeyboardButton("Yellow"), KeyboardButton("Orange"), KeyboardButton("Pink")],
        [KeyboardButton("Grey"), KeyboardButton("Black")],
    ]
    color_reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "First, choose a color from the panel below.",
        reply_markup=color_reply_markup
    )
    return GET_COLOR

async def get_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates color input, stores it, and asks for the logo."""
    color = update.message.text.lower()
    
    if color not in VALID_COLORS:
        await update.message.reply_text(
            f"Invalid color choice: '{color.title()}'. Please choose one of the available options."
        )
        return GET_COLOR
        
    context.user_data['color'] = color
    logger.info(f"User {update.effective_user.id} set color to: {color}")
    
    return await prompt_for_logo(update, context)

async def prompt_for_logo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the user for a logo and provides the Inline 'Go Back' button."""
    
    context.user_data['current_state'] = GET_LOGO
    
    await update.message.reply_text(
        f"Color set to: {context.user_data.get('color', 'black').title()}\n\n"
        "Now, send me an image for the middle logo (optional), or send /skip.",
        reply_markup=INLINE_BACK_KEYBOARD 
    )
    
    return GET_LOGO

async def get_logo_and_prompt_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the logo (from photo or document) and moves to the final text state, rejecting photo albums."""
    
    if update.effective_message.media_group_id:
        await update.message.reply_text("Please send only one image for the logo at a time.", reply_markup=INLINE_BACK_KEYBOARD)
        return GET_LOGO

    file_id = None
    if update.message.photo:
        file_id = update.message.photo[-1]
    elif update.message.document:
        if update.message.document.mime_type in ("image/jpeg", "image/png"):
             file_id = update.message.document
        else:
             await update.message.reply_text("Invalid file type. Please send a photo or a valid PNG/JPEG file.", reply_markup=INLINE_BACK_KEYBOARD)
             return GET_LOGO
    
    if not file_id:
        await update.message.reply_text("Invalid image input. Please send a photo or a valid PNG/JPEG file.", reply_markup=INLINE_BACK_KEYBOARD)
        return GET_LOGO

    photo_file = await file_id.get_file()
    logo_bytes = await photo_file.download_as_bytearray()
    
    context.user_data['logo'] = bytes(logo_bytes)
    logger.info(f"User {update.effective_user.id} uploaded a single logo.")
    
    context.user_data['current_state'] = GET_TEXT
    
    await update.message.reply_text(
        "Logo received. Now, send me the final text or link you want to encode.",
        reply_markup=INLINE_BACK_KEYBOARD
    )
    return GET_TEXT

async def skip_logo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the logo step and moves to the final text state."""
    context.user_data['logo'] = None
    logger.info(f"User {update.effective_user.id} skipped logo.")

    context.user_data['current_state'] = GET_TEXT
    
    await update.message.reply_text(
        "No logo. Now, send me the final text or link you want to encode.",
        reply_markup=INLINE_BACK_KEYBOARD
    )
    return GET_TEXT

async def get_text_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the final text, generates the QR, and ends."""
        
    final_text = update.message.text
    context.user_data['text'] = final_text
    
    await update.message.reply_text("Working on your final QR code...", reply_markup=ReplyKeyboardRemove())

    try:
        data = context.user_data['text']
        color = context.user_data.get('color', 'black')
        logo = context.user_data.get('logo')

        final_qr_buffer = create_custom_qr(data=data, fill_color=color, logo_bytes=logo)
        
        await update.message.reply_photo(
            photo=final_qr_buffer,
            caption=f"Here is your {color.title()} QR code for:\n» {data}"
        )
        
        await update.message.reply_text(
            "QR Code Complete! Press 'Start New QR' to begin again.", 
            reply_markup=PERSISTENT_REPLY_MARKUP
        )
        
    except Exception as e:
        logger.error(f"Failed to create final QR: {e}")
        await update.message.reply_text(
            "Sorry, an internal error occurred while generating the QR. Please try again.",
            reply_markup=PERSISTENT_REPLY_MARKUP
        )
    
    finally:
        context.user_data.pop('active_qr_session', None) 
        context.user_data.clear()
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation, showing the restart button."""
    logger.info(f"User {update.effective_user.id} canceled the conversation.")
    await update.message.reply_text(
        "Custom QR creation canceled.", 
        reply_markup=PERSISTENT_REPLY_MARKUP
    )
    context.user_data.pop('active_qr_session', None)
    context.user_data.clear()
    return ConversationHandler.END

# --- Wrong Input and Restart Handlers ---

async def handle_photo_when_text_expected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles photos received when the bot expects the final text."""
    logger.warning("Unexpected photo received in GET_TEXT state. Ignoring.")
    return GET_TEXT

async def handle_wrong_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unexpected input at any stage."""
        
    current_state = context.user_data.get('current_state')
    input_text = update.message.text.lower() if update.message.text else ''

    if current_state == GET_COLOR:
        if update.message.photo or (update.message.document and update.message.document.mime_type in ("image/jpeg", "image/png")):
            await update.message.reply_text("You must choose a color first before sending the logo photo.")
            return GET_COLOR
        
        await update.message.reply_text("I was expecting a valid color selection. Please choose one of the available options.")
        return GET_COLOR
        
    elif current_state == GET_LOGO:
        
        # Manually catch /skip text and process it if the CommandHandler fails to execute
        if update.message.text and update.message.text.lower() == '/skip':
            logger.warning("/skip command bypassed CommandHandler. Running manually.")
            return await skip_logo(update, context)

        if input_text and input_text in VALID_COLORS:
            logger.info(f"User {update.effective_user.id} re-selected color from GET_LOGO state.")
            return await get_color(update, context) 
        
        await update.message.reply_text("I was expecting a photo/image file for the logo or the command /skip. Please send the correct input.")
        return GET_LOGO
        
    elif current_state == GET_TEXT:
        await update.message.reply_text("I was expecting the final text or link to encode. Please send that now.")
        return GET_TEXT
        
    else:
        await update.message.reply_text("Unrecognized input. Please /start again or choose an option.", reply_markup=PERSISTENT_REPLY_MARKUP)
        context.user_data.pop('active_qr_session', None)
        return ConversationHandler.END

async def handle_new_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the 'Start New QR' button press (via inline callback) 
    by instructing the bot to execute the /start command.
    """
    query = update.callback_query
    await query.answer() # Acknowledge the press

    # 1. Edit the message to clear the button and show "Resetting"
    await query.edit_message_text("Resetting flow...", reply_markup=None)
    
    # 2. Instruct the bot to send the /start command to the user's chat.
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="/start"
    )
    
    # 3. Terminate this specific handler's execution.
    return ConversationHandler.END

async def handle_restart_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the prompt ONLY when the bot is not in an active session."""
    
    if context.user_data.get('active_qr_session'):
        return

    if update.message.text and (update.message.text.lower().startswith('/') or update.message.text.lower() == RESTART_BUTTON_TEXT.lower()):
        return
        

    await update.message.reply_text("Do you want to create another QR code? Please press the 'Start New QR' button below.")

