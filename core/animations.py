import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

async def send_typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a lightweight typing indicator to the chat."""
    chat_id = update.effective_chat.id
    if chat_id:
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception as e:
            logger.debug(f"Could not send typing action: {e}")

class ProgressiveMessage:
    """
    Handles lightweight UI transitions by tracking and editing 
    a single message to avoid spamming the conversation.
    """
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.update = update
        self.context = context
        self.message = None
        self.last_text = ""

    async def start(self, initial_text: str = "⚡ <b>Processing...</b>"):
        """Send the initial placeholder message and typing indicator."""
        self.last_text = initial_text
        await send_typing_action(self.update, self.context)
        
        try:
            if self.update.message:
                self.message = await self.update.message.reply_text(
                    self.last_text, parse_mode="HTML"
                )
            elif self.update.callback_query and self.update.callback_query.message:
                self.message = self.update.callback_query.message
                await self.update.callback_query.edit_message_text(
                    self.last_text, parse_mode="HTML"
                )
        except BadRequest as e:
            logger.debug(f"Ignored bad request during progressive message start: {e}")

    async def step(self, text: str):
        """Update the message progressively to show processing state."""
        if not self.message or self.last_text == text:
            return
            
        self.last_text = text
        await send_typing_action(self.update, self.context)
        try:
            await self.context.bot.edit_message_text(
                chat_id=self.message.chat_id,
                message_id=self.message.message_id,
                text=text,
                parse_mode="HTML"
            )
        except BadRequest as e:
            # specifically ignore 'Message is not modified'
            logger.debug(f"Progressive step failed: {e}")
            
    async def finish(self, final_text: str, reply_markup=None):
        """Set the final clean output."""
        if not self.message:
            return
            
        try:
            await self.context.bot.edit_message_text(
                chat_id=self.message.chat_id,
                message_id=self.message.message_id,
                text=final_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except BadRequest as e:
            logger.debug(f"Progressive finish failed: {e}")
