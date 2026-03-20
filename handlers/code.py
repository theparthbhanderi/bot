"""
Code Handler for KINGPARTH Bot
Handles coding assistant features: explanations, reviews, and help.
"""

from telegram import Update
from telegram.ext import ContextTypes
from services.llm_service import (
    generate_code_explanation,
    generate_code_review,
    chat_completion
)
from services.utils import clean_response, md_to_html, truncate_text, format_premium_response, FOOTER


async def code_explain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain code in plain language."""
    if not context.args:
        if update.message.reply_to_message:
            code = update.message.reply_to_message.text
        else:
            text = format_premium_response(
                title="Code Explainer",
                short="Understand complex code in simple terms.",
                points=[
                    "Usage: /explain [code]",
                    "Or reply to any code message with /explain",
                    "Supports multiple programming languages"
                ]
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return
    else:
        code = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        language = detect_language(code)
        explanation = generate_code_explanation(code, language)
        
        # generate_code_explanation uses chat_completion which follows PREMIUM_PROMPT structure
        formatted_explanation = md_to_html(clean_response(explanation))

        await update.message.reply_text(
            formatted_explanation + FOOTER,
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
            text = format_premium_response(
                title="Code Review",
                short="Identify bugs and optimize your code.",
                points=[
                    "Usage: /review [code]",
                    "Or reply to any code message with /review",
                    "Suggestions for performance & readability"
                ]
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return
    else:
        code = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        language = detect_language(code)
        review = generate_code_review(code, language)
        formatted_review = md_to_html(clean_response(review))

        await update.message.reply_text(
            formatted_review + FOOTER,
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
        text = format_premium_response(
            title="Code Generator",
            short="Generate production-quality code from descriptions.",
            points=[
                "Usage: /code [description]",
                "Example: /code python script to scrape news",
                "Includes comments and best practices"
            ]
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    description = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        system_prompt = """You are a premium coding assistant. Generate clean, well-commented code.
        Follow the EXACT UI structure:
        🧠 <b>Code Generated</b>
        ⚡ <b>Quick Answer</b>
        {Brief summary of the code}
        📖 <b>Explanation</b>
        • {Technical detail 1}
        • {Technical detail 2}
        💡 <b>Tip</b>
        {Usage tip}
        Then provide the code block after the structured response."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate code: {description}"}
        ]

        response = chat_completion(messages, max_tokens=1500)
        formatted_response = md_to_html(clean_response(response))

        await update.message.reply_text(
            formatted_response + FOOTER,
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
        text = format_premium_response(
            title="Coding Help",
            short="Learn about any programming concept or logic.",
            points=[
                "Usage: /helpcode [topic]",
                "Example: /helpcode async in python",
                "Explains with clear examples"
            ]
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    topic = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        system_prompt = """Explain coding concepts clearly.
        Follow the EXACT UI structure:
        🧠 <b>Concept Explained</b>
        ⚡ <b>Quick Answer</b>
        {Brief high-level summary}
        📖 <b>Explanation</b>
        • {Key detail 1}
        • {Key detail 2}
        💡 <b>Tip</b>
        {Helpful advice}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Explain: {topic}"}
        ]

        response = chat_completion(messages, max_tokens=1000)
        formatted_response = md_to_html(clean_response(response))

        await update.message.reply_text(
            formatted_response + FOOTER,
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
            text = format_premium_response(
                title="Code Formatter",
                short="Format your code with proper syntax highlighting.",
                points=[
                    "Usage: /format [code]",
                    "Or reply to any code message with /format",
                    "Auto-detects programming language"
                ]
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return
    else:
        code = ' '.join(context.args)

    try:
        language = detect_language(code)
        
        text = format_premium_response(
            title=f"Formatted: {language.title()}",
            short="Here is your formatted code block.",
            tip="Copy and paste directly into your editor!"
        )
        
        # Append the code block after the premium structure
        text += f"\n<code>{escape_html(code)}</code>"

        await update.message.reply_text(text, parse_mode="HTML")

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
