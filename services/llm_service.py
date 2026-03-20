"""
LLM Service for KINGPARTH Bot
Handles all AI/LLM interactions with Async OpenAI focus.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI, AsyncOpenAI
from services.cache_service import cache

# Get environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo')

# Initialize OpenAI clients
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

async_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)


def get_available_models() -> List[str]:
    """Get list of available models from the API."""
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return [LLM_MODEL_NAME]


def chat_completion(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    system_prompt: str = None
) -> str:
    """Sync chat completion."""
    model = model or LLM_MODEL_NAME
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in chat completion: {e}")
        return f"❌ Error: {str(e)}"


async def async_chat_completion(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    system_prompt: str = None
) -> str:
    """Generate a chat completion using the Async OpenAI client."""
    model = model or LLM_MODEL_NAME
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        response = await async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in async chat completion: {e}")
        return f"❌ Error: {str(e)}"


async def async_chat_completion_stream(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    system_prompt: str = None
):
    """Generate a streaming chat completion."""
    model = model or LLM_MODEL_NAME
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        response = await async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"Error in streaming chat completion: {e}")
        yield f"❌ Error: {str(e)}"


# ==================== Premium System Prompt ====================

PREMIUM_PROMPT = """You are KINGPARTH Bot — a premium AI assistant.
Follow this EXACT UI structure for ALL responses:

🧠 <b>{Title}</b>

⚡ <b>Quick Answer</b>
{Short, direct answer in 1-2 lines}

📖 <b>Explanation</b>
• {Key point 1}
• {Key point 2}
• {Key point 3}

💡 <b>Tip</b> (Optional)
{Helpful advice or example}

🎯 RULES:
• Use <b> for headings only
• Use • for bullets
• Keep it clean, minimal, and premium
• No markdown symbols like ** or #
• Match user language (Hindi/English)"""

async def generate_ai_response(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    system_prompt: str = None,
    use_rag: bool = False,
    knowledge_context: str = None,
    use_semantic_cache: bool = True
) -> str:
    """ULTRA-OPTIMIZED ASYNC AI response generator."""
    # 1. Micro-optimization: Simple queries
    clean_query = user_message.lower().strip()
    if clean_query in ["hi", "hello", "hey"]: return "👋 Hello! How can I help you today?"
    if clean_query in ["who are you", "what is your name"]: return "🤖 I am KINGPARTH Bot, your ultra-fast AI assistant!"

    # 2. Multi-Layer Cache Check
    cache_key = f"{user_message[:100]}:{use_rag}:{bool(knowledge_context)}"
    cached_res = cache.get("llm", cache_key)
    if cached_res: return cached_res
    
    if use_semantic_cache:
        semantic_res = cache.get_semantic("llm", user_message)
        if semantic_res: return semantic_res

    # 3. Dynamic Optimization
    query_len = len(user_message.split())
    max_tokens = 300 if query_len < 15 else (800 if query_len < 50 else 1500)
    model = "gpt-3.5-turbo" if query_len < 15 else LLM_MODEL_NAME

    # 4. Prompt Compression
    messages = []
    system_msg = system_prompt or PREMIUM_PROMPT
    if use_rag and knowledge_context:
        system_msg += f"\n\nContext Snippet:\n{knowledge_context[:800]}"
    messages.append({"role": "system", "content": system_msg})
    if conversation_history:
        messages.extend(conversation_history[-2:]) # Only last 2 for extreme speed
    messages.append({"role": "user", "content": user_message})
    
    # 5. Execute Async
    response = await async_chat_completion(messages, model=model, max_tokens=max_tokens)
    
    # 6. Save Cache
    if response and not response.startswith("❌"):
        cache.set("llm", cache_key, response, ttl_seconds=3600, use_semantic=use_semantic_cache)
    
    return response


def generate_code_explanation(code, language="python"):
    system_prompt = f"Explain this {language} code concisely."
    return chat_completion([{"role": "user", "content": code}], system_prompt=system_prompt)

def generate_code_review(code, language="python"):
    system_prompt = f"Review this {language} code for issues and improvements."
    return chat_completion([{"role": "user", "content": code}], system_prompt=system_prompt)

def generate_summary(text, max_length=200):
    return chat_completion([{"role": "user", "content": f"Summarize: {text}"}], max_tokens=max_length//2)

async def async_translate_text(text: str, target_language: str) -> str:
    """Async translation using LLM to maintain formatting."""
    prompt = f"Translate the following text to {target_language}. MAINTAIN the exact same HTML formatting (like <b>, •, etc.). Only return the translated text.\n\nText:\n{text}"
    messages = [{"role": "user", "content": prompt}]
    return await async_chat_completion(messages, max_tokens=2000)

def translate_text(text, target_language):
    return chat_completion([{"role": "user", "content": f"Translate to {target_language}: {text}"}])

def answer_question(question, context=None):
    return chat_completion([{"role": "user", "content": question}], system_prompt=f"Context: {context}" if context else None)
