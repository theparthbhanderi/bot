#!/usr/bin/env python3
"""
KINGPARTHH Bot - Main Entry Point
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
from handlers.developer import parth_handler, developer_identity_logic

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
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
    welcome_text = f"👋 <b>Welcome to KINGPARTHH Bot, {user.first_name}!</b>\n\nI am your ultimate AI assistant. What would you like to explore today?"
    
    keyboard = [
        [InlineKeyboardButton("🤖 AI Chat", callback_data="btn_ai"), InlineKeyboardButton("📰 News", callback_data="btn_news")],
        [InlineKeyboardButton("🔍 Research", callback_data="btn_research"), InlineKeyboardButton("🔎 Fact Check", callback_data="btn_fact")],
        [InlineKeyboardButton("🛠️ Tools (Web/YT/PDF)", callback_data="btn_tools")],
        [InlineKeyboardButton("💻 Coding", callback_data="btn_code"), InlineKeyboardButton("📚 Knowledge Hub", callback_data="btn_kb")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
🔰 <b>Help - KINGPARTHH Bot</b>

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "btn_main":
        await start_handler(update, context)
        return
        
    back_button = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="btn_main")]]
    reply_markup = InlineKeyboardMarkup(back_button)
        
    category_texts = {
        "btn_ai": "<b>🤖 AI Chat Commands</b>\n\n/ai [message] - Chat with AI\n/clear - Clear conversation memory\n/usage - Check your daily limit",
        "btn_news": "<b>📰 News Commands</b>\n\n/news [topic] - Search news for a topic\n/topnews - Get top global headlines\n/topic [topic] - Get news by category",
        "btn_research": "<b>🔍 Deep Research</b>\n\n/research [topic] - General web research\n/deepsearch [topic] - Detailed, in-depth research",
        "btn_fact": "<b>🔎 Fact Check</b>\n\n/factcheck [claim] - Check if a claim or news is real or fake",
        "btn_tools": "<b>🛠️ Utilities</b>\n\n/website [url] - Summarize any website\n/extract [url] - Extract text from a site\n/youtube [url] - Summarize a YouTube video\n\n<i>Also: Send a PDF to summarize it, or an Image to extract Text!</i>",
        "btn_code": "<b>💻 Coding Assistant</b>\n\n/explain [code] - Explain code snippets\n/review [code] - Review and improve code\n/code [description] - Generate new code\n/help [topic] - Get programming help",
        "btn_kb": "<b>📚 RAG/Knowledge Hub</b>\n\n/addkb [text] - Save information to your memory\n/ask [question] - Ask questions based on your saved info\n/mykb - View everything you saved\n/searchkb [query] - Search through your memory"
    }
    
    text = category_texts.get(data, "Unknown option selected.")
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


# ==================== Main Function ====================

def main():
    """Main function to run the bot."""
    
    # Get bot token from environment
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment!")
        logger.info("Please set BOT_TOKEN in .env file or environment")
        sys.exit(1)
        
    async def post_init(application: Application):
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Start the AI assistant"),
            BotCommand("ai", "Chat with AI"),
            BotCommand("news", "Search for news on a topic"),
            BotCommand("topnews", "Get the top daily headlines"),
            BotCommand("research", "Conduct deep web research"),
            BotCommand("factcheck", "Fact-check a claim or news"),
            BotCommand("youtube", "Summarize a YouTube video"),
            BotCommand("website", "Extract text and summarize a website"),
            BotCommand("parth", "Show developer profile"),
            BotCommand("clear", "Reset your chat session / memory"),
            BotCommand("help", "See all available commands")
        ]
        await application.bot.set_my_commands(commands)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # ==================== Command Handlers ====================
    
    # Basic commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("parth", parth_handler))
    
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, developer_identity_logic), group=-1)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
    
    # Handle inline keyboards
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # ==================== Start Bot ====================
    
    logger.info("🤖 Starting KINGPARTHH Bot...")
    logger.info("📝 Register all handlers")
    logger.info("✅ Bot is ready!")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
