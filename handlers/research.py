"""
Research Handler for KINGPARTH Bot
Handles web research using Tavily API.
"""

import os
import html
import aiohttp
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.utils import truncate_text, format_premium_response, get_http_client, clean_response, md_to_html, FOOTER, get_translation_keyboard
from services.llm_service import async_chat_completion
import asyncio


# Tavily API configuration
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')


async def research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle web research requests."""
    if not context.args:
        text = format_premium_response(
            title="Web Research",
            short="Search the web for any topic using Tavily AI.",
            points=[
                "Usage: /research [topic]",
                "Example: /research global warming",
                "Fetches top 5 relevant sources"
            ]
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    query = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if not TAVILY_API_KEY:
            text = format_premium_response(
                title="Not Configured",
                short="Research API key is missing.",
                tip="Set TAVILY_API_KEY in your environment."
            )
            await update.message.reply_text(text, parse_mode="HTML")
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
            # Fallback to pure LLM if search fails
            prompt = f"Provide a brief summary for: '{query}'. Web search returned no results, so use your internal knowledge."
            answer = await async_chat_completion([{"role": "user", "content": prompt}], max_tokens=500)
            
            text = format_premium_response(
                title=f"AI Insight: {query.title()}",
                short=md_to_html(clean_response(answer)),
                tip="Web search was inconclusive, showing AI knowledge instead."
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        points = []
        for i, result in enumerate(data['results'][:5], 1):
            title = html.escape(result.get('title', 'No title'))
            url = result.get('url', '')
            points.append(f"<b><a href='{url}'>{title}</a></b>")

        response = format_premium_response(
            title=f"Research: {query.title()}",
            short=f"Found {len(points)} relevant sources for your query.",
            points=points
        )
        context.user_data["last_response"] = response
        
        keyboard = get_translation_keyboard().inline_keyboard
        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def deep_research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deep research requests with LLM synthesis."""
    if not context.args:
        text = format_premium_response(
            title="Deep Research",
            short="Comprehensive analysis on any topic.",
            points=[
                "Usage: /deepsearch [topic]",
                "Example: /deepsearch AI trends 2025",
                "Synthesizes multiple sources"
            ]
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    query = ' '.join(context.args)
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    msg = await update.message.reply_text("🔍 <b>Starting Deep Research...</b>", parse_mode="HTML")

    try:
        if not TAVILY_API_KEY:
            text = format_premium_response(
                title="Not Configured",
                short="Research API key is missing.",
                tip="Set TAVILY_API_KEY in your environment."
            )
            await msg.edit_text(text, parse_mode="HTML")
            return

        # 1. Fetch search results
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "comprehensive",
            "max_results": 10,
            "include_answer": True,
            "include_raw_content": True
        }

        client = get_http_client()
        resp = await client.post(
            "https://api.tavily.com/search",
            json=payload,
            timeout=30.0
        )
        data = resp.json()

        if 'results' not in data or not data['results']:
            # Fallback to pure LLM if search fails
            await msg.edit_text("✨ <b>No direct web data found. Using AI Knowledge...</b>", parse_mode="HTML")
            prompt = f"""The user asked for deep research on: '{query}'. 
            Web search returned no results. Provide a comprehensive answer based on your general knowledge.
            
            Follow this EXACT UI structure:
            🧠 <b>AI Insight: {query.title()}</b>
            
            ⚡ <b>Quick Answer</b>
            {{Brief high-level summary}}
            
            📖 <b>Explanation</b>
            • {{Key detail 1}}
            • {{Key detail 2}}
            • {{Key detail 3}}
            
            💡 <b>Tip</b>
            {{Helpful advice}}"""
            
            answer = await async_chat_completion([{"role": "user", "content": prompt}], max_tokens=1000)
            await msg.edit_text(truncate_text(md_to_html(clean_response(answer)) + FOOTER, 4000), parse_mode="HTML")
            return

        # 2. Synthesize answer with LLM if Tavily didn't provide one
        answer = data.get('answer', '')
        if not answer:
            await msg.edit_text("✨ <b>Synthesizing results...</b>", parse_mode="HTML")
            context_text = "\n\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in data['results'][:5]])
            prompt = f"Synthesize a comprehensive answer for the query: '{query}' based on these research results:\n\n{context_text}\n\nProvide a detailed but concise response in HTML format (use <b> for emphasis)."
            answer = await async_chat_completion([{"role": "user", "content": prompt}], max_tokens=1000)
            answer = clean_response(answer)

        # 3. Format final response
        sources = []
        for i, result in enumerate(data['results'][:5], 1):
            title = html.escape(result.get('title', 'No title'))
            url = result.get('url', '')
            sources.append(f"<b><a href='{url}'>{title}</a></b>")

        final_response = format_premium_response(
            title=f"Deep Research: {query.title()}",
            short=md_to_html(answer),
            points=sources,
            tip="Research includes real-time web data."
        )
        context.user_data["last_response"] = final_response
        
        keyboard = get_translation_keyboard().inline_keyboard
        await msg.edit_text(truncate_text(final_response, 4000), parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await msg.edit_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )
