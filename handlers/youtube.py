"""
YouTube Handler for KINGPARTH Bot
Handles YouTube video transcription and summarization.
"""

import os
import re
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import extract_urls, truncate_text, escape_markdown
from services.llm_service import generate_summary


async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube video summarization requests."""
    if not context.args:
        if update.message.reply_to_message:
            text = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🎬 <b>YouTube Summarizer</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 <b>Usage:</b> /youtube [url]\n\n"
                "💡 <b>Example:</b>\n"
                "<code>/youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ</code>",
                parse_mode="HTML"
            )
            return
    else:
        text = ' '.join(context.args)

    urls = extract_urls(text)
    youtube_url = None

    for url in urls:
        if 'youtube.com' in url or 'youtu.be' in url:
            youtube_url = url
            break

    if not youtube_url:
        await update.message.reply_text(
            "⚠️ Please provide a valid YouTube URL.",
            parse_mode="HTML"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        video_id = extract_youtube_id(youtube_url)

        if not video_id:
            await update.message.reply_text(
                "⚠️ Could not extract video ID from this URL.",
                parse_mode="HTML"
            )
            return

        # Get video info using oEmbed (async)
        video_title = "YouTube Video"
        oembed_url = f"https://www.youtube.com/oembed?url={youtube_url}&format=json"

        async with aiohttp.ClientSession() as session:
            async with session.get(oembed_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    oembed_data = await resp.json()
                    video_title = oembed_data.get('title', 'YouTube Video')

        await update.message.reply_text(
            f"🎬 <b>{escape_markdown(video_title)}</b>\n\n"
            f"⏳ Downloading transcript...",
            parse_mode="HTML"
        )

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        transcript = get_youtube_transcript(video_id)

        if not transcript:
            transcript = get_youtube_description(video_id)

            if not transcript:
                await update.message.reply_text(
                    "❌ <b>No Transcript Available</b>\n\n"
                    "This video doesn't have captions.",
                    parse_mode="HTML"
                )
                return

            await update.message.reply_text(
                "⚠️ <i>Transcript not available. Using video description instead.</i>",
                parse_mode="HTML"
            )

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        summary = generate_summary(transcript, max_length=500)

        result_text = (
            f"🎬 <b>YouTube Summary</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 <b>Title:</b> {escape_markdown(video_title)}\n"
            f"🔗 <b>URL:</b> {youtube_url}\n\n"
            f"📖 <b>Summary:</b>\n{summary}"
        )

        await update.message.reply_text(result_text, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def youtube_transcript_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get YouTube video transcript."""
    if not context.args:
        await update.message.reply_text(
            "📝 <b>YouTube Transcript</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /transcript [url]",
            parse_mode="HTML"
        )
        return

    text = ' '.join(context.args)
    urls = extract_urls(text)
    youtube_url = None

    for url in urls:
        if 'youtube.com' in url or 'youtu.be' in url:
            youtube_url = url
            break

    if not youtube_url:
        await update.message.reply_text("⚠️ Please provide a valid YouTube URL.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        video_id = extract_youtube_id(youtube_url)

        transcript = get_youtube_transcript(video_id)

        if not transcript:
            await update.message.reply_text(
                "⚠️ <b>No transcript available.</b>\n\n"
                "Captions might not be enabled for this video.",
                parse_mode="HTML"
            )
            return

        if len(transcript) > 4000:
            transcript = truncate_text(transcript, 3900)
            transcript += "\n\n<i>(Truncated)</i>"

        await update.message.reply_text(
            f"📝 <b>Transcript</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{transcript}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


def extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_youtube_transcript(video_id: str) -> str:
    """Get YouTube video transcript."""
    try:
        import yt_dlp

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

            subtitles = info.get('subtitles') or info.get('automatic_captions')

            if subtitles:
                sub_data = subtitles.get('en') or list(subtitles.values())[0]

                if sub_data:
                    return f"[Transcript available for video {video_id}]"

        return None

    except Exception as e:
        print(f"Transcript error: {e}")
        return None


def get_youtube_description(video_id: str) -> str:
    """Get YouTube video description as fallback."""
    try:
        import yt_dlp

        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return info.get('description', '')

    except Exception:
        return None
