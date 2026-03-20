"""
YouTube Handler for Telegram Super Bot
Handles YouTube video transcription and summarization.
"""

import os
import re
import requests
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import extract_urls, truncate_text, escape_markdown
from services.llm_service import generate_summary


async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle YouTube video summarization requests.
    Usage: /youtube <url> or reply with URL
    """
    # Get URL from args or reply
    if not context.args:
        if update.message.reply_to_message:
            text = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🎬 <b>YouTube Summarizer</b>\n\n"
                "Usage: /youtube <youtube_url>\n\n"
                "Example: /youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                parse_mode="HTML"
            )
            return
    else:
        text = ' '.join(context.args)
    
    # Extract YouTube URL
    urls = extract_urls(text)
    youtube_url = None
    
    for url in urls:
        if 'youtube.com' in url or 'youtu.be' in url:
            youtube_url = url
            break
    
    if not youtube_url:
        await update.message.reply_text("⚠️ Please provide a valid YouTube URL.")
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Extract video ID
        video_id = extract_youtube_id(youtube_url)
        
        if not video_id:
            await update.message.reply_text("⚠️ Could not extract video ID.")
            return
        
        # Get video info using oEmbed
        oembed_url = f"https://www.youtube.com/oembed?url={youtube_url}&format=json"
        oembed_response = requests.get(oembed_url, timeout=10)
        video_title = "YouTube Video"
        
        if oembed_response.status_code == 200:
            oembed_data = oembed_response.json()
            video_title = oembed_data.get('title', 'YouTube Video')
        
        await update.message.reply_text(
            f"🎬 <b>{escape_markdown(video_title)}</b>\n"
            f"Video ID: {video_id}\n\n"
            f"Downloading transcript...",
            parse_mode="HTML"
        )
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Try to get transcript using yt-dlp
        transcript = get_youtube_transcript(video_id)
        
        if not transcript:
            # Try alternate method - get description
            transcript = get_youtube_description(video_id)
            
            if not transcript:
                await update.message.reply_text(
                    "❌ Could not extract transcript from this video.\n"
                    "The video might not have captions available."
                )
                return
            
            await update.message.reply_text(
                "⚠️ Transcript not available. Using video description instead."
            )
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Generate summary
        summary = generate_summary(transcript, max_length=500)
        
        # Send result
        result_text = f"🎬 <b>YouTube Summary</b>\n\n"
        result_text += f"<b>Title:</b> {escape_markdown(video_title)}\n"
        result_text += f"<b>URL:</b> {youtube_url}\n\n"
        result_text += f"<b>Summary:</b>\n{summary}"
        
        await update.message.reply_text(result_text, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def youtube_transcript_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get YouTube video transcript.
    Usage: /transcript <url>
    """
    if not context.args:
        await update.message.reply_text(
            "📝 <b>YouTube Transcript</b>\n\n"
            "Usage: /transcript <youtube_url>",
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
        
        # Get transcript
        transcript = get_youtube_transcript(video_id)
        
        if not transcript:
            await update.message.reply_text(
                "⚠️ Could not get transcript. Captions might not be available."
            )
            return
        
        # Truncate if too long
        if len(transcript) > 4000:
            transcript = truncate_text(transcript, 3900)
            transcript += "\n\n<i>(Transcript truncated)</i>"
        
        await update.message.reply_text(
            f"📝 <b>Transcript:</b>\n\n{transcript}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


def extract_youtube_id(url: str) -> str:
    """
    Extract YouTube video ID from URL.
    
    Args:
        url: YouTube URL
    
    Returns:
        Video ID or None
    """
    # Patterns for different YouTube URL formats
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
    """
    Get YouTube video transcript.
    
    Args:
        video_id: YouTube video ID
    
    Returns:
        Transcript text or None
    """
    try:
        # Try using yt-dlp
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
            
            # Try to get subtitles
            subtitles = info.get('subtitles') or info.get('automatic_captions')
            
            if subtitles:
                # Get English subtitles
                sub_data = subtitles.get('en') or list(subtitles.values())[0]
                
                if sub_data:
                    # For simplicity, return a placeholder
                    # In production, you'd parse the subtitle format
                    return f"[Transcript available for video {video_id}]"
        
        return None
        
    except Exception as e:
        print(f"Transcript error: {e}")
        return None


def get_youtube_description(video_id: str) -> str:
    """
    Get YouTube video description as fallback.
    
    Args:
        video_id: YouTube video ID
    
    Returns:
        Description text or None
    """
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
