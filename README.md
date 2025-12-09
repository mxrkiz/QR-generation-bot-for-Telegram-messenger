# QR generation bot for Telegram messenger
Telegram bot built on Python that allows users to generate QR codes with multiple design options.

# Required libraries

```
python-telegram-bot #Foundational framework
qrcode #QR code generating engine
Pillow #Image processing and logo embedding
numpy #Mathematical operations for fast image processing via Pillow
```

This bot was developed for a semestral project at BUT (Brno University of Technology) as part of my programming course.
## Features
**Custom Color Selection:** Users can select from a predefined color palette.
<img width="1730" height="583" alt="image" src="https://github.com/user-attachments/assets/616987f1-8439-4e1c-a6ad-6671f53263c6" />
```
### handlers.py

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
```
**Logo Embedding:** Supports uploading a custom image to be placed in the center of the QR code.
<img width="1573" height="838" alt="image" src="https://github.com/user-attachments/assets/5f722366-af82-48be-b2c2-d2a807cff1f0" />

```
### handlers.py

def create_custom_qr(data: str, fill_color: str = 'black', logo_bytes: bytes | None = None):
    # ... setup qr code object ...
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H, 
        box_size=10, 
        border=3,    
    )
    qr.add_data(data)
    qr.make(fit=True) 

    img = qr.make_image(fill_color=hex_code, back_color="white").convert("RGB") 

    if logo_bytes:
        try:
            logo_pil = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            img_size = img.size[0]
            # Resize logo to 1/4th size (standard for robustness)
            logo_max_size = img_size // 4
            logo_pil.thumbnail((logo_max_size, logo_max_size))
            
            logo_pos = ((img_size - logo_pil.width) // 2, (img_size - logo_pil.height) // 2)
            # Paste the logo onto the center
            img.paste(logo_pil, logo_pos, mask=logo_pil)
        except Exception as e:
            logger.error(f"Failed to add logo to QR code: {e}")
    # ... return image buffer ...
```
**Robust Navigation:** Uses inline buttons for 'Go Back' functionality and clean flow management.
<img width="555" height="136" alt="image" src="https://github.com/user-attachments/assets/90541353-001f-4b66-94e0-a7037f97b348" />

<img width="555" height="178" alt="image" src="https://github.com/user-attachments/assets/5f35b590-334c-4a21-8815-2b4183b7a63f" />

```
### handlers.py

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Go Back' callback query."""
    
    query = update.callback_query
    await query.answer()

    current_state = context.user_data.get('current_state')

    if current_state == GET_LOGO:
        # Reverts to GET_COLOR
        context.user_data.pop('color', None)
        context.user_data['current_state'] = GET_COLOR
        
        await query.edit_message_text("You went back. Choose a color from the panel below.", reply_markup=None)
        await query.message.reply_text("Color menu:", reply_markup=COLOR_REPLY_MARKUP)
        return GET_COLOR
    
    elif current_state == GET_TEXT:
        # Reverts to GET_LOGO
        context.user_data.pop('logo', None)
        context.user_data['current_state'] = GET_LOGO
        
        await query.edit_message_text(
            f"You went back. Color is still: {context.user_data.get('color', 'black').title()}\n\n"
            "Now, send me an image for the middle logo (optional), or send /skip.",
            reply_markup=INLINE_BACK_KEYBOARD 
        )
        return GET_LOGO
    # ... (rest of logic)
```
**Error Handling:** Manages invalid input, multiple photo uploads, and conversation state errors.
<img width="1567" height="474" alt="image" src="https://github.com/user-attachments/assets/f1267026-edc4-4231-bfe1-1da7df0992d9" />

```
# filters.py

class ImageDocumentFilter(filters.BaseFilter):
    """Custom filter to match documents that are JPEG or PNG images."""
    def __call__(self, update: Update) -> bool:
        if not update.message or not update.message.document:
            return False
        # Checks the MIME type of the document
        return update.message.document.mime_type in ("image/jpeg", "image/png")

IMAGE_FILE_FILTER = filters.PHOTO | ImageDocumentFilter()
```
