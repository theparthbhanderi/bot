"""
LLM Service for KINGPARTH Bot
Handles all AI/LLM interactions with OpenAI-compatible APIs.
"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Get environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo')

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)


def get_available_models() -> List[str]:
    """
    Get list of available models from the API.
    
    Returns:
        List of model names
    """
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
    """
    Generate a chat completion using the LLM.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model name (defaults to LLM_MODEL_NAME)
        temperature: Controls randomness (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        system_prompt: Optional system prompt override
    
    Returns:
        Generated response text
    """
    model = model or LLM_MODEL_NAME
    
    # Add system prompt if provided
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


# ==================== Premium System Prompt ====================

PREMIUM_PROMPT = """You are KINGPARTH Bot — a premium AI assistant inside a high-quality Telegram bot.

🎯 CORE RULES:
• Be CLEAR, CONCISE, and ACCURATE
• Avoid unnecessary long text
• Use structured formatting
• Always give the BEST possible answer

🎨 RESPONSE STYLE:
• Start with a relevant emoji + bold title
• Give a short answer first (1–2 lines)
• Then a clean structured explanation with bullet points
• Optionally add a 💡 Tip or example

✨ FORMATTING:
• Use emojis sparingly but effectively
• Use proper spacing between sections
• Use <b>bold</b> for headings
• Use <i>italics</i> for emphasis
• Use <code>code</code> for technical terms
• No messy paragraphs — keep it clean

🧠 INTELLIGENCE:
• Understand user intent deeply
• If follow-up → use context
• If unclear → assume best intent
• Detect user language → reply in same language

⚡ PERFORMANCE:
• Keep answers optimized (not too long)
• Avoid repeating same info
• Focus on delivering maximum value

🧩 SPECIAL BEHAVIOR:
• coding → structured code block + explanation
• research → concise + key insights
• learning → simple language + examples
• general → direct, premium answer

🚫 AVOID:
• Long boring paragraphs
• Generic/robotic answers
• Unnecessary disclaimers
• Repeating the question back"""


from services.cache_service import cache

def generate_ai_response(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    system_prompt: str = None,
    use_rag: bool = False,
    knowledge_context: str = None
) -> str:
    """
    OPTIMIZED AI response generator.
    Includes compression, dynamic tokens, and 900s caching.
    """
    # 1. Check Cache (Duplicate Query Detection)
    cache_key = f"{user_message[:100]}:{use_rag}:{bool(knowledge_context)}"
    cached_res = cache.get("llm", cache_key)
    if cached_res:
        return cached_res

    # 2. Dynamic Token Control
    # Short query -> few tokens, long query -> more tokens
    query_len = len(user_message.split())
    if query_len < 10:
        max_tokens = 400
    elif query_len < 30:
        max_tokens = 800
    else:
        max_tokens = 2000

    # 3. Prompt Compression (Trim history to last 3 for speed & cost)
    messages = []
    
    # Build system prompt
    system_msg = system_prompt or PREMIUM_PROMPT
    if use_rag and knowledge_context:
        system_msg += f"\n\nContext:\n{knowledge_context[:1000]}"
    
    messages.append({"role": "system", "content": system_msg})
    
    # Trim history (Last 3 messages only)
    if conversation_history:
        messages.extend(conversation_history[-3:])
    
    # Add current message
    messages.append({"role": "user", "content": user_message})
    
    # 4. Execute with Timeout
    response = chat_completion(messages, max_tokens=max_tokens)
    
    # 5. Save to Cache (15 min TTL)
    if response and not response.startswith("❌"):
        cache.set("llm", cache_key, response, ttl_seconds=900)
    
    return response



def generate_code_explanation(code: str, language: str = "python") -> str:
    """
    Generate an explanation for code.
    
    Args:
        code: Code to explain
        language: Programming language
    
    Returns:
        Code explanation
    """
    system_prompt = f"""You are a coding expert. Explain the following {language} code 
    in a clear, beginner-friendly way. Break down each part and explain what it does."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Explain this {language} code:\n\n```{language}\n{code}\n```"}
    ]
    
    return chat_completion(messages, max_tokens=2000)


def generate_code_review(code: str, language: str = "python") -> str:
    """
    Generate a code review.
    
    Args:
        code: Code to review
        language: Programming language
    
    Returns:
        Code review with suggestions
    """
    system_prompt = f"""You are a senior developer. Review the following {language} code 
    for bugs, performance issues, security concerns, and best practices.
    Provide specific suggestions for improvement."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Review this {language} code:\n\n```{language}\n{code}\n```"}
    ]
    
    return chat_completion(messages, max_tokens=2000)


def generate_summary(text: str, max_length: int = 200) -> str:
    """
    Generate a summary of text.
    
    Args:
        text: Text to summarize
        max_length: Maximum length of summary
    
    Returns:
        Summary text
    """
    system_prompt = f"""Summarize the following text in no more than {max_length} characters.
    Focus on the key points and main ideas."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Summarize this:\n\n{text}"}
    ]
    
    return chat_completion(messages, max_tokens=max_length // 4)


def translate_text(text: str, target_language: str) -> str:
    """
    Translate text to target language.
    
    Args:
        text: Text to translate
        target_language: Target language name
    
    Returns:
        Translated text
    """
    system_prompt = f"""Translate the following text to {target_language}.
    Provide only the translation, no explanations."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    
    return chat_completion(messages)


def generate_creative_content(prompt: str, content_type: str = "story") -> str:
    """
    Generate creative content.
    
    Args:
        prompt: Content prompt
        content_type: Type of content (story, poem, joke, etc.)
    
    Returns:
        Generated content
    """
    system_prompt = f"""Generate a creative {content_type} based on the following prompt.
    Be creative and engaging!"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    return chat_completion(messages, max_tokens=1500)


def answer_question(question: str, context: str = None) -> str:
    """
    Answer a question, optionally with context.
    
    Args:
        question: Question to answer
        context: Optional context to help answer
    
    Returns:
        Answer text
    """
    if context:
        system_prompt = f"""Answer the question based on the following context.
        If the context doesn't contain enough information, say so.
        
        Context:
        {context}"""
    else:
        system_prompt = "Answer the following question accurately and concisely."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    return chat_completion(messages, max_tokens=1000)
