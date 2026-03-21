#!/usr/bin/env python3
"""
KINGPARTH Bot - Main Entry Point
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
from handlers.ai import ai_chat_handler, clear_memory_handler, usage_handler, translation_callback_handler
from handlers.news import news_handler, top_news_handler, news_by_topic_handler
from handlers.factcheck import fact_check_handler
from handlers.ocr import ocr_handler, ocr_url_handler
from handlers.pdf import pdf_handler, pdf_url_handler, pdf_extract_handler
from handlers.research import research_handler, deep_research_handler
from handlers.website import website_handler, extract_text_handler, get_headers_handler
from handlers.youtube import youtube_handler, youtube_transcript_handler
from handlers.code import code_explain_handler, code_review_handler, code_generate_handler, code_help_handler, code_format_handler
from handlers.ask import ask_handler, add_knowledge_handler, my_knowledge_handler, clear_knowledge_handler, confirm_clear_knowledge_handler, search_knowledge_handler
from handlers.image import image_handler
from handlers.developer import parth_handler, developer_identity_logic
from handlers.agent import agent_mode_activation_handler, agent_handler
from handlers.coach import coach_handler, set_goal_handler, tasks_handler, complete_task_callback
from handlers.example_router import example_smart_handler

# Core UI & Utilities
from core.ui import build_main_menu, create_card
from core.animations import ProgressiveMessage
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
    
    # Always clear mode on start
    context.user_data["mode"] = "chat"
    
    welcome_content = (
        f"Hey {user.first_name}! 👋\n"
        f"Choose what you want to do 👇"
    )
    
    welcome_text = create_card(
        title="Welcome to KINGPARTH Bot",
        content=welcome_content,
        tip="Your all-in-one AI assistant 🚀"
    )

    reply_markup = build_main_menu()

    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "📖 <b>KINGPARTH Bot — Command Guide</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 <b>Agent Mode</b>\n"
        "• Click 🤖 Agent Mode in main menu\n"
        "• Deep search + Synthesis 🚀\n\n"
        "🤖 <b>AI Chat</b>\n"
        "• /ai [message] — Chat with AI\n"
        "• /clear — Reset conversation\n"
        "• /usage — Check daily limits\n\n"
        "📰 <b>News & Research</b>\n"
        "• /news [topic] — Search news\n"
        "• /topnews — Global headlines\n"
        "• /research [topic] — Web research\n"
        "• /deepsearch [topic] — Deep analysis\n\n"
        "🔎 <b>Fact Check</b>\n"
        "• /factcheck [claim] — Verify a claim\n\n"
        "🛠️ <b>Utilities</b>\n"
        "• /youtube [url] — Video summary\n"
        "• /website [url] — Website summary\n"
        "• /extract [url] — Raw text extract\n\n"
        "💻 <b>Coding</b>\n"
        "• /explain [code] — Explain code\n"
        "• /code [desc] — Generate code\n"
        "• /review [code] — Review code\n\n"
        "📚 <b>Knowledge Hub</b>\n"
        "• /addkb [text] — Save knowledge\n"
        "• /ask [question] — Ask from KB\n"
        "• /mykb — List your saved info\n\n"
        "👨‍💻 <b>Developer</b>\n"
        "• /parth — Developer profile\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Tip:</b> Just send any query to chat with AI!"
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
    """Handle regular messages with smart mode detection."""
    text = update.message.text
    
    # Check current mode
    mode_state = context.user_data.get("mode", "chat")
    
    if mode_state == "agent":
        await agent_handler(update, context)
        return
        
    if mode_state == "image":
        from handlers.image import image_handler
        context.args = text.split()
        await image_handler(update, context)
        context.user_data["mode"] = "chat" # Reset mode so they don't get stuck
        return
        
    # Auto-mode detection for chat mode
    mode = detect_mode(text)

    if mode == 'youtube':
        from services.utils import extract_urls
        urls = extract_urls(text)
        yt_urls = [u for u in urls if 'youtube.com' in u or 'youtu.be' in u]
        if yt_urls:
            context.args = [yt_urls[0]]
            await youtube_handler(update, context)
            return

    elif mode == 'news':
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
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Main menu navigation
    if data == "btn_main":
        context.user_data["mode"] = "chat" # Reset mode
        await start_handler(update, context)
        return

    # Agent mode activation
    if data == "agent_mode":
        await agent_mode_activation_handler(update, context)
        return

    # Quick action buttons
    if data.startswith("action_"):
        if data == "action_upscale":
            from handlers.image import upscale_callback_handler
            await upscale_callback_handler(update, context)
            return
        await handle_quick_action(update, context, data)
        return

    # Set mode dynamically for direct chat actions
    if data == "btn_image":
        context.user_data["mode"] = "image"
    elif data == "btn_ai":
        context.user_data["mode"] = "chat"
    elif data == "agent_mode":
        context.user_data["mode"] = "agent"

    # Back button for all categories
    back_button = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")]]
    reply_markup = InlineKeyboardMarkup(back_button)

    category_texts = {
        "btn_ai": (
            "🤖 <b>AI Chat</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /ai [message] — Chat with AI\n"
            "• /clear — Clear memory\n\n"
            "💡 <i>Just type a message to chat!</i>"
        ),
        "btn_news": (
            "📰 <b>News Center</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /news [topic] — Search news\n"
            "• /topnews — Top headlines\n\n"
            "💡 <i>Example: /news artificial intelligence</i>"
        ),
        "btn_research": (
            "🧠 <b>Deep Research</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /research [topic] — Web research\n"
            "• /deepsearch [topic] — Deep analysis\n\n"
            "💡 <i>Example: /deepsearch market trends</i>"
        ),
        "btn_fact": (
            "🔎 <b>Fact Check</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /factcheck [claim] — Verify any claim\n"
        ),
        "btn_image": (
            "🎨 <b>Image Generation</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Please type your prompt below to generate an image.\n\n"
            "💡 <i>Example: A beautiful sunset and flying superhero in the sky</i>"
        ),
        "btn_tools": (
            "🎬 <b>YouTube & Web</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /youtube [url] — Video summary\n"
            "• /website [url] — Website summary\n"
        ),
        "btn_ocr": (
            "🖼️ <b>OCR & PDF</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• 📷 Send photo → Text\n"
            "• 📄 Send PDF → Summary\n"
        ),
        "btn_code": (
            "💻 <b>Coding</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /explain [code] — Explain code\n"
            "• /code [desc] — Generate code\n"
        ),
        "btn_kb": (
            "📚 <b>Knowledge Hub</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /addkb [text] — Save info\n"
            "• /ask [question] — Ask from KB\n"
        ),
        "btn_dev": (
            "👨‍💻 <b>Developer</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• /parth — Profile info\n"
            "💎 <i>Built by Parth R. Bhanderi</i>"
        )
    }

    text = category_texts.get(data, "❓ Unknown option selected.")
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def handle_quick_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Handle quick action buttons."""
    query = update.callback_query
    original_text = query.message.text or ""

    if not original_text:
        await query.answer("No content to process.")
        return

    await query.answer("⚡ Processing...")
    
    # Temporary msg update
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

        response = chat_completion([{"role": "user", "content": prompt}], max_tokens=1500)
        response = clean_response(response)
        response = md_to_html(response)

        final_text = f"{title}\n\n━━━━━━━━━━━━━━━━━━━━━\n\n{response}" + FOOTER
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(truncate_text(final_text, 4000), parse_mode="HTML", reply_markup=reply_markup)

    except Exception as e:
        await query.edit_message_text(f"⚠️ <b>Error</b>\n\n{str(e)[:200]}", parse_mode="HTML")


