"""
AI Chat Handler for KINGPARTH Bot - ULTRA OPTIMIZED
Handles AI interactions with specular execution and background tasking.
"""

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.llm_service import generate_ai_response
from services.memory import get_memory_context, add_user_message, add_bot_message
from services.utils import clean_response, md_to_html, truncate_text, FOOTER
from database import db

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ULTRA-OPTIMIZED AI Chat Handler.
    - Speculative Execution
    - Background Tasking
    - Multi-layer caching
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_message = " ".join(context.args) if context.args else update.message.text
    
    if not user_message: return

    # 1. Instant Typing Action
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # 2. Context Preparedness
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
        formatted_response = clean_response(response)
        formatted_response = md_to_html(formatted_response)
        final_text = truncate_text(formatted_response, 4000) + FOOTER

        # 5. Quick Actions
        keyboard = [[
            InlineKeyboardButton("🔁 Simplify", callback_data="action_simplify"),
            InlineKeyboardButton("🌐 Translate", callback_data="action_translate"),
            InlineKeyboardButton("📖 Expand", callback_data="action_expand")
        ]]
        
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

async def save_context_and_usage(user_id, user_message, response):
    """Internal helper to save data without blocking user UI."""
    add_user_message(user_id, user_message)
    add_bot_message(user_id, response)
    db.increment_daily_usage(user_id)


async def clear_memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from services.memory import clear_memory
    clear_memory(update.effective_user.id)
    await update.message.reply_text("✨ <b>Memory cleared!</b>", parse_mode="HTML")

async def usage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usage = db.get_daily_usage(user_id)
    await update.message.reply_text(f"📊 <b>Usage:</b> {usage}", parse_mode="HTML")
