"""
News Handler for KINGPARTH Bot
Handles news search using GNews API.
"""

import os
import html
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import truncate_text, escape_markdown, format_premium_response, get_translation_keyboard, FOOTER
from gnews import GNews


# Initialize GNews client
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', '')
gnews_client = GNews(language='en', max_results=10)


async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle news search requests."""
    if not context.args:
        text = format_premium_response(
            title="News Search",
            short="Search for any topic to get the latest headlines.",
            points=[
                "Usage: /news [topic]",
                "Example: /news technology",
                "Real-time results via GNews"
            ]
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    query = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        news = gnews_client.get_news(query)

        if not news:
            text = format_premium_response(
                title="No Results",
                short=f"I couldn't find any recent news for '{query}'.",
                tip="Try a broader topic or different keywords."
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        points = []
        for i, article in enumerate(news[:5], 1):
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            url = article.get('url', '')
            points.append(f"<b><a href='{url}'>{title}</a></b>\n  📰 <i>{publisher}</i>")

        response = format_premium_response(
            title=f"News: {query.title()}",
            short=f"Here are the top 5 articles related to {query}.",
            points=points
        )
        context.user_data["last_response"] = response
        
        keyboard = get_translation_keyboard().inline_keyboard
        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\nCouldn't fetch news: {str(e)[:150]}",
            parse_mode="HTML"
        )


async def top_news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle top news requests."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        news = gnews_client.get_top_news()

        if not news:
            text = format_premium_response(
                title="No News",
                short="I couldn't fetch any top news at the moment.",
                tip="Try again in a few minutes."
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        points = []
        for article in news[:5]:
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            url = article.get('url', '')
            points.append(f"<b><a href='{url}'>{title}</a></b>\n  📰 <i>{publisher}</i>")

        response = format_premium_response(
            title="Top Headlines",
            short="Here are the top 5 global headlines for today.",
            points=points
        )
        context.user_data["last_response"] = response
        
        keyboard = get_translation_keyboard().inline_keyboard
        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\nCouldn't fetch top news: {str(e)[:150]}",
            parse_mode="HTML"
        )


async def news_by_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle news by topic requests."""
    if not context.args:
        text = format_premium_response(
            title="News by Topic",
            short="Get news based on specific categories.",
            points=[
                "WORLD, NATION, BUSINESS",
                "TECHNOLOGY, ENTERTAINMENT",
                "SPORTS, SCIENCE, HEALTH"
            ],
            tip="Example: /topic TECHNOLOGY"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    topic = context.args[0].upper()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        news = gnews_client.get_news_by_topic(topic)

        if not news:
            text = format_premium_response(
                title="Topic Not Found",
                short=f"I couldn't find any news for the topic '{topic}'.",
                tip="Make sure you use a valid topic name."
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        points = []
        for article in news[:5]:
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            url = article.get('url', '')
            points.append(f"<b><a href='{url}'>{title}</a></b>\n  📰 <i>{publisher}</i>")

        response = format_premium_response(
            title=f"News: {topic}",
            short=f"Latest {topic} headlines for you.",
            points=points
        )
        context.user_data["last_response"] = response
        
        keyboard = get_translation_keyboard().inline_keyboard
        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\nCouldn't fetch news for '{topic}': {str(e)[:150]}",
            parse_mode="HTML"
        )
