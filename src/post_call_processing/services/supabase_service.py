"""
Supabase service for storing call analysis data.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from ..models.call_data import CallData, TranscriptSegment

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for interacting with Supabase database."""
    
    def __init__(self, url: Optional[str] = None, service_role_key: Optional[str] = None):
        """
        Initialize Supabase service.
        
        Args:
            url: Supabase project URL
            service_role_key: Supabase service role key
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.service_role_key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_role_key:
            raise ValueError("Supabase URL and service role key are required")
        
        self.client: Client = create_client(self.url, self.service_role_key)
        logger.info("Supabase client initialized successfully")
    
    def store_call_data(self, call_data: CallData) -> Optional[str]:
        """
        Store call data in Supabase.
        
        Args:
            call_data: CallData object to store
            
        Returns:
            Call ID if successful, None if failed
        """
        try:
            # Store main call record
            call_record = call_data.to_dict()
            call_record["created_at"] = call_data.created_at.isoformat()
            
            result = self.client.table("calls").insert(call_record).execute()
            
            if not result.data:
                logger.error("Failed to insert call record")
                return None
            
            call_id = result.data[0]["id"]
            logger.info(f"Stored call record with ID: {call_id}")
            
            # Transcript is now stored as JSON in the main call record
            # No need to store separate transcript segments
            
            # Store call analysis
            if call_data.risk_analysis or call_data.bot_performance:
                self._store_call_analysis(call_id, call_data)
            
            return call_id
            
        except Exception as e:
            logger.error(f"Error storing call data: {e}")
            return None
    
    def _store_transcript_segments(self, call_id: str, segments: List[TranscriptSegment]) -> bool:
        """
        Store transcript segments in database.
        
        Args:
            call_id: Call ID
            segments: List of transcript segments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            segment_records = []
            for segment in segments:
                record = {
                    "call_id": call_id,
                    "speaker": segment.speaker,
                    "text": segment.text,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "confidence": segment.confidence,
                    "words": segment.words
                }
                segment_records.append(record)
            
            result = self.client.table("call_transcripts").insert(segment_records).execute()
            
            if result.data:
                logger.info(f"Stored {len(segments)} transcript segments")
                return True
            else:
                logger.error("Failed to store transcript segments")
                return False
                
        except Exception as e:
            logger.error(f"Error storing transcript segments: {e}")
            return False
    
    def _store_call_analysis(self, call_id: str, call_data: CallData) -> bool:
        """
        Store call analysis in database.
        
        Args:
            call_id: Call ID
            call_data: CallData object with analysis results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            analysis_record = {
                "call_id": call_id,
                "risk_flags": call_data.risk_analysis.__dict__ if call_data.risk_analysis else {},
                "bot_performance": call_data.bot_performance.__dict__ if call_data.bot_performance else {},
                "llm_judge_score": call_data.llm_judge_score,
                "improvement_suggestions": call_data.improvement_suggestions,
                "processing_status": call_data.processing_status,
                "total_processing_time": call_data.total_processing_time
            }
            
            result = self.client.table("call_analysis").insert(analysis_record).execute()
            
            if result.data:
                logger.info("Stored call analysis")
                return True
            else:
                logger.error("Failed to store call analysis")
                return False
                
        except Exception as e:
            logger.error(f"Error storing call analysis: {e}")
            return False
    
    def get_call_by_room_id(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get call data by room ID.
        
        Args:
            room_id: LiveKit room ID
            
        Returns:
            Call data dictionary or None if not found
        """
        try:
            result = self.client.table("calls").select("*").eq("room_id", room_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                logger.info(f"No call found for room_id: {room_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting call by room_id {room_id}: {e}")
            return None
    
    def get_full_transcript_by_room_id(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Get full transcript by room ID.
        
        Args:
            room_id: LiveKit room ID
            
        Returns:
            List of transcript segment dictionaries
        """
        try:
            result = self.client.table("calls").select("full_transcript").eq("room_id", room_id).execute()
            
            if result.data and result.data[0].get("full_transcript"):
                transcript_data = result.data[0]["full_transcript"]
                logger.info(f"Retrieved transcript for room {room_id} with {len(transcript_data)} segments")
                return transcript_data
            else:
                logger.info(f"No transcript found for room_id: {room_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting transcript for room_id {room_id}: {e}")
            return []
    
    def get_call_transcripts(self, call_id: str) -> List[Dict[str, Any]]:
        """
        Get transcript segments for a call from the full_transcript JSON.
        
        Args:
            call_id: Call ID
            
        Returns:
            List of transcript segment dictionaries
        """
        try:
            # Get the full_transcript JSON from the calls table
            result = self.client.table("calls").select("full_transcript").eq("id", call_id).execute()
            
            if result.data and result.data[0].get("full_transcript"):
                transcript_data = result.data[0]["full_transcript"]
                logger.info(f"Retrieved transcript with {len(transcript_data)} segments")
                return transcript_data
            else:
                logger.info(f"No transcript found for call_id: {call_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting transcripts for call_id {call_id}: {e}")
            return []
    
    def get_call_analysis(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get call analysis for a call.
        
        Args:
            call_id: Call ID
            
        Returns:
            Call analysis dictionary or None if not found
        """
        try:
            result = self.client.table("call_analysis").select("*").eq("call_id", call_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                logger.info(f"No analysis found for call_id: {call_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting analysis for call_id {call_id}: {e}")
            return None
    
    def update_call_status(self, call_id: str, status: str) -> bool:
        """
        Update call processing status.
        
        Args:
            call_id: Call ID
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table("calls").update({"call_status": status}).eq("id", call_id).execute()
            
            if result.data:
                logger.info(f"Updated call {call_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update call {call_id} status")
                return False
                
        except Exception as e:
            logger.error(f"Error updating call status: {e}")
            return False
    
    def update_analysis_status(self, call_id: str, status: str) -> bool:
        """
        Update call analysis processing status.
        
        Args:
            call_id: Call ID
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table("call_analysis").update({"processing_status": status}).eq("call_id", call_id).execute()
            
            if result.data:
                logger.info(f"Updated analysis {call_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update analysis {call_id} status")
                return False
                
        except Exception as e:
            logger.error(f"Error updating analysis status: {e}")
            return False
    
    def get_recent_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent calls for monitoring.
        
        Args:
            limit: Number of calls to retrieve
            
        Returns:
            List of call dictionaries
        """
        try:
            result = self.client.table("calls").select("*").order("created_at", desc=True).limit(limit).execute()
            
            if result.data:
                logger.info(f"Retrieved {len(result.data)} recent calls")
                return result.data
            else:
                logger.info("No recent calls found")
                return []
                
        except Exception as e:
            logger.error(f"Error getting recent calls: {e}")
            return []
    
    def get_calls_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get calls by processing status.
        
        Args:
            status: Processing status to filter by
            
        Returns:
            List of call dictionaries
        """
        try:
            result = self.client.table("calls").select("*").eq("call_status", status).execute()
            
            if result.data:
                logger.info(f"Retrieved {len(result.data)} calls with status {status}")
                return result.data
            else:
                logger.info(f"No calls found with status {status}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting calls by status {status}: {e}")
            return []
