"""
Ask Handler for KINGPARTHH Bot
Handles RAG (Retrieval-Augmented Generation) question answering.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from services.llm_service import answer_question
from services.vector_db import add_to_knowledge, search_knowledge
from database import db


async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Answer questions using RAG (knowledge base + AI).
    Usage: /ask <question>
    """
    if not context.args:
        await update.message.reply_text(
            "🤔 <b>Ask (RAG)</b>\n\n"
            "Usage: /ask <question>\n\n"
            "I'll search your knowledge base and answer your question.\n\n"
            "First, add content with /addkb",
            parse_mode="HTML"
        )
        return
    
    question = ' '.join(context.args)
    user_id = update.effective_user.id
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Search knowledge base
        context_text = search_knowledge(user_id, question)
        
        # Generate answer
        if context_text:
            answer = answer_question(question, context_text)
            source = "📚 Knowledge Base"
        else:
            # Fallback to general AI
            answer = answer_question(question)
            source = "🤖 AI"
        
        await update.message.reply_text(
            f"🤔 <b>Question:</b> {question}\n\n"
            f"<b>Answer:</b> {answer}\n\n"
            f"<i>Source: {source}</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def add_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add content to user's knowledge base.
    Usage: /addkb <content> or reply with content
    """
    if not context.args:
        if update.message.reply_to_message:
            content = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "📚 <b>Add to Knowledge Base</b>\n\n"
                "Usage: /addkb <content>\n\n"
                "Or reply to a message with /addkb\n\n"
                "I'll remember this information for future questions.",
                parse_mode="HTML"
            )
            return
    else:
        content = ' '.join(context.args)
    
    user_id = update.effective_user.id
    
    try:
        # Add to vector database
        title = content[:50] + "..." if len(content) > 50 else content
        add_to_knowledge(user_id, title, content)
        
        # Also add to SQLite for backup
        db.add_to_knowledge_base(user_id, title, content)
        
        await update.message.reply_text(
            "✅ <b>Added to Knowledge Base!</b>\n\n"
            f"<i>\"{title}\"</i>\n\n"
            "You can now ask me questions about this content using /ask",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def my_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    List user's knowledge base contents.
    Usage: /mykb
    """
    user_id = update.effective_user.id
    
    try:
        # Get knowledge base from SQLite
        kb_entries = db.get_knowledge_base(user_id)
        
        if not kb_entries:
            await update.message.reply_text(
                "📚 <b>Your Knowledge Base</b>\n\n"
                "You haven't added any content yet.\n\n"
                "Use /addkb to add content.",
                parse_mode="HTML"
            )
            return
        
        response = "📚 <b>Your Knowledge Base</b>\n\n"
        
        for i, entry in enumerate(kb_entries[:10], 1):
            title = entry['title'][:40] + "..." if len(entry['title']) > 40 else entry['title']
            response += f"{i}. {title}\n"
        
        if len(kb_entries) > 10:
            response += f"\n... and {len(kb_entries) - 10} more entries"
        
        await update.message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def clear_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clear user's knowledge base.
    Usage: /clearkb
    """
    user_id = update.effective_user.id
    
    # Confirm with user
    await update.message.reply_text(
        "⚠️ <b>Clear Knowledge Base?</b>\n\n"
        "This will delete all your saved knowledge.\n\n"
        "Reply with /confirmclear to confirm.",
        parse_mode="HTML"
    )


async def confirm_clear_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Confirm clearing knowledge base.
    """
    user_id = update.effective_user.id
    
    try:
        # Clear from vector store
        from services.vector_db import get_vector_store
        store = get_vector_store()
        store.clear()
        
        # Clear from SQLite
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM knowledge_base WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            "✅ <b>Knowledge Base Cleared!</b>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def search_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Search within knowledge base.
    Usage: /searchkb <query>
    """
    if not context.args:
        await update.message.reply_text(
            "🔍 <b>Search Knowledge Base</b>\n\n"
            "Usage: /searchkb <query>",
            parse_mode="HTML"
        )
        return
    
    query = ' '.join(context.args)
    user_id = update.effective_user.id
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Search vector store
        context_text = search_knowledge(user_id, query)
        
        if context_text:
            await update.message.reply_text(
                f"🔍 <b>Search Results:</b> {query}\n\n"
                f"<code>{escape_html(context_text[:500])}</code>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"🔍 No results found for: {query}",
                parse_mode="HTML"
            )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
