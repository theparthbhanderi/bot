"""
Fact Check Handler for KINGPARTH Bot
Handles fact checking using Google Fact Check API.
"""

import os
import html
import aiohttp
from telegram import Update
from services.utils import truncate_text, format_premium_response


# Google Fact Check API configuration
GOOGLE_FACT_CHECK_API_KEY = os.getenv('GOOGLE_FACT_CHECK_API_KEY', '')
FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1/claims:search"


async def fact_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fact check requests."""
    if not context.args:
        text = format_premium_response(
            title="Fact Checker",
            short="Verify any claim using Google Fact Check API.",
            points=[
                "Usage: /factcheck [claim]",
                "Example: /factcheck The earth is flat",
                "Fetches top-rated verdicts"
            ]
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    claim = ' '.join(context.args)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if not GOOGLE_FACT_CHECK_API_KEY:
            text = format_premium_response(
                title="Not Configured",
                short="Fact Check API key is missing.",
                tip="Set GOOGLE_FACT_CHECK_API_KEY in your environment."
            )
            await update.message.reply_text(text, parse_mode="HTML")
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
            text = format_premium_response(
                title="Fact Check Result",
                short=f"No fact-check results found for \"{html.escape(claim)}\".",
                tip="Try rephrasing or use a more specific claim."
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        claim_data = data['claims'][0]
        claim_text = claim_data.get('text', claim)

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

            points = [
                f"{emoji} <b>Verdict:</b> {verdict}",
                f"📊 <b>Rating:</b> <a href='{url}'>{html.escape(rating)}</a>",
                f"📰 <b>Source:</b> <i>{html.escape(publisher)}</i>"
            ]

            response = format_premium_response(
                title="Fact Check Result",
                short=f"Claim: \"{html.escape(claim_text)}\"",
                points=points
            )
            await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)
        else:
            text = format_premium_response(
                title="No Reviews",
                short=f"I found the claim \"{html.escape(claim_text)}\", but there are no expert reviews available.",
                tip="Try searching for a different claim."
            )
            await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )


async def verify_claim_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for fact_check_handler."""
    await fact_check_handler(update, context)
