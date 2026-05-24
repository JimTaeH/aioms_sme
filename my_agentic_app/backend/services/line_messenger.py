"""
Asynchronous LINE messenger service using official line-bot-sdk.
Handles sending replies and push messages back to the LINE platform.
"""
import logging
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage
)
from backend.core.config import settings

logger = logging.getLogger(__name__)

class LineMessengerService:
    """
    Service to interact with the LINE Messaging API asynchronously via SDK.
    """
    
    @staticmethod
    async def send_reply(reply_token: str, text: str) -> None:
        """
        Sends a text reply message back to the user via LINE Messaging API.
        
        Args:
            reply_token (str): The token received from the webhook event.
            text (str): The message content to send back.
        """
        # 1. Validate the text to prevent LINE API 400 Bad Request
        # LLMs might sometimes return empty strings or unexpected types
        if not text or not isinstance(text, str) or text.strip() == "":
            logger.warning(f"Invalid or empty text received from agent: {text}. Using fallback message.")
            text = "ขออภัยครับ ระบบประมวลผลข้อความผิดพลาด (Empty Response from AI)"

        # 2. Configure the SDK
        configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
        
        # 3. Use AsyncApiClient for non-blocking HTTP execution
        async with AsyncApiClient(configuration) as api_client:
            line_bot_api = AsyncMessagingApi(api_client)
            
            # Build the request object cleanly using SDK models
            request = ReplyMessageRequest(
                replyToken=reply_token,
                messages=[TextMessage(text=text)]
            )
            
            try:
                await line_bot_api.reply_message(request)
                logger.info(f"Successfully sent LINE reply via SDK to token: {reply_token}")
            except Exception as e:
                logger.error(f"Failed to send LINE reply via SDK: {str(e)}")
                raise