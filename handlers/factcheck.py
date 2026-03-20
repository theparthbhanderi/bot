"""
Fact Check Handler for KINGPARTHH Bot
Handles fact checking using Google Fact Check API.
"""

import os
import html
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes


# Google Fact Check API configuration
GOOGLE_FACT_CHECK_API_KEY = os.getenv('GOOGLE_FACT_CHECK_API_KEY', '')
FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1/claims:search"


async def fact_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fact check requests."""
    if not context.args:
        await update.message.reply_text(
            "🔎 <b>Fact Check</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 <b>Usage:</b> /factcheck [claim]\n\n"
            "💡 <b>Example:</b>\n"
            "• <code>/factcheck The earth is flat</code>\n"
            "• <code>/factcheck 5G causes COVID</code>",
            parse_mode="HTML"
        )
        return

    claim = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if not GOOGLE_FACT_CHECK_API_KEY:
            await update.message.reply_text(
                "⚠️ <b>Not Configured</b>\n\n"
                "Set <code>GOOGLE_FACT_CHECK_API_KEY</code> in your environment.",
                parse_mode="HTML"
            )
            return

        # Use aiohttp for async request
        params = {
            'key': GOOGLE_FACT_CHECK_API_KEY,
            'query': claim,
            'languageCode': 'en'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(FACT_CHECK_URL, params=params) as resp:
                data = await resp.json()

        if 'claims' not in data or not data['claims']:
            await update.message.reply_text(
                f"🔎 <b>Fact Check Result</b>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📋 <b>Claim:</b> \"{html.escape(claim)}\"\n\n"
                f"❓ No fact-check results found.\n\n"
                f"💡 <i>Try rephrasing or use a more specific claim.</i>",
                parse_mode="HTML"
            )
            return

        claim_data = data['claims'][0]
        claim_text = claim_data.get('text', claim)

        response_text = (
            f"🔎 <b>Fact Check Result</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 <b>Claim:</b> \"{html.escape(claim_text)}\"\n\n"
        )

        if 'claimReviews' in claim_data and claim_data['claimReviews']:
            review = claim_data['claimReviews'][0]
            rating = review.get('textualRating', 'Unknown')
            publisher = review.get('publisher', {}).get('name', 'Unknown')
            url = review.get('url', '')

            # Determine verdict emoji
            rating_lower = rating.lower()
            if 'true' in rating_lower or 'correct' in rating_lower:
                emoji = "✅"
                verdict = "TRUE"
            elif 'false' in rating_lower or 'wrong' in rating_lower:
                emoji = "❌"
                verdict = "FALSE"
            elif 'partial' in rating_lower or 'mixed' in rating_lower:
                emoji = "⚠️"
                verdict = "PARTIALLY TRUE"
            else:
                emoji = "❓"
                verdict = rating.upper()

            response_text += (
                f"{emoji} <b>Verdict:</b> {verdict}\n"
                f"📊 <b>Rating:</b> <a href='{url}'>{html.escape(rating)}</a>\n"
                f"📰 <b>Source:</b> <i>{html.escape(publisher)}</i>"
            )
        else:
            response_text += "❓ No expert reviews available for this claim."

        await update.message.reply_text(response_text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def verify_claim_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for fact_check_handler."""
    await fact_check_handler(update, context)
