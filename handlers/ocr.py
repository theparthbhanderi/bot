"""
OCR Handler for KINGPARTH Bot
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
    """Handle OCR requests. User sends an image and the bot extracts text."""
    if not update.message.photo:
        await update.message.reply_text(
            "📷 <b>OCR — Image to Text</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Send me an image and I'll extract text from it!\n\n"
            "✅ <b>Supported:</b> JPEG, PNG, GIF, BMP, WebP",
            parse_mode="HTML"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if not GOOGLE_CLOUD_VISION_API_KEY:
            await update.message.reply_text(
                "⚠️ <b>Not Configured</b>\n\n"
                "Set <code>GOOGLE_CLOUD_VISION_API_KEY</code> in your environment.",
                parse_mode="HTML"
            )
            return

        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()

        import aiohttp
        import base64
        image_content = base64.b64encode(bytes(photo_bytes)).decode('utf-8')

        api_url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"

        payload = {
            "requests": [{
                "image": {"content": image_content},
                "features": [{"type": "TEXT_DETECTION"}]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as resp:
                data = await resp.json()

        if 'responses' in data and data['responses']:
            text = data['responses'][0].get('text', '')

            if text:
                if len(text) > 4000:
                    text = truncate_text(text, 3900)
                    text += "\n\n<i>(Truncated — text too long)</i>"

                await update.message.reply_text(
                    f"📷 <b>Extracted Text</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{text}",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    "🔍 <b>No text detected</b> in this image.",
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                "⚠️ Could not process the image. Try a clearer image.",
                parse_mode="HTML"
            )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def ocr_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OCR from image URL."""
    if not context.args:
        await update.message.reply_text(
            "📷 <b>OCR from URL</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /ocrurl [image_url]\n\n"
            "💡 <b>Example:</b>\n"
            "<code>/ocrurl https://example.com/image.png</code>",
            parse_mode="HTML"
        )
        return

    image_url = context.args[0]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if not GOOGLE_CLOUD_VISION_API_KEY:
            await update.message.reply_text(
                "⚠️ <b>Not Configured</b>\n\n"
                "Set <code>GOOGLE_CLOUD_VISION_API_KEY</code> in your environment.",
                parse_mode="HTML"
            )
            return

        import aiohttp
        import base64

        async with aiohttp.ClientSession() as session:
            # Download image
            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                image_content = await resp.read()

            image_b64 = base64.b64encode(image_content).decode('utf-8')

            api_url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"

            payload = {
                "requests": [{
                    "image": {"content": image_b64},
                    "features": [{"type": "TEXT_DETECTION"}]
                }]
            }

            async with session.post(api_url, json=payload) as api_resp:
                data = await api_resp.json()

        if 'responses' in data and data['responses']:
            text = data['responses'][0].get('text', '')

            if text:
                if len(text) > 4000:
                    text = truncate_text(text, 3900)
                    text += "\n\n<i>(Truncated)</i>"

                await update.message.reply_text(
                    f"📷 <b>Extracted Text</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{text}",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    "🔍 <b>No text detected</b> in this image.",
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                "⚠️ Could not process the image.",
                parse_mode="HTML"
            )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )
