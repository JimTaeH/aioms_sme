"""
API Router for handling incoming LINE Webhooks.
Implements signature verification and asynchronous task dispatching.
"""
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
import logging

from backend.core.config import settings
from backend.services.task_dispatcher import TaskDispatcherService

logger = logging.getLogger(__name__)

# Initialize router and LINE parser
router = APIRouter()
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

@router.post("/webhook")
async def line_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None, alias="x-line-signature")
):
    """
    Endpoint to receive webhook events from the LINE Platform.
    
    Args:
        request (Request): The raw FastAPI request object.
        background_tasks (BackgroundTasks): FastAPI background task manager.
        x_line_signature (str): The signature header provided by LINE for verification.
        
    Returns:
        dict: A simple {"status": "ok"} response indicating successful receipt.
    """
    if x_line_signature is None:
        raise HTTPException(status_code=400, detail="Missing x-line-signature header")

    # Read the raw body as text for verification
    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        # Parse and verify the signature simultaneously using line-bot-sdk
        events = parser.parse(body_text, x_line_signature)
    except InvalidSignatureError:
        logger.warning("Invalid LINE signature detected. Rejecting request.")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error parsing webhook body: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Process each event asynchronously without blocking the response
    for event in events:
        # Convert the event object to a dictionary for serialization
        event_dict = event.to_dict()
        
        # Dispatch to the worker queue using FastAPI's BackgroundTasks as an immediate bridge
        # In a fully split architecture, this sends data to Redis via TaskDispatcherService
        background_tasks.add_task(TaskDispatcherService.dispatch_line_event, event_dict)

    # Respond to LINE platform immediately with 200 OK
    return {"status": "ok"}