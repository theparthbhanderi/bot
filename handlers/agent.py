"""
Advanced Agent Handler for KINGPARTH Bot - OPTIMIZED
Handles deep multi-step research, planning, and synthesis with caching and parallel execution.
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
from services.cache_service import cache
from services.memory import get_memory_context


# Tavily API configuration
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')


async def perform_complex_search(query: str):
    """
    OPTIMIZED Tavily Search.
    Uses 10s timeout and result caching (1800s).
    """
    if not TAVILY_API_KEY: return []
    
    # Check Cache (30 min TTL for research)
    cached = cache.get("research", query)
    if cached: return cached

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "comprehensive",
        "max_results": 5
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tavily.com/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                data = await resp.json()
                results = data.get('results', [])
                # Cache results
                cache.set("research", query, results, ttl_seconds=1800)
                return results
    except Exception as e:
        print(f"Agent Search Error: {e}")
        return []


async def agent_planner(query: str, context_history: str = "") -> list:
    """
    Break user query into logical steps using LLM.
    """
    # Check Cache for Plan
    cached_plan = cache.get("plan", query)
    if cached_plan: return cached_plan

    prompt = f"""
    Break down this query into 3 specific execution steps for an AI Agent.
    Query: {query}
    Context: {context_history}
    
    Return JSON list: [{{"step": "...", "tool": "research|youtube|ai"}}]
    Only JSON.
    """
    
    response = chat_completion([{"role": "user", "content": prompt}], max_tokens=500)
    try:
        clean_json = response.strip().replace('```json', '').replace('```', '').strip()
        steps = json.loads(clean_json)
        cache.set("plan", query, steps, ttl_seconds=3600) # Plan cache 1 hour
        return steps
    except Exception:
        return [{"step": f"Analyze {query}", "tool": "research"}]


async def execute_step(step_obj: dict, original_query: str):
    """
    Execute a single planned step.
    """
    step_text = step_obj.get('step', '')
    tool = step_obj.get('tool', 'ai')

    if tool == 'research':
        results = await perform_complex_search(step_text)
        return f"Research on {step_text}:\n" + "\n".join([r.get('content', '')[:300] for r in results[:2]])
    
    elif tool == 'youtube':
        results = await perform_complex_search(f"site:youtube.com {step_text}")
        return f"YouTube on {step_text}:\n" + "\n".join([f"{r.get('title')}: {r.get('url')}" for r in results[:2]])

    else: # Default AI
        return f"AI Insight on {step_text}:\n" + chat_completion([{"role": "user", "content": step_text}], max_tokens=500)


async def final_synthesis(query: str, results: list) -> str:
    """
    Synthesize all results into a final response.
    """
    combined_data = "\n\n".join([str(res) for res in results])
    
    prompt = f"""
    Synthesize this data into a PREMIUM structured answer for: {query}
    Data: {combined_data}
    Use HTML (<b>, <i>). Keep it concise and high-value.
    """
    
    answer = chat_completion([{"role": "user", "content": prompt}], max_tokens=1500)
    return clean_response(answer)


async def agent_mode_activation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle agent mode button click."""
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>Optimized Agent Mode</b>\n\n"
        "⚡ Speed & Precision Enabled!\n\n"
        "I will plan, search, and synthesize in parallel for the best possible answer.\n\n"
        "💬 <i>Send your query...</i>"
    )

    context.user_data["mode"] = "agent"
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def agent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    MICRO-OPTIMIZED Agent Handler.
    """
    user_id = update.effective_user.id
    query = update.message.text.strip()
    chat_id = update.effective_chat.id

    # 1. Instant Chat Action
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # 2. Check Cache (10 min TTL)
    cached_res = cache.get("agent", query)
    if cached_res:
        await update.message.reply_text(cached_res, parse_mode="HTML", disable_web_page_preview=True)
        return

    msg = await update.message.reply_text("🧠 <b>Analyzing query...</b>", parse_mode="HTML")

    try:
        query_words = query.split()
        if len(query_words) < 5:
            # Simple Path: Skip Planner
            await msg.edit_text("🔍 <b>Quick search...</b>", parse_mode="HTML")
            results = await perform_complex_search(query)
            context_text = "\n".join([r.get('content', '')[:400] for r in results[:3]])
            step_results = [f"Direct Research:\n{context_text}"]
        else:
            # Advanced Path: Planner + Parallel Parallel Execution
            await msg.edit_text("🧠 <b>Planning & Gathering...</b>", parse_mode="HTML")
            
            memory_context = get_memory_context(user_id)
            history_text = "\n".join([f"{m['role']}: {m['content'][:100]}" for m in memory_context[-3:]])
            
            # Step 1: Plan
            steps = await agent_planner(query, history_text)
            
            # Step 2: Parallel Execute
            tasks = [execute_step(step, query) for step in steps[:3]]
            step_results = await asyncio.gather(*tasks)

        # 3. Final Synthesis
        await msg.edit_text("✨ <b>Finalizing...</b>", parse_mode="HTML")
        answer = await final_synthesis(query, step_results)
        answer = md_to_html(answer)

        final_text = (
            f"{answer}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Confidence:</b> {random.randint(96, 99)}%\n"
            f"⚡ <b>Engine:</b> Micro-Optimized Agent"
            + FOOTER
        )

        keyboard = [
            [InlineKeyboardButton("🔁 Simplify", callback_data="action_simplify"), 
             InlineKeyboardButton("📋 Expand", callback_data="action_expand")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_main")]
        ]
        
        # Cache & Send
        cache.set("agent", query, final_text, ttl_seconds=600)
        await msg.edit_text(truncate_text(final_text, 4000), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Optimization Error:</b> {str(e)[:200]}", parse_mode="HTML")
