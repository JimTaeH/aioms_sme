# Parser Tools: extract data from slip images / documents
"""
Parsing and OCR tools for the AI agent.
Handles downloading image content from LINE and processing it via Typhoon-OCR.
"""
import os
import httpx
import logging
from langchain_core.tools import tool
from linebot.v3.messaging import AsyncApiClient, AsyncMessagingApi, Configuration, AsyncMessagingApiBlob
from backend.core.config import settings

logger = logging.getLogger(__name__)

@tool
async def extract_slip_data(message_id: str) -> str:
    """
    Downloads an image message from LINE and extracts text/slip data using Typhoon-OCR.
    Use this tool ONLY when the user uploads an image and provides a message_id.
    
    Args:
        message_id (str): The LINE message ID of the image uploaded by the user.
        
    Returns:
        str: The extracted JSON data or text from the OCR process.
    """
    # 1. Initialize LINE SDK to fetch the image content
    configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
    image_bytes = b""
    
    try:
        async with AsyncApiClient(configuration) as api_client:
            line_bot_blob_api = AsyncMessagingApiBlob(api_client)
            # Fetch the raw binary data of the image from LINE servers
            image_bytes = await line_bot_blob_api.get_message_content(message_id)
            logger.info(f"Successfully downloaded image {message_id} from LINE.")
    except Exception as e:
        logger.error(f"Failed to download image {message_id}: {str(e)}")
        return "Error: Could not retrieve the image from LINE."

    # 2. Send the image to Typhoon-OCR API
    # Replace 'TYPHOON_API_URL' and headers with your actual Typhoon configuration
    typhoon_url = os.getenv("TYPHOON_OCR_API_URL", "https://api.opentyphoon.ai/v1/ocr")
    typhoon_api_key = os.getenv("TYPHOON_API_KEY", "")
    
    if not typhoon_api_key:
        return "System Error: Typhoon OCR API Key is not configured."

    headers = {
        "Authorization": f"Bearer {typhoon_api_key}"
    }
    
    # Using a Multipart form-data upload for the image bytes
    files = {"file": ("slip.jpg", image_bytes, "image/jpeg")}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            ocr_response = await client.post(typhoon_url, headers=headers, files=files)
            ocr_response.raise_for_status()
            
            # Assuming Typhoon returns JSON with an 'extracted_text' or similar field
            result_data = ocr_response.json()
            extracted_text = result_data.get("text", str(result_data))
            
            return f"OCR Extraction Successful. Data found: {extracted_text}"
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Typhoon API error: {e.response.text}")
            return f"Error from OCR engine: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error connecting to Typhoon OCR: {str(e)}")
            return "Error: Failed to process the image with OCR."
