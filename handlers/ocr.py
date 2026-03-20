"""
OCR Handler for Telegram Super Bot
Handles OCR (Optical Character Recognition) using Google Cloud Vision API.
"""

import os
import io
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import truncate_text


# Google Cloud Vision API configuration
GOOGLE_CLOUD_VISION_API_KEY = os.getenv('GOOGLE_CLOUD_VISION_API_KEY', '')


async def ocr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle OCR requests.
    User sends an image and the bot extracts text from it.
    """
    # Check for photo
    if not update.message.photo:
        await update.message.reply_text(
            "📷 <b>OCR - Image to Text</b>\n\n"
            "Please send me an image and I'll extract the text from it!\n\n"
            "Supported formats: JPEG, PNG, GIF, BMP, WebP",
            parse_mode="HTML"
        )
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Check if API key is configured
        if not GOOGLE_CLOUD_VISION_API_KEY:
            await update.message.reply_text(
                "⚠️ OCR API is not configured.\n"
                "Please set GOOGLE_CLOUD_VISION_API_KEY in your environment."
            )
            return
        
        # Get the photo
        photo = update.message.photo[-1]  # Get highest resolution
        
        # Download the photo
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Process with Google Cloud Vision API
        import requests
        
        api_url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"
        
        # Convert to base64
        import base64
        image_content = base64.b64encode(bytes(photo_bytes)).decode('utf-8')
        
        payload = {
            "requests": [{
                "image": {"content": image_content},
                "features": [{"type": "TEXT_DETECTION"}]
            }]
        }
        
        response = requests.post(api_url, json=payload)
        data = response.json()
        
        if 'responses' in data and data['responses']:
            text = data['responses'][0].get('text', '')
            
            if text:
                # Truncate if too long
                if len(text) > 4000:
                    text = truncate_text(text, 3900)
                    text += "\n\n<i>(Text truncated - too long to display)</i>"
                
                await update.message.reply_text(
                    f"📷 <b>Extracted Text:</b>\n\n{text}",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    "🔍 No text detected in the image."
                )
        else:
            await update.message.reply_text(
                "🔍 Could not process the image."
            )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def ocr_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle OCR from image URL.
    Usage: /ocrurl <image_url>
    """
    if not context.args:
        await update.message.reply_text(
            "📷 <b>OCR from URL</b>\n\n"
            "Usage: /ocrurl <image_url>\n\n"
            "Example: /ocrurl https://example.com/image.png",
            parse_mode="HTML"
        )
        return
    
    image_url = context.args[0]
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Check if API key is configured
        if not GOOGLE_CLOUD_VISION_API_KEY:
            await update.message.reply_text(
                "⚠️ OCR API is not configured.\n"
                "Please set GOOGLE_CLOUD_VISION_API_KEY in your environment."
            )
            return
        
        # Download image
        import requests
        response = requests.get(image_url, timeout=30)
        image_content = response.content
        
        # Process with Google Cloud Vision API
        import base64
        image_b64 = base64.b64encode(image_content).decode('utf-8')
        
        api_url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"
        
        payload = {
            "requests": [{
                "image": {"content": image_b64},
                "features": [{"type": "TEXT_DETECTION"}]
            }]
        }
        
        api_response = requests.post(api_url, json=payload)
        data = api_response.json()
        
        if 'responses' in data and data['responses']:
            text = data['responses'][0].get('text', '')
            
            if text:
                if len(text) > 4000:
                    text = truncate_text(text, 3900)
                    text += "\n\n<i>(Text truncated)</i>"
                
                await update.message.reply_text(
                    f"📷 <b>Extracted Text:</b>\n\n{text}",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    "🔍 No text detected in the image."
                )
        else:
            await update.message.reply_text(
                "🔍 Could not process the image."
            )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
