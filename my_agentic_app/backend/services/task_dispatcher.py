"""
Service module responsible for dispatching background tasks to the worker queue.
Ensures the Gateway remains non-blocking.
"""
import logging
from backend.services.agent_worker import AgentWorkerService

logger = logging.getLogger(__name__)

class TaskDispatcherService:
    """
    Handles routing of incoming LINE events to the asynchronous task queue or worker thread.
    """
    
    @staticmethod
    async def dispatch_line_event(event_data: dict) -> None:
        """
        Forwards the LINE event payload to the asynchronous execution worker.
        Since this runs inside FastAPI's BackgroundTasks, it does not block the webhook HTTP response.
        
        Args:
            event_data (dict): The dictionary representation of the LINE event.
        """
        try:
            # Directly hand off execution to the asynchronous agent worker.
            await AgentWorkerService.process_line_event(event_data)
            
        except Exception as e:
            logger.error(f"Failed to dispatch task to worker: {str(e)}")
            raise