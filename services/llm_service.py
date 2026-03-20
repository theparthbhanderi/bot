"""
LLM Service for Telegram Super Bot
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


def generate_ai_response(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    system_prompt: str = None,
    use_rag: bool = False,
    knowledge_context: str = None
) -> str:
    """
    Generate an AI response with optional conversation history and RAG context.
    
    Args:
        user_message: Current user message
        conversation_history: Previous messages in conversation
        system_prompt: Custom system prompt
        use_rag: Whether to use RAG context
        knowledge_context: Additional context from knowledge base
    
    Returns:
        AI response text
    """
    # Build messages list
    messages = []
    
    # Build system prompt
    if system_prompt:
        system_msg = system_prompt
    else:
        system_msg = """You are a helpful AI assistant in a Telegram bot.
        Provide clear, concise, and accurate responses.
        Be friendly and engaging."""
    
    # Add RAG context if available
    if use_rag and knowledge_context:
        system_msg += f"\n\nRelevant knowledge base information:\n{knowledge_context}"
    
    messages.append({"role": "system", "content": system_msg})
    
    # Add conversation history
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    return chat_completion(messages)


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
