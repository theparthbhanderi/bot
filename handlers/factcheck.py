"""
Fact Check Handler for Telegram Super Bot
Handles fact checking using Google Fact Check API.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from services.utils import escape_markdown


# Google Fact Check API configuration
GOOGLE_FACT_CHECK_API_KEY = os.getenv('GOOGLE_FACT_CHECK_API_KEY', '')
FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1/claims:search"


async def fact_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle fact check requests.
    Usage: /factcheck <claim to verify>
    """
    if not context.args:
        await update.message.reply_text(
            "🔍 <b>Fact Check</b>\n\n"
            "Usage: /factcheck <claim to verify>\n\n"
            "Example: /factcheck The earth is flat",
            parse_mode="HTML"
        )
        return
    
    claim = ' '.join(context.args)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Check if API key is configured
        if not GOOGLE_FACT_CHECK_API_KEY:
            await update.message.reply_text(
                "⚠️ Fact Check API is not configured.\n"
                "Please set GOOGLE_FACT_CHECK_API_KEY in your environment."
            )
            return
        
        # Make API request
        import requests
        params = {
            'key': GOOGLE_FACT_CHECK_API_KEY,
            'query': claim,
            'languageCode': 'en'
        }
        
        response = requests.get(FACT_CHECK_URL, params=params)
        data = response.json()
        
        if 'claims' not in data or not data['claims']:
            await update.message.reply_text(
                f"🔍 <b>Fact Check Result</b>\n\n"
                f"Claim: \"{claim}\"\n\n"
                f"❓ No fact-check results found for this claim.",
                parse_mode="HTML"
            )
            return
        
        # Format results
        claim_data = data['claims'][0]
        claim_text = claim_data.get('text', claim)
        
        response_text = f"🔍 <b>Fact Check Result</b>\n\n"
        response_text += f"Claim: \"{escape_markdown(claim_text)}\"\n\n"
        
        # Check for reviews
        if 'claimReviews' in claim_data and claim_data['claimReviews']:
            review = claim_data['claimReviews'][0]
            rating = review.get('textualRating', 'Unknown')
            publisher = review.get('publisher', {}).get('name', 'Unknown')
            url = review.get('url', '')
            
            # Determine emoji based on rating
            rating_lower = rating.lower()
            if 'true' in rating_lower or 'correct' in rating_lower:
                emoji = "✅"
            elif 'false' in rating_lower or 'wrong' in rating_lower:
                emoji = "❌"
            elif 'partial' in rating_lower:
                emoji = "⚠️"
            else:
                emoji = "❓"
            
            response_text += f"<b>Rating:</b> {emoji} {escape_markdown(rating)}\n"
            response_text += f"<b>Source:</b> {escape_markdown(publisher)}\n"
            response_text += f"<b>URL:</b> {url}\n"
        else:
            response_text += "❓ No reviews available for this claim."
        
        await update.message.reply_text(response_text, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def verify_claim_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Alias for fact_check_handler.
    """
    await fact_check_handler(update, context)
