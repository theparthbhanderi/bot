"""
Website Handler for KINGPARTHH Bot
Handles website content extraction and summarization.
"""

import os
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import validate_url, truncate_text, escape_markdown
from services.llm_service import generate_summary


async def website_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle website summarization requests."""
    if not context.args:
        if update.message.reply_to_message:
            text = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🌐 <b>Website Summarizer</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 <b>Usage:</b> /website [url]\n\n"
                "💡 <b>Example:</b>\n"
                "<code>/website https://example.com</code>",
                parse_mode="HTML"
            )
            return
    else:
        text = ' '.join(context.args)

    from services.utils import extract_urls
    urls = extract_urls(text)

    if not urls:
        await update.message.reply_text(
            "⚠️ Please provide a valid URL.",
            parse_mode="HTML"
        )
        return

    url = urls[0]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                html_text = await resp.text()

        soup = BeautifulSoup(html_text, 'lxml')

        for script in soup(["script", "style"]):
            script.decompose()

        title = soup.title.string if soup.title else "Untitled"

        article = soup.find('article') or soup.find('main') or soup.find('body')
        content = article.get_text(separator='\n', strip=True) if article else ""

        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(line for line in lines if line)

        if not content:
            await update.message.reply_text(
                "🔍 Could not extract content from this website.",
                parse_mode="HTML"
            )
            return

        if len(content) > 5000:
            content = content[:5000]

        await update.message.reply_text(
            f"⏳ <b>Processing:</b> {escape_markdown(title)}\n"
            f"Generating summary...",
            parse_mode="HTML"
        )

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        summary = generate_summary(content, max_length=400)

        result_text = (
            f"🌐 <b>Website Summary</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 <b>Title:</b> {escape_markdown(title)}\n"
            f"🔗 <b>URL:</b> {url}\n\n"
            f"📖 <b>Summary:</b>\n{summary}"
        )

        await update.message.reply_text(result_text, parse_mode="HTML", disable_web_page_preview=True)

    except aiohttp.ClientError as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\nFailed to fetch website: {str(e)[:150]}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def extract_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Extract raw text from a website."""
    if not context.args:
        await update.message.reply_text(
            "📄 <b>Website Text Extractor</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /extract [url]\n\n"
            "Extracts raw text content from any webpage.",
            parse_mode="HTML"
        )
        return

    url = context.args[0]

    if not validate_url(url):
        await update.message.reply_text("⚠️ Please provide a valid URL.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                html_text = await resp.text()

        soup = BeautifulSoup(html_text, 'lxml')

        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        title = soup.title.string if soup.title else "Untitled"

        article = soup.find('article') or soup.find('main') or soup.find('body')
        content = article.get_text(separator='\n', strip=True) if article else ""

        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(line for line in lines if line)

        if not content:
            await update.message.reply_text("🔍 Could not extract content.")
            return

        if len(content) > 4000:
            content = truncate_text(content, 3900)
            content += "\n\n<i>(Truncated — content too long)</i>"

        result_text = (
            f"📄 <b>Extracted: {escape_markdown(title)}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{content}"
        )

        await update.message.reply_text(result_text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def get_headers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get website headers/meta information."""
    if not context.args:
        await update.message.reply_text(
            "📋 <b>Website Headers</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /headers [url]",
            parse_mode="HTML"
        )
        return

    url = context.args[0]

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.head(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
                resp_headers = resp.headers

        result_text = (
            f"📋 <b>Headers</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 {url}\n\n"
        )

        important_headers = ['content-type', 'content-length', 'server', 'last-modified', 'cache-control']

        for header in important_headers:
            value = resp_headers.get(header)
            if value:
                result_text += f"<b>{header}:</b> {value}\n"

        await update.message.reply_text(result_text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )
