"""
Developer Handler for KINGPARTHH Bot
Handles developer identity and branding features.
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters


async def parth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /parth command.
    Sends a profile card with developer info.
    """
    # Profile photo path
    photo_path = os.path.join(os.getcwd(), "IMG_9890_Original.JPG")
    
    # Caption with formatted info
    caption = (
        "👨‍💻 <b>Developer: Parth R. Bhanderi</b>\n"
        "🚀 AI Builder & Developer\n\n"
        "🌐 <b>Website:</b> https://parthbhanderi.in\n"
        "📸 <b>Instagram:</b> https://instagram.com/theparthbhanderi\n"
        "💻 <b>GitHub:</b> https://github.com/theparthbhanderi\n"
        "🐦 <b>X:</b> https://x.com/parthbhanderii\n\n"
        "💡 <i>Creator of KINGPARTHH Bot</i>"
    )
    
    # Inline keyboard buttons
    keyboard = [
        [
            InlineKeyboardButton("🌐 Website", url="https://parthbhanderi.in"),
            InlineKeyboardButton("📸 Instagram", url="https://instagram.com/theparthbhanderi")
        ],
        [
            InlineKeyboardButton("💻 GitHub", url="https://github.com/theparthbhanderi"),
            InlineKeyboardButton("🐦 X", url="https://x.com/parthbhanderii")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
        else:
            # Fallback if photo not found
            await update.message.reply_text(
                caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=False
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def developer_identity_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Auto-detect questions about the developer and respond.
    """
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.lower()
    
    # Keywords to trigger response
    developer_questions = [
        "who made you",
        "who is your developer",
        "who created you",
        "who is parth",
        "developer kaun hai",
        "tujhe kisne banaya"
    ]
    
    if any(q in text for q in developer_questions):
        response = (
            "👨‍💻 <b>Developer Name:</b> Parth R. Bhanderi\n"
            "🚀 I was created by Parth, an AI Builder & Developer who loves building intelligent tools.\n\n"
            "You can use /parth to see his full profile!"
        )
        await update.message.reply_text(response, parse_mode="HTML")
