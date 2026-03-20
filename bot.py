#!/usr/bin/env python3
"""
KINGPARTHH Bot - Main Entry Point
A comprehensive Telegram bot with AI features, RAG, and more.
"""

import os
import sys
import asyncio
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

# Services
from services.utils import detect_mode, FOOTER
from services.llm_service import generate_ai_response, chat_completion
from services.utils import clean_response, md_to_html, truncate_text

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
    """Handle /start command with premium app-like UI."""
    user = update.effective_user
    welcome_text = (
        f"✨ <b>Welcome to KINGPARTHH Bot</b>\n\n"
        f"Hey {user.first_name}! 👋\n"
        f"Your all-in-one AI assistant 🚀\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Choose what you want to do 👇"
    )

    keyboard = [
        [
            InlineKeyboardButton("🤖 AI Chat", callback_data="btn_ai"),
            InlineKeyboardButton("🧠 Research", callback_data="btn_research")
        ],
        [
            InlineKeyboardButton("📰 News", callback_data="btn_news"),
            InlineKeyboardButton("🔎 Fact Check", callback_data="btn_fact")
        ],
        [
            InlineKeyboardButton("🎬 YouTube", callback_data="btn_tools"),
            InlineKeyboardButton("🖼️ OCR / PDF", callback_data="btn_ocr")
        ],
        [
            InlineKeyboardButton("💻 Coding", callback_data="btn_code"),
            InlineKeyboardButton("📚 Knowledge", callback_data="btn_kb")
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer", callback_data="btn_dev")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "📖 <b>KINGPARTHH Bot — Command Guide</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 <b>AI Chat</b>\n"
        "• /ai [message] — Chat with AI\n"
        "• /clear — Reset conversation\n"
        "• /usage — Check your usage stats\n\n"
        "📰 <b>News</b>\n"
        "• /news [topic] — Search news\n"
        "• /topnews — Top headlines\n"
        "• /topic [category] — News by topic\n\n"
        "🔍 <b>Research</b>\n"
        "• /research [topic] — Web research\n"
        "• /deepsearch [topic] — In-depth research\n\n"
        "🔎 <b>Fact Check</b>\n"
        "• /factcheck [claim] — Verify a claim\n\n"
        "🛠️ <b>Utilities</b>\n"
        "• /website [url] — Summarize website\n"
        "• /extract [url] — Extract text\n"
        "• /youtube [url] — Summarize video\n"
        "• 📷 Send Image → OCR\n"
        "• 📄 Send PDF → Summary\n\n"
        "💻 <b>Coding</b>\n"
        "• /explain [code] — Explain code\n"
        "• /review [code] — Code review\n"
        "• /code [desc] — Generate code\n\n"
        "📚 <b>Knowledge Hub</b>\n"
        "• /addkb [text] — Save knowledge\n"
        "• /ask [question] — Ask from KB\n"
        "• /mykb — View saved items\n\n"
        "👨‍💻 <b>Developer</b>\n"
        "• /parth — Developer profile\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 <b>Tip:</b> Just send a message to chat with AI directly!"
        + FOOTER
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "⚠️ <b>Oops!</b> Something went wrong.\n\n"
            "Please try again or use /help for guidance.",
            parse_mode="HTML"
        )


async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages with smart auto mode detection."""
    text = update.message.text
    mode = detect_mode(text)

    if mode == 'youtube':
        # Try to extract URL and redirect
        from services.utils import extract_urls
        urls = extract_urls(text)
        yt_urls = [u for u in urls if 'youtube.com' in u or 'youtu.be' in u]
        if yt_urls:
            context.args = [yt_urls[0]]
            await youtube_handler(update, context)
            return

    elif mode == 'news':
        # Strip the keyword and search
        query = text.lower().replace('latest news', '').replace('news about', '').replace('headlines', '').replace('khabar', '').strip()
        if query:
            context.args = query.split()
            await news_handler(update, context)
            return

    elif mode == 'factcheck':
        query = text.lower().replace('fact check', '').replace('is it true', '').replace('verify', '').replace('real or fake', '').strip()
        if query:
            context.args = query.split()
            await fact_check_handler(update, context)
            return

    # Default: AI chat
    await ai_chat_handler(update, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button clicks with smooth navigation."""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Main menu navigation
    if data == "btn_main":
        await start_handler(update, context)
        return

    # Quick action buttons (from AI responses)
    if data.startswith("action_"):
        await handle_quick_action(update, context, data)
        return

    # Back button for all categories
    back_button = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")]]
    reply_markup = InlineKeyboardMarkup(back_button)

    category_texts = {
        "btn_ai": (
            "🤖 <b>AI Chat</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /ai [message] — Chat with AI\n"
            "• /clear — Clear conversation memory\n"
            "• /usage — Check your daily limit\n\n"
            "💡 <i>Or just type a message to chat!</i>"
        ),
        "btn_news": (
            "📰 <b>News Center</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /news [topic] — Search news\n"
            "• /topnews — Top global headlines\n"
            "• /topic [category] — News by category\n\n"
            "💡 <i>Example: /news artificial intelligence</i>"
        ),
        "btn_research": (
            "🧠 <b>Deep Research</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /research [topic] — Web research\n"
            "• /deepsearch [topic] — In-depth analysis\n\n"
            "💡 <i>Example: /deepsearch climate change effects</i>"
        ),
        "btn_fact": (
            "🔎 <b>Fact Check</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /factcheck [claim] — Verify any claim\n\n"
            "💡 <i>Example: /factcheck The earth is flat</i>"
        ),
        "btn_tools": (
            "🎬 <b>YouTube & Web Tools</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /youtube [url] — Summarize video\n"
            "• /website [url] — Summarize website\n"
            "• /extract [url] — Extract text\n\n"
            "💡 <i>Just paste a YouTube link to auto-summarize!</i>"
        ),
        "btn_ocr": (
            "🖼️ <b>OCR & PDF Tools</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• 📷 Send an image → Extract text\n"
            "• 📄 Send a PDF → Auto-summarize\n"
            "• /ocrurl [url] — OCR from image URL\n\n"
            "💡 <i>Just send any photo with text!</i>"
        ),
        "btn_code": (
            "💻 <b>Coding Assistant</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /explain [code] — Explain code\n"
            "• /review [code] — Review & improve\n"
            "• /code [desc] — Generate code\n"
            "• /helpcode [topic] — Programming help\n\n"
            "💡 <i>Reply to code with /explain for instant explanation!</i>"
        ),
        "btn_kb": (
            "📚 <b>Knowledge Hub (RAG)</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /addkb [text] — Save to memory\n"
            "• /ask [question] — Ask from your KB\n"
            "• /mykb — View saved items\n"
            "• /searchkb [query] — Search memory\n"
            "• /clearkb — Clear all knowledge\n\n"
            "💡 <i>Reply to any message with /addkb to save it!</i>"
        ),
        "btn_dev": (
            "👨‍💻 <b>Developer Info</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /parth — View developer profile\n\n"
            "💎 <i>Built with ❤️ by Parth R. Bhanderi</i>"
        )
    }

    text = category_texts.get(data, "❓ Unknown option selected.")
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def handle_quick_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Handle quick action buttons (Simplify, Translate, Expand)."""
    query = update.callback_query
    original_text = query.message.text or ""

    if not original_text:
        await query.answer("No content to process.")
        return

    # Show processing
    await query.answer("⚡ Processing...")
    await query.edit_message_text("⚡ <b>Processing...</b>", parse_mode="HTML")

    try:
        if action == "action_simplify":
            prompt = f"Simplify this explanation for a beginner. Keep it very short and clear:\n\n{original_text[:2000]}"
            title = "🔁 Simplified"
        elif action == "action_translate":
            prompt = f"Translate this to Hindi (Hinglish style). Keep formatting:\n\n{original_text[:2000]}"
            title = "🌐 Translated"
        elif action == "action_expand":
            prompt = f"Expand on this with more details and examples:\n\n{original_text[:2000]}"
            title = "📋 Expanded"
        else:
            await query.edit_message_text(original_text, parse_mode="HTML")
            return

        response = chat_completion(
            [{"role": "user", "content": prompt}],
            max_tokens=1500
        )

        response = clean_response(response)
        response = md_to_html(response)

        final_text = f"{title}\n\n━━━━━━━━━━━━━━━━━━━━━\n\n{response}" + FOOTER

        # Back to menu button
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            truncate_text(final_text, 4000),
            parse_mode="HTML",
            reply_markup=reply_markup
        )

    except Exception as e:
        await query.edit_message_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


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
            BotCommand("start", "🚀 Start the bot"),
            BotCommand("ai", "🤖 Chat with AI"),
            BotCommand("news", "📰 Search news"),
            BotCommand("topnews", "📰 Top headlines"),
            BotCommand("research", "🔍 Web research"),
            BotCommand("deepsearch", "🔬 Deep research"),
            BotCommand("factcheck", "🔎 Fact-check a claim"),
            BotCommand("youtube", "🎬 Summarize YouTube video"),
            BotCommand("website", "🌐 Summarize website"),
            BotCommand("parth", "👨‍💻 Developer profile"),
            BotCommand("clear", "🗑️ Reset chat session"),
            BotCommand("help", "📖 All commands")
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

    # Developer identity auto-detection (higher priority group)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, developer_identity_logic), group=-1)

    # Handle regular text messages with smart mode detection + AI
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))

    # Handle inline keyboards (including quick action buttons)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Error handler
    application.add_error_handler(error_handler)

    # ==================== Start Bot ====================

    logger.info("🤖 Starting KINGPARTHH Bot...")
    logger.info("📝 All handlers registered")
    logger.info("✅ Bot is ready!")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
