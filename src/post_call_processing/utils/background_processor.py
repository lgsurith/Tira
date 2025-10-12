"""
Background processor for handling post-call processing asynchronously.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from ..main_processor import PostCallProcessor

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """Background processor for handling post-call processing tasks."""
    
    def __init__(self):
        """Initialize background processor."""
        self.processor = PostCallProcessor()
        self._running_tasks = set()
    
    async def process_call_async(self, room_id: str, customer_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Process a call in the background.
        
        Args:
            room_id: LiveKit room ID
            customer_context: Optional customer context data
        """
        try:
            logger.info(f"Starting background processing for room: {room_id}")
            
            # Create task and add to running tasks
            task = asyncio.create_task(
                self.processor.process_call(room_id, customer_context)
            )
            self._running_tasks.add(task)
            
            # Add callback to remove task when done
            task.add_done_callback(self._running_tasks.discard)
            
            # Wait for completion
            result = await task
            
            if result:
                logger.info(f"Background processing completed for room {room_id}, call_id: {result}")
            else:
                logger.error(f"Background processing failed for room {room_id}")
                
        except Exception as e:
            logger.error(f"Error in background processing for room {room_id}: {e}")
    
    def process_call_sync(self, room_id: str, customer_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Process a call synchronously (for use in non-async contexts).
        
        Args:
            room_id: LiveKit room ID
            customer_context: Optional customer context data
        """
        try:
            # Run in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(
                    self.process_call_async(room_id, customer_context)
                )
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in sync processing for room {room_id}: {e}")
    
    async def process_pending_calls_async(self) -> int:
        """
        Process pending calls in the background.
        
        Returns:
            Number of calls processed
        """
        try:
            logger.info("Starting background processing of pending calls")
            result = await self.processor.process_pending_calls()
            logger.info(f"Background processing of pending calls completed: {result} calls processed")
            return result
        except Exception as e:
            logger.error(f"Error in background processing of pending calls: {e}")
            return 0
    
    def process_pending_calls_sync(self) -> int:
        """
        Process pending calls synchronously.
        
        Returns:
            Number of calls processed
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.process_pending_calls_async()
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in sync processing of pending calls: {e}")
            return 0
    
    def get_call_summary(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get call summary (synchronous).
        
        Args:
            room_id: LiveKit room ID
            
        Returns:
            Call summary dictionary or None if not found
        """
        return self.processor.get_call_summary(room_id)
    
    def get_running_tasks_count(self) -> int:
        """
        Get the number of currently running background tasks.
        
        Returns:
            Number of running tasks
        """
        return len(self._running_tasks)
    
    async def wait_for_all_tasks(self) -> None:
        """Wait for all running background tasks to complete."""
        if self._running_tasks:
            logger.info(f"Waiting for {len(self._running_tasks)} background tasks to complete")
            await asyncio.gather(*self._running_tasks, return_exceptions=True)
            logger.info("All background tasks completed")
