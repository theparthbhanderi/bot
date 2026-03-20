"""
Research Handler for Telegram Super Bot
Handles web research using Tavily API.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import truncate_text, escape_markdown


# Tavily API configuration
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')


async def research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle web research requests.
    Usage: /research <topic>
    """
    if not context.args:
        await update.message.reply_text(
            "🔬 <b>Web Research</b>\n\n"
            "Usage: /research <topic>\n\n"
            "I'll search the web and provide comprehensive information on your topic.\n\n"
            "Example: /research climate change effects",
            parse_mode="HTML"
        )
        return
    
    query = ' '.join(context.args)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Check if API key is configured
        if not TAVILY_API_KEY:
            await update.message.reply_text(
                "⚠️ Research API is not configured.\n"
                "Please set TAVILY_API_KEY in your environment."
            )
            return
        
        # Make API request to Tavily
        import requests
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 5
        }
        
        response = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        data = response.json()
        
        if 'results' not in data or not data['results']:
            await update.message.reply_text(f"🔍 No results found for: {query}")
            return
        
        # Format results
        response_text = f"🔬 <b>Research: {query}</b>\n\n"
        
        for i, result in enumerate(data['results'][:5], 1):
            title = escape_markdown(result.get('title', 'No title'))
            content = escape_markdown(result.get('content', 'No content'))
            url = result.get('url', '')
            
            # Truncate content
            if len(content) > 200:
                content = content[:197] + "..."
            
            response_text += f"<b>{i}. {title}</b>\n"
            response_text += f"{content}\n"
            response_text += f"🔗 {url}\n\n"
        
        await update.message.reply_text(response_text, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def deep_research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle deep research requests.
    Provides more comprehensive research results.
    Usage: /deepsearch <topic>
    """
    if not context.args:
        await update.message.reply_text(
            "🔬 <b>Deep Research</b>\n\n"
            "Usage: /deepsearch <topic>\n\n"
            "Provides comprehensive in-depth research on your topic.",
            parse_mode="HTML"
        )
        return
    
    query = ' '.join(context.args)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        if not TAVILY_API_KEY:
            await update.message.reply_text(
                "⚠️ Research API is not configured.\n"
                "Please set TAVILY_API_KEY in your environment."
            )
            return
        
        import requests
        
        headers = {"Content-Type": "application/json"}
        
        # Deep search with more results
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "comprehensive",
            "max_results": 10,
            "include_answer": True,
            "include_raw_content": False
        }
        
        response = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        data = response.json()
        
        response_text = f"🔬 <b>Deep Research: {query}</b>\n\n"
        
        # Include AI answer if available
        if 'answer' in data and data['answer']:
            response_text += f"<b>Summary:</b>\n{escape_markdown(data['answer'])}\n\n"
        
        if 'results' in data and data['results']:
            response_text += "<b>Sources:</b>\n\n"
            
            for i, result in enumerate(data['results'][:8], 1):
                title = escape_markdown(result.get('title', 'No title'))
                content = escape_markdown(result.get('content', 'No content'))
                url = result.get('url', '')
                
                if len(content) > 150:
                    content = content[:147] + "..."
                
                response_text += f"<b>{i}. {title}</b>\n"
                response_text += f"{content}\n"
                response_text += f"🔗 {url}\n\n"
        
        await update.message.reply_text(truncate_text(response_text, 4000), parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
