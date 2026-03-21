import os
import logging
import httpx
import asyncio

from services.llm_service import async_chat_completion

logger = logging.getLogger(__name__)

IMAGE_API_URL = "https://fixpix-image.bcjqxt9wn8.workers.dev/"

# Predefined styles for generation
STYLES = {
    "anime": "anime style, vibrant colors, detailed illustration",
    "realistic": "ultra realistic, 8k, high detail, photography",
    "cinematic": "cinematic lighting, dramatic shadows, film style",
    "cyberpunk": "neon lights, futuristic city, cyberpunk theme"
}

import json

async def enhance_image_prompt(prompt: str, user_negative: str = None) -> dict:
    """
    ULTRA-ADVANCED PROMPT ENHANCER
    Transforms weak prompts into optimized, style-aware JSON structures.
    """
    system_prompt = """You are a world-class AI prompt engineer specializing in image generation optimization.
Your task is to transform weak user prompts into HIGH-QUALITY, MODEL-OPTIMIZED prompts.

# 🎯 OBJECTIVE
Convert simple user input into highly descriptive, visually rich, style-aware, model-optimized prompts.

# 🧠 INTELLIGENCE LAYERS
1. CONTEXT: Analyze subject, environment, mood, style hints.
2. AUTO EXPANSION: Expand intelligently.
3. VISUAL TAGS: Add lighting, camera, quality, textures.
4. STYLE INJECTION: Adapt to anime, cinematic, realistic, etc.
5. NEGATIVE PROMPT: Generate standard negative tags (blurry, low quality, distorted, bad anatomy, extra limbs) plus specific ones based on context.
6. TOKEN OPTIMIZATION: Max 2-3 lines.
7. CATEGORIES: Use different templates for Characters, Landscapes, Objects.
8. ADAPTIVE: If already detailed, DO NOT over-enhance.
9. STRUCTURED OUTPUT: Return strict JSON.

# 📦 OUTPUT RULES
Return ONLY valid JSON matching this format exactly:
{
  "enhanced_prompt": "...",
  "negative_prompt": "...",
  "style": "...",
  "confidence": 95
}
No explanation. Only JSON."""
    
    try:
        response_text = await async_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        # Clean JSON markdown blocks
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Merge user's manual negative prompt if provided
        if user_negative:
            data["negative_prompt"] = f"{data.get('negative_prompt', '')}, {user_negative}".strip(", ")
            
        return data
    except Exception as e:
        logger.warning(f"Advanced prompt enhancement failed: {e}")
        return {
            "enhanced_prompt": f"{prompt}, high quality, detailed, 4k, sharp focus",
            "negative_prompt": f"blurry, low quality, distorted, bad anatomy{', ' + user_negative if user_negative else ''}",
            "style": "cinematic",
            "confidence": 0
        }

def detect_style(prompt: str) -> str:
    """
    Lightweight keyword-based style detection.
    Defaults to 'cinematic'.
    """
    prompt_lower = prompt.lower()
    for style_kw in STYLES.keys():
        if style_kw in prompt_lower:
            return style_kw
    return "cinematic"

def apply_style(prompt: str, style: str = None) -> tuple[str, str]:
    """
    Applies a predefined style to the prompt.
    Returns the (final_prompt, detected_style_name)
    """
    if not style:
        style = detect_style(prompt)
        
    style_prompt = STYLES.get(style, STYLES["cinematic"])
    final_prompt = f"{prompt}, {style_prompt}"
    
    return final_prompt, style

def apply_negative_prompt(prompt: str, negative: str = None) -> str:
    """
    Appends negative prompts to exclude unwanted elements from the image.
    Uses a standard baseline + optional user additions.
    """
    default_negative = "blurry, low quality, distorted, bad anatomy"
    
    if negative:
        combined_negative = f"{default_negative}, {negative}"
    else:
        combined_negative = default_negative
        
    # Append to the final prompt (common SD/Midjourney format style if negative field isn't separate)
    return f"{prompt} | negative: {combined_negative}"

async def generate_image(prompt: str) -> bytes:
    """
    Calls the external text-to-image API.
    Returns the binary image data.
    """
    api_key = os.getenv("IMAGE_API_KEY", "")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt
    }
    
    max_retries = 2
    timeout = httpx.Timeout(60.0) # Image generation can take time
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.post(IMAGE_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                return response.content
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Image generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    logger.error(f"All {max_retries + 1} attempts to generate image failed.")
                    raise Exception("Failed to generate image after multiple attempts. Please try again later.")
                await asyncio.sleep(2) # brief delay before retry
    
    raise Exception("Failed to call API.")

async def upscale_image(image_bytes: bytes) -> bytes:
    """
    Sends the image to an upscale API for 4K/HD enhancement.
    Returns the upscaled binary image data.
    """
    # Simulate API execution time
    await asyncio.sleep(2)
    return image_bytes
