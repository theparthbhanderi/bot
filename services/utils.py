"""
Utility Functions for KINGPARTH Bot
Various helper functions for common tasks.
"""

import os
import re
import json
import requests
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse, quote

# Global Async HTTP Client with Connection Pooling
# Optimized for high throughput and low latency
_http_client = None

def get_http_client():
    global _http_client
    if _http_client is None:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        _http_client = httpx.AsyncClient(limits=limits, timeout=30.0)
    return _http_client

async def close_http_client():
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None


def validate_url(url: str) -> bool:
    """
    Check if a string is a valid URL.
    
    Args:
        url: URL string to validate
    
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_urls(text: str) -> List[str]:
    """
    Extract all URLs from text.
    
    Args:
        text: Text to extract URLs from
    
    Returns:
        List of URLs
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls


def truncate_text(text: str, max_length: int = 4000) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def clean_response(text: str) -> str:
    """
    Clean LLM response for premium output.
    Removes extra whitespace, double spaces, and trailing newlines.
    
    Args:
        text: Raw LLM response
    
    Returns:
        Cleaned text
    """
    if not text:
        return text
    # Remove excessive whitespace
    text = text.strip()
    text = re.sub(r'  +', ' ', text)
    # Remove excessive newlines (3+ → 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def md_to_html(text: str) -> str:
    """
    Convert common Markdown formatting to Telegram HTML.
    Handles **bold**, *italic*, `code`, and ### headings.
    Safely escapes raw HTML tags before conversion.
    """
    if not text:
        return text
    
    # 1. First, separate code blocks to preserve them
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(match.group(1))
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"
    
    # Temporarily hide triple-backtick code blocks
    text = re.sub(r'```(?:[a-zA-Z]*)\n?([\s\S]*?)```', save_code_block, text)
    
    # 2. Escape all remaining raw HTML tags to prevent "Can't parse entities" errors
    text = escape_html(text)
    
    # 3. Convert Markdown to HTML
    # Headings
    text = re.sub(r'^###\s*(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s*(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s*(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    
    # Bold & Italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    
    # 4. Restore code blocks with proper escaping
    for i, block in enumerate(code_blocks):
        escaped_block = escape_html(block.strip())
        # Truncate block if it's individually too long for Telegram's parser
        if len(escaped_block) > 3800:
            escaped_block = escaped_block[:3797] + "..."
        text = text.replace(f"___CODE_BLOCK_{i}___", f"<pre>{escaped_block}</pre>")
        
    return text


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_translation_keyboard() -> InlineKeyboardMarkup:
    """Returns the Hindi | Gujarati | English inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🇮🇳 Hindi", callback_data="translate_hi"),
            InlineKeyboardButton("🇮🇳 Gujarati", callback_data="translate_gu"),
            InlineKeyboardButton("🇺🇸 English", callback_data="translate_en")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== Premium UI Helpers ====================

FOOTER = "\n━━━━━━━━━━━━━━━\n🚀 <i>Powered by Parth</i>"

def format_premium_response(
    title: str,
    short: str = "",
    points: List[str] = None,
    tip: str = "",
) -> str:
    """
    Format a premium, clean, and highly readable UI response for Telegram.
    Redesigned by Senior UI/UX Engineer.
    """
    # 1. Header with Bold Title
    res = f"🧠 <b>{title}</b>\n\n"
    
    # 2. Quick Answer Section
    if short:
        res += f"⚡ <b>Quick Answer</b>\n{short}\n\n"
    
    # 3. Explanation Section with Bullet Points
    if points:
        res += "📖 <b>Explanation</b>\n"
        for p in points:
            res += f"• {p}\n"
        res += "\n"
    
    # 4. Optional Tip Section
    if tip:
        res += f"💡 <b>Tip</b>\n{tip}\n\n"
    
    # 5. Single Light Divider & Footer
    res += FOOTER
    
    return res

def escape_html(text: str) -> str:
    """Helper to make text HTML safe for Telegram."""
    return (text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def detect_mode(text: str) -> str:
    """
    Auto-detect user intent from message text.
    
    Args:
        text: User message
    
    Returns:
        Detected mode: 'youtube', 'news', 'research', 'factcheck', 'code', or 'chat'
    """
    text_lower = text.lower()
    
    # YouTube detection
    if any(kw in text_lower for kw in ['youtube', 'youtu.be', 'video summarize', 'video summary']):
        return 'youtube'
    
    # News detection
    if any(kw in text_lower for kw in ['latest news', 'news about', 'headlines', 'khabar']):
        return 'news'
    
    # Research detection
    if any(kw in text_lower for kw in ['research', 'search about', 'find info', 'deep search']):
        return 'research'
    
    # Fact check detection
    if any(kw in text_lower for kw in ['fact check', 'is it true', 'verify', 'real or fake']):
        return 'factcheck'
    
    # Code detection
    if any(kw in text_lower for kw in ['write code', 'generate code', 'code for', 'program for']):
        return 'code'
    
    return 'chat'



def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Markdown.
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text
    """
    # Escape special Markdown characters
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_timestamp(timestamp: str = None) -> str:
    """
    Format timestamp to readable string.
    
    Args:
        timestamp: ISO format timestamp (optional)
    
    Returns:
        Formatted timestamp
    """
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return timestamp
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def download_file(url: str, save_path: str) -> bool:
    """
    Download a file from URL.
    
    Args:
        url: File URL
        save_path: Local path to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False


def fetch_json(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> Optional[Dict]:
    """
    Fetch JSON from URL.
    
    Args:
        url: API URL
        headers: Optional headers
        timeout: Request timeout
    
    Returns:
        JSON response or None
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"JSON fetch error: {e}")
        return None


