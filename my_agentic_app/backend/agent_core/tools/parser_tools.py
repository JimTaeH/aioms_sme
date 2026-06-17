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

from backend.services.document_service import DocumentService
from backend.schemas.tool_schemas import ExtractSlipDataInput

logger = logging.getLogger(__name__)

@tool(args_schema=ExtractSlipDataInput)
async def extract_slip_data(message_id: str, line_user_id: str) -> str:
    """
    Downloads an image message from LINE, extracts text using Typhoon-OCR, and saves the record.
    Use this tool ONLY when the user uploads an image and provides a message_id and line_user_id.
    
    Args:
        message_id (str): The LINE message ID of the image.
        line_user_id (str): The LINE ID of the user who sent the image.
        
    Returns:
        str: The extracted text to answer the user.
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

    # Increased timeout to 60 seconds since OCR processes can be heavy
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            ocr_response = await client.post(typhoon_url, headers=headers, files=files)
            
            # Will raise httpx.HTTPStatusError for 4XX or 5XX status codes
            ocr_response.raise_for_status()
            
            # Read raw response first to prevent JSON decode crashes
            raw_text = ocr_response.text
            logger.debug(f"Raw OCR Response from Typhoon: {raw_text}")
            
            try:
                result_data = ocr_response.json()
                # Typhoon might return the text in different keys depending on the exact endpoint version
                extracted_text = result_data.get("text", str(result_data))

                await DocumentService.save_ocr_document(
                    line_user_id=line_user_id, 
                    message_id=message_id, 
                    extracted_data=result_data, 
                    status="completed"
                )

            except ValueError:
                # If the response is not valid JSON, fallback to using the raw text
                logger.warning("Typhoon OCR response is not a valid JSON. Using raw text.")
                extracted_text = raw_text
                # Save raw text if JSON parsing fails
                await DocumentService.save_ocr_document(
                    line_user_id=line_user_id, 
                    message_id=message_id, 
                    extracted_data={"raw_response": raw_text}, 
                    status="completed"
                )
            
            return f"OCR Extraction Successful. Data found: {extracted_text}"
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Typhoon API HTTP error: {e.response.status_code} - {e.response.text}")
            return f"Error from OCR engine: HTTP {e.response.status_code}"
            
        except httpx.RequestError as e:
            # Captures TimeoutException, ConnectionError, etc.
            logger.error(f"Typhoon API Network/Timeout error: {str(e)}")
            return "Error: Network timeout or connection failed with OCR service."
            
        except Exception as e:
            # Catch-all for any other unexpected errors
            logger.error(f"Unexpected error in OCR processing: {str(e)}")
            return f"Error: Failed to process the image with OCR due to an internal error."
