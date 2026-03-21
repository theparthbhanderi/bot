import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from services.image_service import generate_image, enhance_image_prompt, upscale_image, generate_multi_model_images
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
        
        final_desc = prompt_data.get("enhanced_prompt", prompt)
        final_neg = prompt_data.get("negative_prompt", "")
        detected_style = prompt_data.get("style", "cinematic")
        composition = prompt_data.get("composition", "")
        lighting = prompt_data.get("lighting", "")
        
        # Format payload for API
        api_payload = f"{final_desc} | negative: {final_neg}"
        
        # 2. Parallel Multi-Model Generation
        results = await generate_multi_model_images(api_payload)
        
        if not results:
            raise Exception("All OpenRouter pipelines timed out or failed.")
            
        media_group = []
        best_image_bytes = None
        
        for i, res in enumerate(results):
            score = res.get("score", 0.0)
            is_best = (i == 0) # Already sorted highest to lowest natively!
            
            if is_best:
                best_image_bytes = res["image"]
                star = " ⭐ (Best Model)"
            else:
                star = ""
                
            caption = (
                f"🎨 <b>Model:</b> {res['model']}{star}\n"
                f"⚡ <b>Style:</b> {str(detected_style).title()}\n"
                f"📈 <b>Quality Score:</b> {score:.1f}"
            )
            media_group.append(InputMediaPhoto(media=res['image'], caption=caption, parse_mode="HTML"))
            
        # Broadcast all dynamically
        await update.message.reply_media_group(media=media_group)
        
        # Deploy context engine keyboard immediately trailing the album
        keyboard = [
            [InlineKeyboardButton("🔁 Regenerate All", callback_data="action_regenerate_all"),
             InlineKeyboardButton("🎯 Best Only (Upscale)", callback_data="action_upscale")]
        ]
        
        # Store context in memory to safely upscale
        context.user_data["cached_upscale_target"] = best_image_bytes
        
        await update.message.reply_text(
            f"<b>Prompt:</b> {final_desc}\n\n<i>Select an action:</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
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
    """Handles the Upscale inline button, natively supporting Text UI tracking over Albums."""
    query = update.callback_query
    await query.answer("🔍 Sending image for 4K HD upscaling...", show_alert=False)
    
    progress_msg = await query.message.reply_text("✨ <b>Upscaling image to 4K resolution...</b>\n\n<i>This may take a moment.</i>", parse_mode="HTML")
    
    try:
        # Dynamically load cached target buffer
        image_bytes = context.user_data.get("cached_upscale_target")
        caption_html = query.message.caption_html or query.message.text_html
        
        if not image_bytes:
            # Fallback for standard single-photo messages
            if query.message.photo:
                photo = query.message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                image_bytes = bytes(await file.download_as_bytearray())
            else:
                raise Exception("No image binary cached in memory to upscale.")
                
        # 1. Call upscale API
        upscaled_bytes = await upscale_image(image_bytes)
        
        # Append identifier
        new_caption = caption_html + "\n\n✨ <i>Upscaled to 4K HD</i>"
        
        # 2. Safely output media (In-place edit if possible, otherwise standard reply)
        if query.message.photo:
            await query.edit_message_media(
                media=InputMediaPhoto(media=upscaled_bytes, caption=new_caption, parse_mode="HTML"),
                reply_markup=query.message.reply_markup
            )
        else:
            await query.message.reply_photo(
                photo=upscaled_bytes, 
                caption=new_caption, 
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Upscale failed: {e}")
        await query.message.reply_text(f"❌ <b>Upscaling failed:</b> {e}", parse_mode="HTML")
    finally:
        try:
            await progress_msg.delete()
        except:
            pass

async def regenerate_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hits OpenRouter parallel models array on demand."""
    query = update.callback_query
    await query.answer("🔁 Regenerating all parallel models...", show_alert=False)
    
    progress_msg = await query.message.reply_text("✨ <b>Generating new parallel images...</b>", parse_mode="HTML")
    
    try:
        caption_html = query.message.text_html
        import re
        base_prompt = ""
        match = re.search(r'<b>Prompt:</b> (.*?)\n', caption_html)
        if match:
            base_prompt = match.group(1).strip()
        else:
            base_prompt = "cinematic highly detailed portrait"
            
        results = await generate_multi_model_images(base_prompt)
        
        if not results:
            raise Exception("All OpenRouter pipelines timed out or failed.")
            
        media_group = []
        best_image_bytes = None
        
        for i, res in enumerate(results):
            score = res.get("score", 0.0)
            is_best = (i == 0)
            if is_best:
                best_image_bytes = res["image"]
                star = " ⭐ (Best Model)"
            else:
                star = ""
                
            caption = (
                f"🎨 <b>Model:</b> {res['model']}{star}\n"
                f"📈 <b>Quality Score:</b> {score:.1f}"
            )
            media_group.append(InputMediaPhoto(media=res['image'], caption=caption, parse_mode="HTML"))
            
        await query.message.reply_media_group(media=media_group)
        context.user_data["cached_upscale_target"] = best_image_bytes
        
    except Exception as e:
        logger.error(f"Regenerate failed: {e}")
        await query.message.reply_text(f"❌ <b>Regenerate failed:</b> {e}", parse_mode="HTML")
    finally:
        try:
            await progress_msg.delete()
        except:
            pass
