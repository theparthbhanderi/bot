"""
AI Chat Handler for KINGPARTH Bot - ULTRA OPTIMIZED
Handles AI interactions with specular execution and background tasking.
"""

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.utils import clean_response, md_to_html, truncate_text, FOOTER, format_premium_response, get_translation_keyboard
from services.llm_service import generate_ai_response, async_translate_text
from database import db

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ULTRA-OPTIMIZED AI Chat Handler.
    - Speculative Execution
    - Background Tasking
    - Multi-layer caching
    - Translation Support
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_message = " ".join(context.args) if context.args else update.message.text
    
    if not user_message: return

    # 1. Instant Typing Action
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # 2. Context Preparedness
        from services.memory import get_memory_context
        history = get_memory_context(user_id)
        
        from services.vector_db import search_knowledge
        # RAG Search (Fast/Local)
        knowledge_context = search_knowledge(user_id, user_message)

        # 3. Speculative Response Generation (Async)
        response = await generate_ai_response(
            user_message=user_message,
            conversation_history=history,
            use_rag=bool(knowledge_context),
            knowledge_context=knowledge_context
        )

        # 4. Ultra-Fast Formatting
        formatted_response = md_to_html(clean_response(response))
        final_text = truncate_text(formatted_response, 4000) + FOOTER
        
        # Save for translation
        context.user_data["last_response"] = final_text

        # 5. Keyboard with Translation
        keyboard = [
            [
                InlineKeyboardButton("🔁 Simplify", callback_data="action_simplify"),
                InlineKeyboardButton("📖 Expand", callback_data="action_expand")
            ],
            [
                InlineKeyboardButton("🇮🇳 Hindi", callback_data="translate_hi"),
                InlineKeyboardButton("🇮🇳 Gujarati", callback_data="translate_gu"),
                InlineKeyboardButton("🇺🇸 English", callback_data="translate_en")
            ]
        ]
        
        # 6. Immediate Response
        await update.message.reply_text(
            final_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # 7. Background persistence (Non-blocking)
        asyncio.create_task(save_context_and_usage(user_id, user_message, response))

    except Exception as e:
        await update.message.reply_text(f"⚠️ <b>Error</b>\n\n{str(e)[:200]}", parse_mode="HTML")

async def translation_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles translation button clicks."""
    query = update.callback_query
    await query.answer("Translating... 🔄")
    
    lang_code = query.data.split('_')[1]
    target_lang = "Hindi" if lang_code == 'hi' else ("Gujarati" if lang_code == 'gu' else "English")
    
    original_text = context.user_data.get("last_response")
    if not original_text:
        await query.edit_message_text("⚠️ Original text not found. Please try again.", parse_mode="HTML")
        return

    # Use LLM for translation to keep HTML tags intact
    translated_text = await async_translate_text(original_text, target_lang)
    
    # Update keyboard (to keep functionality)
    keyboard = query.message.reply_markup.inline_keyboard
    
    await query.edit_message_text(
        truncate_text(translated_text, 4000),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def save_context_and_usage(user_id, user_message, response):
    """Internal helper to save data without blocking user UI."""
    from services.memory import add_user_message, add_bot_message
    add_user_message(user_id, user_message)
    add_bot_message(user_id, response)
    db.increment_daily_usage(user_id)


async def clear_memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from services.memory import clear_memory
    clear_memory(update.effective_user.id)
    text = format_premium_response(
        title="Memory Cleared",
        short="Your conversation history has been successfully reset.",
        tip="Send a new message to start a fresh chat!"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def usage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usage = db.get_daily_usage(user_id)
    text = format_premium_response(
        title="Daily Usage",
        short=f"You have used {usage} requests today.",
        points=[
            f"Daily Limit: {os.getenv('PREMIUM_DAILY_LIMIT', '10')}",
            f"Remaining: {max(0, int(os.getenv('PREMIUM_DAILY_LIMIT', '10')) - usage)}"
        ],
        tip="Premium users get unlimited access!"
    )
    await update.message.reply_text(text, parse_mode="HTML")
