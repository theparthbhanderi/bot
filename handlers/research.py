"""
Research Handler for KINGPARTHH Bot
Handles web research using Tavily API.
"""

import os
import html
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import truncate_text


# Tavily API configuration
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')


async def research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle web research requests."""
    if not context.args:
        await update.message.reply_text(
            "🔬 <b>Web Research</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /research [topic]\n\n"
            "💡 <b>Example:</b>\n"
            "• <code>/research climate change effects</code>\n"
            "• <code>/research latest AI developments</code>",
            parse_mode="HTML"
        )
        return

    query = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if not TAVILY_API_KEY:
            await update.message.reply_text(
                "⚠️ <b>Not Configured</b>\n\n"
                "Research API key is missing.\n"
                "Set <code>TAVILY_API_KEY</code> in your environment.",
                parse_mode="HTML"
            )
            return

        # Use aiohttp for async request
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 5
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tavily.com/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()

        if 'results' not in data or not data['results']:
            await update.message.reply_text(
                f"🔍 <b>No Results</b>\n\nNo research found for: <i>{html.escape(query)}</i>",
                parse_mode="HTML"
            )
            return

        response_text = (
            f"🔬 <b>Research: {html.escape(query)}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for i, result in enumerate(data['results'][:5], 1):
            title = html.escape(result.get('title', 'No title'))
            content = html.escape(result.get('content', 'No content'))
            url = result.get('url', '')

            if len(content) > 200:
                content = content[:197] + "..."

            response_text += f"{i}. <b><a href='{url}'>{title}</a></b>\n"
            response_text += f"<i>{content}</i>\n\n"

        await update.message.reply_text(
            truncate_text(response_text, 4000),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def deep_research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deep research requests."""
    if not context.args:
        await update.message.reply_text(
            "🔬 <b>Deep Research</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /deepsearch [topic]\n\n"
            "💡 Provides comprehensive, in-depth analysis.",
            parse_mode="HTML"
        )
        return

    query = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if not TAVILY_API_KEY:
            await update.message.reply_text(
                "⚠️ <b>Not Configured</b>\n\n"
                "Set <code>TAVILY_API_KEY</code> in your environment.",
                parse_mode="HTML"
            )
            return

        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "comprehensive",
            "max_results": 10,
            "include_answer": True,
            "include_raw_content": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tavily.com/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()

        response_text = (
            f"🔬 <b>Deep Research: {html.escape(query)}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Include AI answer if available
        if 'answer' in data and data['answer']:
            response_text += f"⚡ <b>Summary:</b>\n{html.escape(data['answer'])}\n\n"
            response_text += "━━━━━━━━━━━━━━━━━━━━━\n\n"

        if 'results' in data and data['results']:
            response_text += "📚 <b>Sources:</b>\n\n"

            for i, result in enumerate(data['results'][:8], 1):
                title = html.escape(result.get('title', 'No title'))
                content = html.escape(result.get('content', 'No content'))
                url = result.get('url', '')

                if len(content) > 150:
                    content = content[:147] + "..."

                response_text += f"{i}. <b><a href='{url}'>{title}</a></b>\n"
                response_text += f"<i>{content}</i>\n\n"

        await update.message.reply_text(
            truncate_text(response_text, 4000),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )
