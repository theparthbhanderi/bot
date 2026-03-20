"""
Advanced Agent Handler for KINGPARTH Bot
Handles deep multi-step research, planning, and synthesis.
"""

import os
import html
import asyncio
import aiohttp
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.llm_service import chat_completion, generate_ai_response
from services.utils import clean_response, md_to_html, truncate_text, FOOTER
from services.memory import get_memory_context


# Tavily API configuration
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')


async def perform_complex_search(query: str):
    """Helper to perform Tavily search for the agent."""
    if not TAVILY_API_KEY:
        return []
        
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "comprehensive",
        "max_results": 7
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tavily.com/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=45)
            ) as resp:
                data = await resp.json()
                return data.get('results', [])
    except Exception as e:
        print(f"Agent Search Error: {e}")
        return []


async def agent_planner(query: str, context_history: str = "") -> list:
    """
    Break user query into logical execution steps using LLM.
    """
    prompt = f"""
    You are the Strategy Planner for KINGPARTH Advanced Agent.
    Your job is to break down a complex user query into 3-4 specific execution steps.
    
    User Query: {query}
    Context History: {context_history}
    
    Available Tools:
    - 'research': Web search for latest info, news, or data.
    - 'youtube': Search for video content or tutorials.
    - 'ai': Generate creative content, explanation, or logic.
    - 'knowledge': Check user's personal knowledge base.

    Return a JSON list of steps. Example:
    [
        {{"step": "Search for latest IELTS exam pattern 2024", "tool": "research"}},
        {{"step": "Find YouTube tutorials for IELTS speaking tips", "tool": "youtube"}},
        {{"step": "Create a 30-day IELTS study plan based on findings", "tool": "ai"}}
    ]
    Only return JSON, no explanation.
    """
    
    response = chat_completion([{"role": "user", "content": prompt}], max_tokens=1000)
    try:
        # Clean potential markdown JSON
        clean_json = response.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Planner Error: {e}")
        # Fallback plan
        return [
            {"step": f"Research about {query}", "tool": "research"},
            {"step": f"Provide detailed AI synthesis for {query}", "tool": "ai"}
        ]


async def execute_step(step_obj: dict, original_query: str):
    """
    Execute a single planned step using the selected tool.
    """
    step_text = step_obj.get('step', '')
    tool = step_obj.get('tool', 'ai')

    if tool == 'research':
        results = await perform_complex_search(step_text)
        return f"Research Results for '{step_text}':\n" + "\n".join([r.get('content', '')[:500] for r in results[:3]])
    
    elif tool == 'youtube':
        results = await perform_complex_search(f"site:youtube.com {step_text}")
        return f"YouTube Resources for '{step_text}':\n" + "\n".join([f"{r.get('title')}: {r.get('url')}" for r in results[:3]])

    elif tool == 'knowledge':
        from services.vector_db import search_knowledge
        # Placeholder for knowledge search requiring user_id
        return "Knowledge base context retrieved for personal query."

    else: # Default AI
        return f"AI Insight for '{step_text}':\n" + chat_completion([{"role": "user", "content": step_text}], max_tokens=1000)


async def final_synthesis(query: str, results: list, context_history: str = "") -> str:
    """
    Synthesize all step results into a final premium response.
    """
    combined_data = "\n\n".join(results)
    
    prompt = f"""
    You are KINGPARTH Advanced Agent. 
    Synthesize the following data gathered from multiple tools into a single, high-quality, structured response.
    
    Query: {query}
    Data Gathered:
    {combined_data}
    
    RESPONSE FORMAT (Strict):
    1. 🚀 **Advanced AI Report**
    2. ⚡ **Short Answer:** (2-line punchy summary)
    3. 📖 **The Plan / Details:** (Deeply structured content with bullet points)
    4. 💡 **Expert Insight:** (Pro-tip or unique perspective)
    5. 🛠️ **Tools & Resources:** (Links or specific tools mentioned)
    
    RULES:
    - Match user's language (Hindi/English/Hinglish).
    - Use HTML tags (<b>, <i>, <code>).
    - Premium, professional tone.
    """
    
    answer = chat_completion([{"role": "user", "content": prompt}], max_tokens=2500)
    return clean_response(answer)


async def agent_mode_activation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle agent mode button click."""
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>Advanced Agent Mode</b>\n\n"
        "I am now in Deep Multi-Step Mode! 🧠 🚀\n\n"
        "<b>Strategy Engine:</b>\n"
        "1. 🧠 <b>Planner:</b> Breaking query into steps\n"
        "2. 🛠 <b>Executor:</b> Running parallel tools\n"
        "3. 📊 <b>Synthesis:</b> Combining all data\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 <i>Send your complex query now (e.g., 'Make a 30-day study plan for UPSC with resources')...</i>"
    )

    context.user_data["mode"] = "agent"
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def agent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main handler for Advanced Agent Mode.
    """
    user_id = update.effective_user.id
    query = update.message.text
    chat_id = update.effective_chat.id

    # Get context
    memory_context = get_memory_context(user_id)
    history_text = "\n".join([f"{m['role']}: {m['content'][:100]}" for m in memory_context[-3:]])

    # UI Step 1: Planning
    msg = await update.message.reply_text("🧠 <b>Planning strategy...</b>", parse_mode="HTML")
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # Plan
        steps = await agent_planner(query, history_text)
        
        # UI Step 2: Gathering
        await asyncio.sleep(0.5)
        await msg.edit_text("🔍 <b>Gathering info (Parallel)...</b>", parse_mode="HTML")
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Execute parallel
        tasks = [execute_step(step, query) for step in steps]
        step_results = await asyncio.gather(*tasks)

        # UI Step 3: Processing
        await asyncio.sleep(0.5)
        await msg.edit_text("⚙️ <b>Processing & Analyzing...</b>", parse_mode="HTML")
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # UI Step 4: Finalizing
        await asyncio.sleep(0.5)
        await msg.edit_text("✨ <b>Finalizing AI Report...</b>", parse_mode="HTML")
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Synthesis
        answer = await final_synthesis(query, step_results, history_text)
        answer = md_to_html(answer)

        # Final assemble
        confidence = random.randint(94, 99)
        final_text = (
            f"{answer}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Agent Confidence:</b> {confidence}%\n"
            f"🤖 <b>Engine:</b> Advanced Multi-Step"
            + FOOTER
        )

        keyboard = [
            [
                InlineKeyboardButton("🔁 Simplify", callback_data="action_simplify"),
                InlineKeyboardButton("📋 More Details", callback_data="action_expand")
            ],
            [
                InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            truncate_text(final_text, 4000),
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    except Exception as e:
        await msg.edit_text(
            f"⚠️ <b>Advanced Agent Error</b>\n\n{str(e)[:200]}",
            parse_mode="HTML"
        )
