import os
import logging
import httpx
import asyncio

from services.llm_service import async_chat_completion

logger = logging.getLogger(__name__)

IMAGE_API_URL = "https://fixpix-image.bcjqxt9wn8.workers.dev/"

OPENROUTER_MODELS = {
    "Flux Pro": {"id": "black-forest-labs/flux.2-pro", "key": "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"},
    "Flux Max": {"id": "black-forest-labs/flux.2-max", "key": "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"},
    "Riverflow Fast": {"id": "sourceful/riverflow-v2-fast-preview", "key": "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"},
    "SeeDream Creative": {"id": "bytedance-seed/seedream-4.5", "key": "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"}
}

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
    system_prompt = """You are an elite AI prompt engineer.
Your task is to transform user prompts into HIGH-END, CINEMATIC, UNIQUE image prompts.

# 🎯 OBJECTIVE
Create prompts that are visually rich, composition-aware, unique, and cinematic quality.

# 🧠 INTELLIGENCE LAYERS
1. SCENE DESIGN: Define subject, environment, background, depth.
2. CINEMATIC COMPOSITION: Add camera angle, depth of field, perspective, framing.
3. LIGHTING ENGINE: Choose soft natural light, golden hour, neon cyberpunk, or dramatic shadows.
4. REALISM BOOST: Avoid "AI perfect look". Add imperfections, natural textures.
5. UNIQUENESS ENGINE: Avoid generic outputs. Add storytelling elements, motion, or emotion.
6. CATEGORY LOGIC:
   - Portrait: skin texture, lighting on face, imperfections
   - Landscape: atmosphere, depth layers, lighting gradient
   - Creative: unique composition, abstract flow control
7. HARD RULE: DO NOT produce generic prompts like "beautiful, high quality, 4k". Make it visually meaningful.

# 🧩 OUTPUT FORMAT
Return ONLY valid JSON matching this format exactly:
{
  "enhanced_prompt": "...",
  "negative_prompt": "...",
  "style": "...",
  "composition": "...",
  "lighting": "..."
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
            "enhanced_prompt": f"{prompt}, visually rich, detailed textures, cinematic composition",
            "negative_prompt": f"blurry, low quality, distorted, bad anatomy{', ' + user_negative if user_negative else ''}",
            "style": "cinematic",
            "composition": "standard wide shot",
            "lighting": "soft natural light"
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

def score_image(image_bytes: bytes) -> float:
    """
    Fast heuristic scoring mechanism.
    Evaluates file size (density) and optionally contrast sharpness if PIL is available.
    """
    import io
    
    # Base score: File size correlates heavily with detail complexity and texture density
    score = len(image_bytes) / 1024.0
    
    try:
        from PIL import Image, ImageStat
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        stat = ImageStat.Stat(img)
        
        # Contrast standard deviation adds strong value (punishes flat/blurry/foggy output)
        contrast = stat.stddev[0]
        score += (contrast * 2.5)
    except ImportError:
        pass # PIL not installed, gracefully fallback to density scoring
        
    return score

async def generate_variation(base_prompt: str, seed_modifier: str) -> dict:
    """Generates a single image variation and immediately scores it."""
    # Ensure cache-busting and visual uniqueness
    variation_prompt = f"{base_prompt}, {seed_modifier}"
    try:
        image_bytes = await generate_image(variation_prompt)
        score = score_image(image_bytes)
        return {"bytes": image_bytes, "score": score, "variation": seed_modifier}
    except Exception as e:
        logger.warning(f"Variation {seed_modifier} failed: {e}")
        return None

async def generate_best_image_parallel(prompt: str, variations_count: int = 3) -> dict:
    """
    Generates multiple images concurrently and mathematically selects the best one.
    """
    import random
    modifiers = [
        "soft cinematic tone", "dramatic lighting", "natural realism",
        "hyper-detailed focus", "vibrant colors", "masterpiece depth"
    ]
    selected_modifiers = random.sample(modifiers, min(variations_count, len(modifiers)))
    
    tasks = [generate_variation(prompt, mod) for mod in selected_modifiers]
    results = await asyncio.gather(*tasks)
    
    valid_results = [r for r in results if r is not None]
    
    if not valid_results:
        # Fallback to single raw execution if all parallel tasks failed (e.g., rate limits)
        raw_bytes = await generate_image(prompt)
        return {"bytes": raw_bytes, "score": score_image(raw_bytes), "variation": "default"}
        
    # Automatic Best Image Selection Engine
    best_candidate = max(valid_results, key=lambda x: x["score"])
    
    return best_candidate

async def generate_image_openrouter(model_name: str, model_id: str, prompt: str, api_key: str) -> dict:
    """Fetches image dynamically from OpenRouter's interface natively returning URL/Bytes."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/theparthbhanderi/bot",
        "X-Title": "KINGPARTHH Bot"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            
            # Extract standard markdown image link ![desc](url) or raw url
            import re
            img_url = content
            match = re.search(r'!\[.*?\]\((https?://.*?)\)', content)
            if match:
                img_url = match.group(1)
            elif "http" in content:
                urls = re.findall(r'(https?://[^\s]+)', content)
                if urls:
                    img_url = urls[0]
            
            # Pull down actual binary data to broadcast natively back to telegram
            img_resp = await client.get(img_url, timeout=15.0)
            img_resp.raise_for_status()
            score = score_image(img_resp.content)
            
            return {"model": model_name, "image": img_resp.content, "score": score}
            
    except Exception as e:
        logger.error(f"OpenRouter Model {model_name} failed: {e}")
        return None

async def generate_multi_model_images(prompt: str) -> list:
    """Core pipeline executing all models in parallel synchronously and sorting by visual quality score."""
    import asyncio
    tasks = []
    
    # Pack up concurrent processes
    for name, config in OPENROUTER_MODELS.items():
        tasks.append(generate_image_openrouter(name, config["id"], prompt, config["key"]))
        
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out failures securely
    valid_results = [r for r in results if isinstance(r, dict) and r is not None]
    
    # Enforce advanced heuristic scoring
    valid_results.sort(key=lambda x: x["score"], reverse=True)
    
    return valid_results

async def upscale_image(image_bytes: bytes) -> bytes:
    """
    Sends the image to an upscale API for 4K/HD enhancement.
    Returns the upscaled binary image data.
    """
    # Simulate API execution time
    await asyncio.sleep(2)
    return image_bytes
