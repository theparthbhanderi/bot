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


async def code_explain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Explain code in plain language.
    Usage: /explain <code> or reply with code
    """
    # Get code from args or reply
    if not context.args:
        if update.message.reply_to_message:
            code = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "💻 <b>Code Explainer</b>\n\n"
                "Usage: /explain <code>\n\n"
                "Or reply to a message with /explain",
                parse_mode="HTML"
            )
            return
    else:
        code = ' '.join(context.args)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Detect language
        language = detect_language(code)
        
        # Generate explanation
        explanation = generate_code_explanation(code, language)
        
        await update.message.reply_text(
            f"💻 <b>Code Explanation</b>\n\n"
            f"<b>Language:</b> {language}\n\n"
            f"<b>Explanation:</b>\n{explanation}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def code_review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Review code for issues and improvements.
    Usage: /review <code> or reply with code
    """
    if not context.args:
        if update.message.reply_to_message:
            code = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🔍 <b>Code Review</b>\n\n"
                "Usage: /review <code>\n\n"
                "Or reply to a message with /review",
                parse_mode="HTML"
            )
            return
    else:
        code = ' '.join(context.args)
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        language = detect_language(code)
        
        review = generate_code_review(code, language)
        
        await update.message.reply_text(
            f"🔍 <b>Code Review</b>\n\n"
            f"<b>Language:</b> {language}\n\n"
            f"<b>Review:</b>\n{review}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def code_generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Generate code based on description.
    Usage: /code <description>
    """
    if not context.args:
        await update.message.reply_text(
            "✨ <b>Code Generator</b>\n\n"
            "Usage: /code <description>\n\n"
            "Example: /code function to sort a list in python",
            parse_mode="HTML"
        )
        return
    
    description = ' '.join(context.args)
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        system_prompt = """You are a coding assistant. Generate clean, well-commented code 
        based on the user's description. Include explanations when needed."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate code: {description}"}
        ]
        
        response = chat_completion(messages, max_tokens=1500)
        
        await update.message.reply_text(
            f"✨ <b>Generated Code</b>\n\n"
            f"<b>Request:</b> {description}\n\n"
            f"<b>Code:</b>\n<code>{escape_html(response)}</code>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def code_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get help with a coding concept.
    Usage: /help <topic>
    """
    if not context.args:
        await update.message.reply_text(
            "❓ <b>Coding Help</b>\n\n"
            "Usage: /help <topic>\n\n"
            "Example: /help recursion",
            parse_mode="HTML"
        )
        return
    
    topic = ' '.join(context.args)
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        system_prompt = """Explain coding concepts in a beginner-friendly way.
        Use examples when helpful. Keep explanations clear and concise."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Explain: {topic}"}
        ]
        
        response = chat_completion(messages, max_tokens=1000)
        
        await update.message.reply_text(
            f"❓ <b>Coding Help: {topic}</b>\n\n{response}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def code_format_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Format code with syntax highlighting.
    Usage: /format <code>
    """
    if not context.args:
        if update.message.reply_to_message:
            code = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "📝 <b>Code Formatter</b>\n\n"
                "Usage: /format <code>",
                parse_mode="HTML"
            )
            return
    else:
        code = ' '.join(context.args)
    
    try:
        language = detect_language(code)
        
        # Just return the code with HTML formatting
        await update.message.reply_text(
            f"📝 <b>Formatted Code</b>\n\n"
            f"<b>Language:</b> {language}\n\n"
            f"<code>{escape_html(code)}</code>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


def detect_language(code: str) -> str:
    """
    Detect programming language from code.
    
    Args:
        code: Code snippet
    
    Returns:
        Detected language
    """
    code_lower = code.lower()
    
    # Python indicators
    if 'def ' in code and ':' in code and 'print(' in code:
        return "python"
    
    # JavaScript/TypeScript indicators
    if 'function' in code or 'const ' in code or 'let ' in code:
        if ':' in code and 'interface' in code:
            return "typescript"
        return "javascript"
    
    # Java indicators
    if 'public class' in code or 'public static void main' in code:
        return "java"
    
    # C/C++ indicators
    if '#include' in code or 'int main(' in code:
        return "cpp"
    
    # Go indicators
    if 'package main' in code or 'func ' in code:
        return "go"
    
    # Rust indicators
    if 'fn main()' in code or 'let mut' in code:
        return "rust"
    
    # HTML indicators
    if '<html' in code or '<div' in code:
        return "html"
    
    # SQL indicators
    if 'SELECT' in code.upper() or 'INSERT INTO' in code.upper():
        return "sql"
    
    # Shell/Bash indicators
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
