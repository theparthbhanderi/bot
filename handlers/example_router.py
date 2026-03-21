import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from core.ui import format_smart_response, build_smart_actions
from core.animations import ProgressiveMessage

async def example_smart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Example demonstrating the 5 Parts of the new UI architecture.
    Triggered manually for showcase purposes.
    """
    # 1. Start Progressive Flow
    progress = ProgressiveMessage(update, context)
    await progress.start("⚡ <b>Processing...</b>")
    
    # 2. Simulate API Execution / Deep Thinking Transitions
    await asyncio.sleep(1)
    await progress.step("🔍 <b>Searching...</b>")
    
    await asyncio.sleep(1)
    await progress.step("📄 <b>Reading...</b>")
    
    await asyncio.sleep(1.5)
    await progress.step("🧠 <b>Thinking...</b>")
    
    # 3. Smart Response Formatter
    details = [
        "Clean structure using unified core/ui.py config.",
        "Smooth experience heavily relies on tracking inline messages.",
        "Lightweight performance guaranteed by async awaits."
    ]
    
    final_text = format_smart_response(
        title="Redesigned Architecture",
        short_answer="The entire bot's layout structure now sits underneath the premium card and button UI template.",
        details=details,
        tip="Click any of the quick actions below to test!"
    )
    
    # 4. Push Final Result with Smart Buttons
    await progress.finish(
        final_text=final_text, 
        reply_markup=build_smart_actions()
    )
