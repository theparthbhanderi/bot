"""
PDF Handler for KINGPARTH Bot
Handles PDF document processing and summarization.
"""

import os
import io
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import truncate_text, download_file, format_premium_response, FOOTER
from services.llm_service import generate_summary
from pypdf import PdfReader


async def pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle PDF document processing.
    """
    # Check for document
    if not update.message.document:
        text = format_premium_response(
            title="PDF Summarizer",
            short="Upload a PDF to get an instant AI-powered summary.",
            points=[
                "Extracts key insights and data",
                "Handles long documents with ease",
                "Supports research papers and reports"
            ],
            tip="Just send or forward any PDF file!"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return
    
    # Check if it's a PDF
    document = update.message.document
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "⚠️ Please send a PDF file."
        )
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Download the PDF
        pdf_file = await context.bot.get_file(document.file_id)
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
            await pdf_file.download_to_drive(tmp_path)
        
        # Extract text from PDF
        text = extract_text_from_pdf(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if not text:
            await update.message.reply_text(
                "🔍 Could not extract text from the PDF."
            )
            return
        
        # Show page count info
        page_count = count_pdf_pages(tmp_path)
        await update.message.reply_text(
            f"📄 Extracted text from {page_count} pages.\n"
            f"Generating summary...",
            parse_mode="HTML"
        )
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Generate summary
        summary = generate_summary(text, max_length=500)
        
        await update.message.reply_text(
            f"📄 <b>PDF Summary</b>\n\n"
            f"<b>Pages:</b> {page_count}\n\n"
            f"<b>Summary:</b>\n{summary}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing PDF: {str(e)}")


async def pdf_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle PDF from URL.
    Usage: /pdfurl <pdf_url>
    """
    if not context.args:
        await update.message.reply_text(
            "📄 <b>PDF from URL</b>\n\n"
            "Usage: /pdfurl <pdf_url>\n\n"
            "Example: /pdfurl https://example.com/document.pdf",
            parse_mode="HTML"
        )
        return
    
    pdf_url = context.args[0]
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Download PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
        
        success = download_file(pdf_url, tmp_path)
        
        if not success:
            await update.message.reply_text("❌ Failed to download PDF.")
            return
        
        # Extract text
        text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)
        
        if not text:
            await update.message.reply_text("🔍 Could not extract text from the PDF.")
            return
        
        page_count = count_pdf_pages(tmp_path)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Generate summary
        summary = generate_summary(text, max_length=500)
        
        await update.message.reply_text(
            f"📄 <b>PDF Summary</b>\n\n"
            f"<b>Source:</b> {pdf_url}\n"
            f"<b>Pages:</b> {page_count}\n\n"
            f"<b>Summary:</b>\n{summary}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def pdf_extract_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle PDF text extraction (without summary).
    """
    if not update.message.document:
        await update.message.reply_text(
            "📄 <b>PDF Text Extractor</b>\n\n"
            "Please send me a PDF document to extract text from it.",
            parse_mode="HTML"
        )
        return
    
    document = update.message.document
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("⚠️ Please send a PDF file.")
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Download the PDF
        pdf_file = await context.bot.get_file(document.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
            await pdf_file.download_to_drive(tmp_path)
        
        # Extract text
        text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)
        
        if not text:
            await update.message.reply_text("🔍 Could not extract text from the PDF.")
            return
        
        # Truncate if too long
        if len(text) > 4000:
            text = truncate_text(text, 3900)
            text += "\n\n<i>(Text truncated - document is too long)</i>"
        
        await update.message.reply_text(
            f"📄 <b>Extracted Text:</b>\n\n{text}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Extracted text
    """
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n".join(text_parts)
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def count_pdf_pages(pdf_path: str) -> int:
    """
    Count pages in a PDF.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Number of pages
    """
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception:
        return 0
