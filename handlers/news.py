"""
News Handler for Telegram Super Bot
Handles news search using GNews API.
"""

import os
import html
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import truncate_text, escape_markdown
from gnews import GNews


# Initialize GNews client
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', '')
gnews_client = GNews(language='en', max_results=10)


async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle news search requests.
    Usage: /news <search term>
    """
    # Get search query from command arguments
    if not context.args:
        await update.message.reply_text(
            "📰 <b>News Search</b>\n\n"
            "Usage: /news <search term>\n\n"
            "Example: /news artificial intelligence",
            parse_mode="HTML"
        )
        return
    
    query = ' '.join(context.args)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Fetch news
        news = gnews_client.get_news(query)
        
        if not news:
            await update.message.reply_text(f"🔍 No news found for: {query}")
            return
        
        # Format results
        response = f"📰 <b>News: {query}</b>\n\n"
        
        for i, article in enumerate(news[:5], 1):  # Limit to 5 results
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            published = article.get('published date', 'Unknown date')
            url = article.get('url', '')
            
            response += f"{i}. <b><a href='{url}'>{title}</a></b>\n"
            response += f"   📰 <i>{publisher}</i>"
            if published != 'Unknown date':
                response += f" • 🕐 {published}"
            response += "\n\n"
        
        await update.message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching news: {str(e)}")


async def top_news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle top news requests.
    Usage: /topnews
    """
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Fetch top news
        news = gnews_client.get_top_news()
        
        if not news:
            await update.message.reply_text("🔍 No news available at the moment.")
            return
        
        # Format results
        response = "📰 <b>Top News</b>\n\n"
        
        for i, article in enumerate(news[:5], 1):
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            published = article.get('published date', 'Unknown date')
            url = article.get('url', '')
            
            response += f"{i}. <b><a href='{url}'>{title}</a></b>\n"
            response += f"   📰 <i>{publisher}</i>"
            if published != 'Unknown date':
                response += f" • 🕐 {published}"
            response += "\n\n"
        
        await update.message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching news: {str(e)}")


async def news_by_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle news by topic requests.
    Usage: /topic <topic name>
    """
    if not context.args:
        await update.message.reply_text(
            "📰 <b>News by Topic</b>\n\n"
            "Usage: /topic <topic>\n\n"
            "Example: /topic technology",
            parse_mode="HTML"
        )
        return
    
    topic = ' '.join(context.args)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Fetch news by topic
        news = gnews_client.get_news_by_topic(topic)
        
        if not news:
            await update.message.reply_text(f"🔍 No news found for topic: {topic}")
            return
        
        # Format results
        response = f"📰 <b>Topic: {topic.title()}</b>\n\n"
        
        for i, article in enumerate(news[:5], 1):
            title = html.escape(article.get('title', 'No title'))
            publisher = html.escape(article.get('publisher', {}).get('title', 'Unknown'))
            url = article.get('url', '')
            
            response += f"{i}. <b><a href='{url}'>{title}</a></b>\n"
            response += f"   📰 <i>{publisher}</i>\n\n"
        
        await update.message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching news: {str(e)}")
