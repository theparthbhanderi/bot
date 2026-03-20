"""
News Handler for KINGPARTH Bot
Handles news search using GNews API.
"""

import os
import html
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import truncate_text, escape_markdown, format_premium_response


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

        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

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
            await update.message.reply_text(
                "📰 <b>No news available at the moment.</b>",
                parse_mode="HTML"
            )
            return

        response = (
            "📰 <b>Top Headlines</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for i, article in enumerate(news[:5], 1):
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            published = article.get('published date', '')
            url = article.get('url', '')

            response += f"{i}. <b><a href='{url}'>{title}</a></b>\n"
            response += f"   📰 <i>{publisher}</i>"
            if published:
                response += f" • 🕐 {published}"
            response += "\n\n"

        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\nCouldn't fetch news: {str(e)[:150]}",
            parse_mode="HTML"
        )


async def news_by_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle news by topic requests."""
    if not context.args:
        await update.message.reply_text(
            "📰 <b>News by Topic</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /topic [category]\n\n"
            "💡 <b>Example:</b>\n"
            "• <code>/topic technology</code>\n"
            "• <code>/topic sports</code>",
            parse_mode="HTML"
        )
        return

    topic = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        news = gnews_client.get_news_by_topic(topic)

        if not news:
            await update.message.reply_text(
                f"🔍 <b>No Results</b>\n\n"
                f"No news found for topic: <i>{html.escape(topic)}</i>",
                parse_mode="HTML"
            )
            return

        response = (
            f"📰 <b>Topic: {html.escape(topic.title())}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for i, article in enumerate(news[:5], 1):
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            url = article.get('url', '')

            response += f"{i}. <b><a href='{url}'>{title}</a></b>\n"
            response += f"   📰 <i>{publisher}</i>\n\n"

        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\nCouldn't fetch news: {str(e)[:150]}",
            parse_mode="HTML"
        )