def post_json(url: str, data: Dict, headers: Dict[str, str] = None, timeout: int = 30) -> Optional[Dict]:
    """
    POST JSON to URL.
    
    Args:
        url: API URL
        data: JSON data
        headers: Optional headers
        timeout: Request timeout
    
    Returns:
        JSON response or None
    """
    try:
        response = requests.post(url, json=data, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"JSON post error: {e}")
        return None


def parse_markdown_bold(text: str) -> str:
    """
    Parse **bold** text in markdown.
    
    Args:
        text: Text with markdown
    
    Returns:
        Text with Telegram HTML bold tags
    """
    # Replace **text** with <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Replace *italic* with <i>italic</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Replace `code` with <code>code</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def split_message(text: str, max_length: int = 4000) -> List[str]:
    """
    Split long message into chunks.
    
    Args:
        text: Long text
        max_length: Maximum chunk length
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    lines = text.split('\n')
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def get_file_extension(url: str) -> str:
    """
    Get file extension from URL.
    
    Args:
        url: File URL
    
    Returns:
        File extension (without dot)
    """
    parsed = urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1]
    return ext.lstrip('.').lower() if ext else ''


def is_image_url(url: str) -> bool:
    """
    Check if URL points to an image.
    
    Args:
        url: URL to check
    
    Returns:
        True if image URL
    """
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
    ext = get_file_extension(url)
    return ext in image_extensions


def is_pdf_url(url: str) -> bool:
    """
    Check if URL points to a PDF.
    
    Args:
        url: URL to check
    
    Returns:
        True if PDF URL
    """
    return get_file_extension(url) == 'pdf'


def format_error_message(error: Exception) -> str:
    """
    Format error message for user display.
    
    Args:
        error: Exception object
    
    Returns:
        User-friendly error message
    """
    error_msg = str(error)
    
    # Shorten common error messages
    if "rate limit" in error_msg.lower():
        return "⚠️ Rate limit exceeded. Please try again later."
    elif "timeout" in error_msg.lower():
        return "⏱️ Request timed out. Please try again."
    elif "connection" in error_msg.lower():
        return "🔌 Connection error. Please check your internet."
    else:
        return f"❌ Error: {error_msg[:100]}"
