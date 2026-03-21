import logging
from telegram import Update
from telegram.ext import ContextTypes

from services.image_service import generate_image
from services.utils import FOOTER

logger = logging.getLogger(__name__)

async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /image command to generate text-to-image."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ <b>Please provide a prompt.</b>\n\n"
            "Example: <code>/image A futuristic city at night</code>",
            parse_mode="HTML"
        )
        return
        
    prompt = " ".join(context.args)
    
    if len(prompt) > 1000: # Limit length
        await update.message.reply_text(
            "⚠️ <b>Prompt too long!</b>\n"
            "Please keep it under 1000 characters.",
            parse_mode="HTML"
        )
        return
        
    loading_msg = await update.message.reply_text("🎨 <b>Generating image...</b>\n\n<i>This may take a few moments.</i>", parse_mode="HTML")
    
    try:
        image_bytes = await generate_image(prompt)
        
        caption = (
            f"🎨 <b>Generated Image</b>\n\n"
            f"<b>Prompt:</b> {prompt}\n"
            f"{FOOTER}"
        )
        
        await update.message.reply_photo(
            photo=image_bytes,
            caption=caption,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in image handler: {e}")
        await update.message.reply_text(
            f"❌ <b>Error generating image:</b>\n{str(e)}",
            parse_mode="HTML"
        )
    finally:
        # Delete loading message
        try:
            await loading_msg.delete()
        except Exception as e:
            logger.warning(f"Failed to delete loading message: {e}")
