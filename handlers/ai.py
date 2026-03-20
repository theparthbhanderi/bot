"""
AI Handler for Telegram Super Bot
Handles AI chat interactions with memory and premium features.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from services.llm_service import generate_ai_response
from services.memory import add_user_message, add_bot_message, get_memory_context
from database import db


# Get premium daily limit from environment
DAILY_LIMIT = int(os.getenv('PREMIUM_DAILY_LIMIT', '10'))


async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle AI chat messages.
    Checks premium status and daily limit before processing.
    """
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Check daily limit
    if not db.check_daily_limit(user_id, DAILY_LIMIT):
        usage = db.get_daily_usage(user_id)
        await update.message.reply_text(
            f"⚠️ Daily limit reached! You've used {usage['daily_queries']}/{DAILY_LIMIT} free queries today.\n\n"
            f"Upgrade to premium for unlimited access!",
            reply_markup=None
        )
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
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
        
        # Save to memory
        add_user_message(user_id, user_message)
        add_bot_message(user_id, response)
        
        # Increment usage
        db.increment_daily_usage(user_id)
        
        # Show remaining limits
        usage = db.get_daily_usage(user_id)
        remaining = DAILY_LIMIT - usage['daily_queries']
        
        # Send response
        await update.message.reply_text(
            f"{response}\n\n"
            f"📊 Daily limit: {remaining}/{DAILY_LIMIT} remaining",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def clear_memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clear user's conversation memory.
    """
    user_id = update.effective_user.id
    from services.memory import clear_user_memory
    clear_user_memory(user_id)
    await update.message.reply_text("✅ Conversation memory cleared!")


async def usage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show user's usage statistics.
    """
    user_id = update.effective_user.id
    usage = db.get_daily_usage(user_id)
    
    remaining = DAILY_LIMIT - usage['daily_queries'] if not usage['is_premium'] else "∞"
    
    await update.message.reply_text(
        f"📊 <b>Usage Statistics</b>\n\n"
        f"• Daily queries: {usage['daily_queries']}/{DAILY_LIMIT}\n"
        f"• Remaining: {remaining}\n"
        f"• Total queries: {usage['total_queries']}\n"
        f"• Premium: {'✅ Yes' if usage['is_premium'] else '❌ No'}",
        parse_mode="HTML"
    )
