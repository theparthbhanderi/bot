"""
AI Handler for KINGPARTH Bot
Handles AI chat interactions with memory and premium features.
"""

import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.llm_service import generate_ai_response
from services.memory import add_user_message, add_bot_message, get_memory_context
from services.utils import clean_response, md_to_html, truncate_text, FOOTER
from database import db


# Get premium daily limit from environment
DAILY_LIMIT = int(os.getenv('PREMIUM_DAILY_LIMIT', '10'))


async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle AI chat messages with premium UX.
    Shows "Thinking..." then edits with final answer + quick action buttons.
    """
    user_id = update.effective_user.id
    user_message = update.message.text

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Send "Thinking..." loading message
    thinking_msg = await update.message.reply_text(
        "⚡ <b>Thinking...</b>",
        parse_mode="HTML"
    )

    # Get conversation memory
    memory_context = get_memory_context(user_id)

    # Get user's knowledge base context (RAG)
    from services.vector_db import search_knowledge
    knowledge_context = search_knowledge(user_id, user_message)

    # Generate AI response
    try:
        response = generate_ai_response(
            user_message=user_message,
            conversation_history=db.get_conversation_history(user_id),
            use_rag=bool(knowledge_context),
            knowledge_context=knowledge_context
        )

        # Clean + convert markdown to HTML
        response = clean_response(response)
        response = md_to_html(response)
        response = truncate_text(response, 3800)

        # Add footer
        response += FOOTER

        # Save to memory
        add_user_message(user_id, user_message)
        add_bot_message(user_id, response)

        # Increment usage
        db.increment_daily_usage(user_id)

        # Quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔁 Simplify", callback_data="action_simplify"),
                InlineKeyboardButton("🌐 Translate", callback_data="action_translate"),
            ],
            [
                InlineKeyboardButton("📋 Expand", callback_data="action_expand"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Edit the "Thinking..." message with the actual response
        await thinking_msg.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=reply_markup
        )

    except Exception as e:
        await thinking_msg.edit_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def clear_memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear user's conversation memory."""
    user_id = update.effective_user.id
    from services.memory import clear_user_memory
    clear_user_memory(user_id)
    await update.message.reply_text(
        "🗑️ <b>Memory Cleared!</b>\n\n"
        "Your conversation history has been reset.\n"
        "You're ready for a fresh start! ✨"
        + FOOTER,
        parse_mode="HTML"
    )


async def usage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's usage statistics."""
    user_id = update.effective_user.id
    usage = db.get_daily_usage(user_id)

    remaining = DAILY_LIMIT - usage['daily_queries'] if not usage['is_premium'] else "∞"
    premium_badge = "💎 Premium" if usage['is_premium'] else "🆓 Free"

    await update.message.reply_text(
        f"📊 <b>Your Usage Stats</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ <b>Plan:</b> {premium_badge}\n"
        f"📈 <b>Today:</b> {usage['daily_queries']}/{DAILY_LIMIT} queries\n"
        f"⏳ <b>Remaining:</b> {remaining}\n"
        f"📊 <b>Total:</b> {usage['total_queries']} all-time queries"
        + FOOTER,
        parse_mode="HTML"
    )
