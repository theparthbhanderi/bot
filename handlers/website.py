"""
Website Handler for KINGPARTHH Bot
Handles website content extraction and summarization.
"""

import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import validate_url, truncate_text, escape_markdown
from services.llm_service import generate_summary


async def website_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle website summarization requests.
    Usage: /website <url> or reply with URL
    """
    # Check for URL in command args
    if not context.args:
        # Check if user replied to a message with URL
        if update.message.reply_to_message:
            text = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🌐 <b>Website Summarizer</b>\n\n"
                "Usage: /website <url>\n\n"
                "Example: /website https://example.com",
                parse_mode="HTML"
            )
            return
    else:
        text = ' '.join(context.args)
    
    # Extract URL
    from services.utils import extract_urls
    urls = extract_urls(text)
    
    if not urls:
        await update.message.reply_text("⚠️ Please provide a valid URL.")
        return
    
    url = urls[0]
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Fetch website content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract title
        title = soup.title.string if soup.title else "Untitled"
        
        # Extract main content
        # Try to find article or main content
        article = soup.find('article') or soup.find('main') or soup.find('body')
        content = article.get_text(separator='\n', strip=True) if article else ""
        
        # Clean up whitespace
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(line for line in lines if line)
        
        if not content:
            await update.message.reply_text("🔍 Could not extract content from the website.")
            return
        
        # Truncate for processing
        if len(content) > 5000:
            content = content[:5000]
        
        # Show progress
        await update.message.reply_text(
            f"📄 Extracted content from: {title}\n"
            f"Generating summary..."
        )
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Generate summary
        summary = generate_summary(content, max_length=400)
        
        # Send results
        result_text = f"🌐 <b>Website Summary</b>\n\n"
        result_text += f"<b>Title:</b> {escape_markdown(title)}\n"
        result_text += f"<b>URL:</b> {url}\n\n"
        result_text += f"<b>Summary:</b>\n{summary}"
        
        await update.message.reply_text(result_text, parse_mode="HTML")
        
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ Failed to fetch website: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def extract_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Extract raw text from a website.
    Usage: /extract <url>
    """
    if not context.args:
        await update.message.reply_text(
            "📄 <b>Website Text Extractor</b>\n\n"
            "Usage: /extract <url>\n\n"
            "Extracts raw text from a website.",
            parse_mode="HTML"
        )
        return
    
    url = context.args[0]
    
    if not validate_url(url):
        await update.message.reply_text("⚠️ Please provide a valid URL.")
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get title
        title = soup.title.string if soup.title else "Untitled"
        
        # Get content
        article = soup.find('article') or soup.find('main') or soup.find('body')
        content = article.get_text(separator='\n', strip=True) if article else ""
        
        # Clean up
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(line for line in lines if line)
        
        if not content:
            await update.message.reply_text("🔍 Could not extract content.")
            return
        
        # Truncate if too long
        if len(content) > 4000:
            content = truncate_text(content, 3900)
            content += "\n\n<i>(Content truncated - website is too long)</i>"
        
        result_text = f"📄 <b>Extracted from: {title}</b>\n\n{content}"
        
        await update.message.reply_text(result_text, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def get_headers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get website headers/meta information.
    Usage: /headers <url>
    """
    if not context.args:
        await update.message.reply_text(
            "📋 <b>Website Headers</b>\n\n"
            "Usage: /headers <url>",
            parse_mode="HTML"
        )
        return
    
    url = context.args[0]
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        result_text = f"📋 <b>Headers for:</b> {url}\n\n"
        
        # Show important headers
        important_headers = ['content-type', 'content-length', 'server', 'last-modified', 'cache-control']
        
        for header in important_headers:
            value = response.headers.get(header)
            if value:
                result_text += f"<b>{header}:</b> {value}\n"
        
        await update.message.reply_text(result_text, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
