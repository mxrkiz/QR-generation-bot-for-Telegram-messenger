from telegram.ext import filters
from telegram import Update

# --- Custom Filter Class Implementation ---
class ImageDocumentFilter(filters.BaseFilter):
    """Custom filter to match documents that are JPEG or PNG images."""
    def __call__(self, update: Update) -> bool:
        if not update.message or not update.message.document:
            return False
        # Check if the document is a JPEG or PNG file
        return update.message.document.mime_type in ("image/jpeg", "image/png")

# Define the final filter instance to be imported
IMAGE_FILE_FILTER = filters.PHOTO | ImageDocumentFilter()