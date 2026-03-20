"""
Code Handler for KINGPARTHH Bot
Handles coding assistant features: explanations, reviews, and help.
"""

from telegram import Update
from telegram.ext import ContextTypes
from services.llm_service import (
    generate_code_explanation,
    generate_code_review,
    chat_completion
)
from services.utils import clean_response, md_to_html, truncate_text


async def code_explain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain code in plain language."""
    if not context.args:
        if update.message.reply_to_message:
            code = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "💻 <b>Code Explainer</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 <b>Usage:</b> /explain [code]\n\n"
                "Or reply to a code message with /explain",
                parse_mode="HTML"
            )
            return
    else:
        code = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        language = detect_language(code)
        explanation = generate_code_explanation(code, language)
        explanation = clean_response(explanation)
        explanation = md_to_html(explanation)

        await update.message.reply_text(
            f"💻 <b>Code Explanation</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔤 <b>Language:</b> {language.title()}\n\n"
            f"📖 <b>Explanation:</b>\n{truncate_text(explanation, 3800)}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def code_review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Review code for issues and improvements."""
    if not context.args:
        if update.message.reply_to_message:
            code = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🔍 <b>Code Review</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 <b>Usage:</b> /review [code]\n\n"
                "Or reply to a code message with /review",
                parse_mode="HTML"
            )
            return
    else:
        code = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        language = detect_language(code)
        review = generate_code_review(code, language)
        review = clean_response(review)
        review = md_to_html(review)

        await update.message.reply_text(
            f"🔍 <b>Code Review</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔤 <b>Language:</b> {language.title()}\n\n"
            f"📋 <b>Review:</b>\n{truncate_text(review, 3800)}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def code_generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate code based on description."""
    if not context.args:
        await update.message.reply_text(
            "✨ <b>Code Generator</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /code [description]\n\n"
            "💡 <b>Example:</b>\n"
            "<code>/code function to sort a list in python</code>",
            parse_mode="HTML"
        )
        return

    description = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        system_prompt = """You are a premium coding assistant. Generate clean, well-commented, production-quality code.
        Format the code properly. Add brief explanations after the code."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate code: {description}"}
        ]

        response = chat_completion(messages, max_tokens=1500)
        response = clean_response(response)
        response = md_to_html(response)

        await update.message.reply_text(
            f"✨ <b>Generated Code</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 <b>Request:</b> {description}\n\n"
            f"{truncate_text(response, 3800)}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def code_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get help with a coding concept."""
    if not context.args:
        await update.message.reply_text(
            "❓ <b>Coding Help</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /helpcode [topic]\n\n"
            "💡 <b>Example:</b>\n"
            "<code>/helpcode recursion</code>",
            parse_mode="HTML"
        )
        return

    topic = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        system_prompt = """Explain coding concepts clearly with examples. 
        Use structured formatting. Be concise and helpful."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Explain: {topic}"}
        ]

        response = chat_completion(messages, max_tokens=1000)
        response = clean_response(response)
        response = md_to_html(response)

        await update.message.reply_text(
            f"❓ <b>Coding Help: {topic}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{truncate_text(response, 3800)}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def code_format_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Format code with syntax highlighting."""
    if not context.args:
        if update.message.reply_to_message:
            code = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "📝 <b>Code Formatter</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 <b>Usage:</b> /format [code]",
                parse_mode="HTML"
            )
            return
    else:
        code = ' '.join(context.args)

    try:
        language = detect_language(code)

        await update.message.reply_text(
            f"📝 <b>Formatted Code</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔤 <b>Language:</b> {language.title()}\n\n"
            f"<code>{escape_html(code)}</code>",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


def detect_language(code: str) -> str:
    """Detect programming language from code."""
    code_lower = code.lower()

    if 'def ' in code and ':' in code:
        return "python"
    if 'function' in code or 'const ' in code or 'let ' in code:
        if ':' in code and 'interface' in code:
            return "typescript"
        return "javascript"
    if 'public class' in code or 'public static void main' in code:
        return "java"
    if '#include' in code or 'int main(' in code:
        return "cpp"
    if 'package main' in code or 'func ' in code:
        return "go"
    if 'fn main()' in code or 'let mut' in code:
        return "rust"
    if '<html' in code_lower or '<div' in code_lower:
        return "html"
    if 'SELECT' in code.upper() or 'INSERT INTO' in code.upper():
        return "sql"
    if '#!/bin/bash' in code or 'echo ' in code:
        return "bash"

    return "text"


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
