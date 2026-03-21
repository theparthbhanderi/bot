import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from services.image_service import generate_image, enhance_image_prompt, upscale_image
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
        
    # Extract user negative prompt if provided using "--no"
    negative_prompt = None
    if "--no" in prompt:
        parts = prompt.split("--no", 1)
        prompt = parts[0].strip()
        negative_prompt = parts[1].strip()
        
    loading_msg = await update.message.reply_text("✨ <b>Enhancing prompt & generating image...</b>\n\n<i>This may take a few moments.</i>", parse_mode="HTML")
    
    try:
        # 1. Execute Ultra-Advanced Enhancer (handles styles + negatives + enhancements internally via JSON)
        prompt_data = await enhance_image_prompt(prompt, user_negative=negative_prompt)
        
        final_desc = prompt_data["enhanced_prompt"]
        final_neg = prompt_data["negative_prompt"]
        detected_style = prompt_data["style"]
        
        # Format payload for SD API
        api_payload = f"{final_desc} | negative: {final_neg}"
        
        # 2. Generate Image
        image_bytes = await generate_image(api_payload)
        
        caption = (
            f"🎨 <b>Generated Image</b>\n\n"
            f"<b>Prompt:</b> {final_desc}\n"
            f"<b>Style:</b> {str(detected_style).title()}\n"
        )
        if final_neg:
            caption += f"<b>Avoided:</b> {final_neg}\n"
        caption += f"\n{FOOTER}"
        
        keyboard = [[InlineKeyboardButton("🔍 Upscale (HD)", callback_data="action_upscale")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=image_bytes,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_markup
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

async def upscale_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the Upscale inline button."""
    query = update.callback_query
    await query.answer("🔍 Upscaling image to 4K...", show_alert=False)
    
    progress_msg = await query.message.reply_text("✨ <b>Upscaling to 4K HD...</b>", parse_mode="HTML")
    
    try:
        # 1. Get original image bytes
        photo_file = await query.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # 2. Upscale
        upscaled_bytes = await upscale_image(bytes(image_bytes))
        
        # 3. Maintain original prompt (keeps original caption)
        new_caption = query.message.caption_html + "\n\n✨ <i>Upscaled to 4K HD</i>"
        
        # 4. Replace image natively format
        await query.edit_message_media(
            media=InputMediaPhoto(media=upscaled_bytes, caption=new_caption, parse_mode="HTML")
        )
    except Exception as e:
        logger.error(f"Upscaling failed: {e}")
        await query.message.reply_text(f"❌ <b>Upscale failed:</b> {e}", parse_mode="HTML")
    finally:
        try:
            await progress_msg.delete()
        except:
            pass
