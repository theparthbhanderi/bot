"""
AI Chat Handler for KINGPARTH Bot - OPTIMIZED
Handles AI interactions with history compression and caching.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.llm_service import generate_ai_response
from services.memory import get_memory_context, add_user_message, add_bot_message
from services.utils import clean_response, md_to_html, truncate_text, FOOTER
from database import db

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    OPTIMIZED AI Chat Handler.
    - Instant typing action
    - Compressed history (handled in service)
    - Result caching (handled in service)
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Get message text
    if context.args:
        user_message = " ".join(context.args)
    else:
        user_message = update.message.text

    if not user_message:
        await update.message.reply_text("Please provide a message for the AI.")
        return

    # 1. Instant Typing Feedback
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # 2. Get history
        history = get_memory_context(user_id)
        
        # 3. Get Knowledge Base context (RAG)
        from services.vector_db import search_knowledge
        knowledge_context = search_knowledge(user_id, user_message)

        # 4. Generate Optimized Response
        response = generate_ai_response(
            user_message=user_message,
            conversation_history=history,
            use_rag=bool(knowledge_context),
            knowledge_context=knowledge_context
        )

        # 5. Format response
        formatted_response = clean_response(response)
        formatted_response = md_to_html(formatted_response)

        # 6. Quick Action Buttons
        keyboard = [
            [
                InlineKeyboardButton("🔁 Simplify", callback_data="action_simplify"),
                InlineKeyboardButton("🌐 Translate", callback_data="action_translate"),
                InlineKeyboardButton("📖 Expand", callback_data="action_expand")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 7. Send Response
        await update.message.reply_text(
            truncate_text(formatted_response, 4000) + FOOTER,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        
        # 8. Save to Context & DB
        add_user_message(user_id, user_message)
        add_bot_message(user_id, response)
        db.increment_daily_usage(user_id)

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def clear_memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear user conversation memory."""
    user_id = update.effective_user.id
    from services.memory import clear_memory
    clear_memory(user_id)
    await update.message.reply_text("✨ <b>Memory cleared!</b>", parse_mode="HTML")


async def usage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current daily usage."""
    user_id = update.effective_user.id
    usage = db.get_daily_usage(user_id)
    limit = int(os.getenv('PREMIUM_DAILY_LIMIT', 50))
    
    await update.message.reply_text(
        f"📊 <b>Daily Usage</b>\n\n"
        f"Used: {usage}\n"
        f"Limit: {limit}\n"
        f"Remaining: {max(0, limit - usage)}"
        + FOOTER,
        parse_mode="HTML"
    )
