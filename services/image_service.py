import os
import logging
import httpx
import asyncio

logger = logging.getLogger(__name__)

IMAGE_API_URL = "https://fixpix-image.bcjqxt9wn8.workers.dev/"

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
