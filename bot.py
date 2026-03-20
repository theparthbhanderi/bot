#!/usr/bin/env python3
"""
Telegram Super Bot - Main Entry Point
A comprehensive Telegram bot with AI features, RAG, and more.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import handlers
from handlers.ai import ai_chat_handler, clear_memory_handler, usage_handler
from handlers.news import news_handler, top_news_handler, news_by_topic_handler
from handlers.factcheck import fact_check_handler
from handlers.ocr import ocr_handler, ocr_url_handler
from handlers.pdf import pdf_handler, pdf_url_handler, pdf_extract_handler
from handlers.research import research_handler, deep_research_handler
from handlers.website import website_handler, extract_text_handler, get_headers_handler
from handlers.youtube import youtube_handler, youtube_transcript_handler
from handlers.code import code_explain_handler, code_review_handler, code_generate_handler, code_help_handler, code_format_handler
from handlers.ask import ask_handler, add_knowledge_handler, my_knowledge_handler, clear_knowledge_handler, confirm_clear_knowledge_handler, search_knowledge_handler

# Telegram imports
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==================== Bot Commands ====================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    welcome_text = f"""
👋 <b>Welcome to Telegram Super Bot, {user.first_name}!</b>

I am your AI-powered assistant with many features:

<b>🤖 AI Chat</b>
/ai <message> - Chat with AI
/clear - Clear conversation memory
/usage - Check your daily usage

<b>📰 News</b>
/news <topic> - Search news
/topnews - Get top news
/topic <topic> - News by topic

<b>🔍 Research</b>
/research <topic> - Web research
/deepsearch <topic> - In-depth research

<b>🔎 Fact Check</b>
/factcheck <claim> - Verify facts

<b>📷 OCR (Image to Text)</b>
Send me an image - Extract text from images

<b>📄 PDF Processing</b>
Send me a PDF - Summarize PDF documents

<b>🌐 Website Tools</b>
/website <url> - Summarize websites
/extract <url> - Extract website text

<b>🎬 YouTube</b>
/youtube <url> - Summarize YouTube videos

<b>💻 Coding Assistant</b>
/explain <code> - Explain code
/review <code> - Review code
/code <description> - Generate code
/help <topic> - Get coding help

<b>📚 RAG/Knowledge Base</b>
/addkb <content> - Add to knowledge
/ask <question> - Ask using knowledge
/mykb - View your knowledge
/searchkb <query> - Search knowledge

Send me a message to start chatting with AI!
"""
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
🔰 <b>Help - Telegram Super Bot</b>

<b>Quick Start:</b>
• Just send a message to chat with AI
• Use commands for specific features

<b>Premium System:</b>
• 10 free AI queries per day
• Upgrade to premium for unlimited access
• Check /usage for your current status

<b>Tips:</b>
• Reply to messages to use with commands
• Use /clear to reset conversation
• Add knowledge with /addkb for RAG

<b>Support:</b>
Need help? Just ask!
"""
    await update.message.reply_text(help_text, parse_mode="HTML")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update.message:
        await update.message.reply_text(
            "⚠️ An error occurred. Please try again."
        )


async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages (echo with AI)."""
    # This allows users to just send messages to chat with AI
    await ai_chat_handler(update, context)


# ==================== Main Function ====================

def main():
    """Main function to run the bot."""
    
    # Get bot token from environment
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment!")
        logger.info("Please set BOT_TOKEN in .env file or environment")
        sys.exit(1)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ==================== Command Handlers ====================
    
    # Basic commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    
    # AI commands
    application.add_handler(CommandHandler("ai", ai_chat_handler))
    application.add_handler(CommandHandler("clear", clear_memory_handler))
    application.add_handler(CommandHandler("usage", usage_handler))
    
    # News commands
    application.add_handler(CommandHandler("news", news_handler))
    application.add_handler(CommandHandler("topnews", top_news_handler))
    application.add_handler(CommandHandler("topic", news_by_topic_handler))
    
    # Research commands
    application.add_handler(CommandHandler("research", research_handler))
    application.add_handler(CommandHandler("deepsearch", deep_research_handler))
    
    # Fact check
    application.add_handler(CommandHandler("factcheck", fact_check_handler))
    application.add_handler(CommandHandler("factcheck", fact_check_handler))
    
    # OCR commands
    application.add_handler(CommandHandler("ocrurl", ocr_url_handler))
    
    # PDF commands
    application.add_handler(CommandHandler("pdfurl", pdf_url_handler))
    application.add_handler(CommandHandler("pdfextract", pdf_extract_handler))
    
    # Website commands
    application.add_handler(CommandHandler("website", website_handler))
    application.add_handler(CommandHandler("extract", extract_text_handler))
    application.add_handler(CommandHandler("headers", get_headers_handler))
    
    # YouTube commands
    application.add_handler(CommandHandler("youtube", youtube_handler))
    application.add_handler(CommandHandler("transcript", youtube_transcript_handler))
    
    # Code commands
    application.add_handler(CommandHandler("explain", code_explain_handler))
    application.add_handler(CommandHandler("review", code_review_handler))
    application.add_handler(CommandHandler("code", code_generate_handler))
    application.add_handler(CommandHandler("helpcode", code_help_handler))
    application.add_handler(CommandHandler("format", code_format_handler))
    
    # RAG/Knowledge commands
    application.add_handler(CommandHandler("ask", ask_handler))
    application.add_handler(CommandHandler("addkb", add_knowledge_handler))
    application.add_handler(CommandHandler("mykb", my_knowledge_handler))
    application.add_handler(CommandHandler("clearkb", clear_knowledge_handler))
    application.add_handler(CommandHandler("confirmclear", confirm_clear_knowledge_handler))
    application.add_handler(CommandHandler("searchkb", search_knowledge_handler))
    
    # ==================== Message Handlers ====================
    
    # Handle photos (OCR)
    application.add_handler(MessageHandler(filters.PHOTO, ocr_handler))
    
    # Handle documents (PDF)
    application.add_handler(MessageHandler(filters.Document.PDF, pdf_handler))
    
    # Handle regular text messages with AI
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # ==================== Start Bot ====================
    
    logger.info("🤖 Starting Telegram Super Bot...")
    logger.info("📝 Register all handlers")
    logger.info("✅ Bot is ready!")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
