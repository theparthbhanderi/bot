"""
Ask Handler for KINGPARTH Bot
Handles RAG (Retrieval-Augmented Generation) question answering.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from services.llm_service import answer_question
from services.vector_db import add_to_knowledge, search_knowledge
from services.utils import clean_response, md_to_html, format_premium_response, FOOTER
from database import db


async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answer questions using RAG (knowledge base + AI)."""
    if not context.args:
        text = format_premium_response(
            title="Ask Anything",
            short="Search your personal Knowledge Base using AI.",
            points=[
                "Usage: /ask [question]",
                "Uses RAG for accurate answers",
                "Fallback to global AI knowledge"
            ],
            tip="First, add information using /addkb"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    question = ' '.join(context.args)
    user_id = update.effective_user.id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        context_text = search_knowledge(user_id, question)
        answer = answer_question(question, context_text) if context_text else answer_question(question)
        
        # answer_question uses chat_completion which will now return structured response 
        # because of updated PREMIUM_PROMPT
        formatted_answer = md_to_html(clean_response(answer))
        
        await update.message.reply_text(
            formatted_answer + FOOTER,
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def add_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add content to user's knowledge base."""
    if not context.args:
        if update.message.reply_to_message:
            content = update.message.reply_to_message.text
        else:
            text = format_premium_response(
                title="Add Knowledge",
                short="Save information to your personal AI memory.",
                points=[
                    "Usage: /addkb [content]",
                    "Or reply to any message with /addkb",
                    "Stored for RAG semantic search"
                ]
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return
    else:
        content = ' '.join(context.args)

    user_id = update.effective_user.id

    try:
        title = content[:50] + "..." if len(content) > 50 else content
        add_to_knowledge(user_id, title, content)
        db.add_to_knowledge_base(user_id, title, content)

        text = format_premium_response(
            title="Saved Successfully",
            short=f"I've added \"{title}\" to your knowledge base.",
            tip="You can now ask questions about this using /ask"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def my_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List user's knowledge base contents."""
    user_id = update.effective_user.id

    try:
        kb_entries = db.get_knowledge_base(user_id)

        if not kb_entries:
            await update.message.reply_text(
                "📚 <b>Your Knowledge Base</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📭 <i>Empty — no content saved yet.</i>\n\n"
                "Use /addkb to add your first item!",
                parse_mode="HTML"
            )
            return

        response = (
            "📚 <b>Your Knowledge Base</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for i, entry in enumerate(kb_entries[:10], 1):
            title = entry['title'][:40] + "..." if len(entry['title']) > 40 else entry['title']
            response += f"{i}. {title}\n"

        if len(kb_entries) > 10:
            response += f"\n<i>... and {len(kb_entries) - 10} more entries</i>"

        response += f"\n\n📊 <b>Total:</b> {len(kb_entries)} items"

        await update.message.reply_text(response, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def clear_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear user's knowledge base."""
    await update.message.reply_text(
        "⚠️ <b>Clear Knowledge Base?</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "This will <b>permanently delete</b> all your saved knowledge.\n\n"
        "Reply with /confirmclear to confirm.",
        parse_mode="HTML"
    )


async def confirm_clear_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm clearing knowledge base."""
    user_id = update.effective_user.id

    try:
        from services.vector_db import get_vector_store
        store = get_vector_store()
        store.clear()

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM knowledge_base WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            "✅ <b>Knowledge Base Cleared!</b>\n\n"
            "All saved content has been removed.\n"
            "Start fresh with /addkb ✨",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def search_knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search within knowledge base."""
    if not context.args:
        await update.message.reply_text(
            "🔍 <b>Search Knowledge Base</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /searchkb [query]",
            parse_mode="HTML"
        )
        return

    query = ' '.join(context.args)
    user_id = update.effective_user.id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        context_text = search_knowledge(user_id, query)

        if context_text:
            await update.message.reply_text(
                f"🔍 <b>Search Results:</b> {query}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<code>{escape_html(context_text[:500])}</code>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"🔍 <b>No results</b> found for: <i>{query}</i>",
                parse_mode="HTML"
            )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