# ==================== Main Function ====================

def main():
    """Main function to run the bot."""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found!")
        sys.exit(1)

    async def post_init(application: Application):
        from telegram import BotCommand
        commands = [
            BotCommand("coach", "🧑‍🎓 AI Coach"),
            BotCommand("setgoal", "🎯 Set new goal"),
            BotCommand("tasks", "📝 View daily tasks"),
            BotCommand("start", "🚀 Start the bot"),
            BotCommand("ai", "🤖 Chat with AI"),
            BotCommand("news", "📰 Search news"),
            BotCommand("topnews", "📰 Top headlines"),
            BotCommand("research", "🔍 Web research"),
            BotCommand("deepsearch", "🧠 Deep analysis"),
            BotCommand("image", "🎨 Generate AI image"),
            BotCommand("factcheck", "🔎 Fact-check"),
            BotCommand("youtube", "🎬 YT summary"),
            BotCommand("website", "🌐 Web summary"),
            BotCommand("parth", "👨‍💻 Developer"),
            BotCommand("clear", "🗑️ Reset chat"),
            BotCommand("usage", "📊 Check usage"),
            BotCommand("help", "📖 All commands")
        ]
        await application.bot.set_my_commands(commands)

    application = Application.builder().token(BOT_TOKEN).post_init(post_init).concurrent_updates(True).build()

    # Handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("parth", parth_handler))
    application.add_handler(CommandHandler("ai", ai_chat_handler))
    application.add_handler(CommandHandler("clear", clear_memory_handler))
    application.add_handler(CommandHandler("usage", usage_handler))
    
    # News handlers
    application.add_handler(CommandHandler("news", news_handler))
    application.add_handler(CommandHandler("topnews", top_news_handler))
    application.add_handler(CommandHandler("topic", news_by_topic_handler))
    
    # Research & Factcheck
    application.add_handler(CommandHandler("research", research_handler))
    application.add_handler(CommandHandler("deepsearch", deep_research_handler))
    application.add_handler(CommandHandler("factcheck", fact_check_handler))
    
    # Media & Web handlers
    application.add_handler(CommandHandler("youtube", youtube_handler))
    application.add_handler(CommandHandler("transcript", youtube_transcript_handler))
    application.add_handler(CommandHandler("website", website_handler))
    application.add_handler(CommandHandler("extract", extract_text_handler))
    application.add_handler(CommandHandler("headers", get_headers_handler))
    application.add_handler(CommandHandler("image", image_handler))

    # OCR & PDF handlers
    application.add_handler(CommandHandler("ocrurl", ocr_url_handler))
    application.add_handler(CommandHandler("pdfurl", pdf_url_handler))
    application.add_handler(CommandHandler("pdfextract", pdf_extract_handler))

    # Code handlers
    application.add_handler(CommandHandler("explain", code_explain_handler))
    application.add_handler(CommandHandler("review", code_review_handler))
    application.add_handler(CommandHandler("code", code_generate_handler))
    application.add_handler(CommandHandler("helpcode", code_help_handler))
    application.add_handler(CommandHandler("format", code_format_handler))

    # KB handlers
    application.add_handler(CommandHandler("ask", ask_handler))
    application.add_handler(CommandHandler("addkb", add_knowledge_handler))
    application.add_handler(CommandHandler("mykb", my_knowledge_handler))
    application.add_handler(CommandHandler("searchkb", search_knowledge_handler))
    application.add_handler(CommandHandler("clearkb", clear_knowledge_handler))
    application.add_handler(CommandHandler("confirmclear", confirm_clear_knowledge_handler))

    # AI Coach handlers
    application.add_handler(CommandHandler("coach", coach_handler))
    application.add_handler(CommandHandler("setgoal", set_goal_handler))
    application.add_handler(CommandHandler("tasks", tasks_handler))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(agent_mode_activation_handler, pattern="^agent_mode$"))
    application.add_handler(CallbackQueryHandler(coach_handler, pattern="^coach_main$"))
    application.add_handler(CallbackQueryHandler(set_goal_handler, pattern="^coach_set_goal$"))
    application.add_handler(CallbackQueryHandler(tasks_handler, pattern="^coach_tasks$"))
    application.add_handler(CallbackQueryHandler(complete_task_callback, pattern="^coach_done_"))
    application.add_handler(CallbackQueryHandler(translation_callback_handler, pattern="^translate_"))
    application.add_handler(CallbackQueryHandler(start_handler, pattern="^btn_main$"))

    # Message handlers
    application.add_handler(MessageHandler(filters.PHOTO, ocr_handler))
    application.add_handler(MessageHandler(filters.Document.PDF, pdf_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, developer_identity_logic), group=-1)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
    
    # Example Handler logic
    application.add_handler(CommandHandler("example", example_smart_handler))

    # Button handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Error handler
    application.add_error_handler(error_handler)

    logger.info("🤖 Starting KINGPARTH Bot Agent...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
