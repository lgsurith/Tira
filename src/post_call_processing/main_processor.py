"""
Main post-call processor orchestrator.
"""

import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .services.gcs_service import GCSService
from .services.transcription_service import TranscriptionService
from .services.analysis_service import AnalysisService
from .services.supabase_service import SupabaseService
from .models.call_data import CallData, RiskAnalysis, BotPerformance

logger = logging.getLogger(__name__)


class PostCallProcessor:
    """Main orchestrator for post-call processing pipeline."""
    
    def __init__(self):
        """Initialize the post-call processor with all services."""
        try:
            # Initialize services
            self.gcs_service = GCSService(
                bucket_name=os.getenv("GCS_BUCKET", "riverline-agent"),
                credentials_path="key.json"
            )
            self.transcription_service = TranscriptionService()
            self.analysis_service = AnalysisService()
            self.supabase_service = SupabaseService()
            
            logger.info("Post-call processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize post-call processor: {e}")
            raise
    
    async def process_call(self, room_id: str, customer_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Process a completed call through the full pipeline.
        
        Args:
            room_id: LiveKit room ID
            customer_context: Optional customer context data
            
        Returns:
            Call ID if successful, None if failed
        """
        start_time = time.time()
        call_data = None
        
        try:
            logger.info(f"Starting post-call processing for room: {room_id}")
            
            # Create call data object
            call_data = CallData(
                room_id=room_id,
                customer_context=customer_context,
                processing_status="processing"
            )
            
            # Step 1: Download recording from GCS
            logger.info("Step 1: Downloading recording from GCS")
            local_file_path = self.gcs_service.download_recording(room_id)
            
            if not local_file_path:
                logger.error(f"No recording found for room {room_id}")
                call_data.processing_status = "failed"
                await self._store_failed_call(call_data, "No recording found")
                return None
            
            # Get recording info
            recording_info = self.gcs_service.get_recording_info(room_id)
            if recording_info:
                call_data.gcs_recording_path = recording_info["gcs_path"]
                call_data.recording_duration_seconds = recording_info.get("size_bytes", 0) / 1000.0  # Rough estimate
            
            # Step 2: Transcribe with AssemblyAI
            logger.info("Step 2: Transcribing with AssemblyAI")
            transcription_result = self.transcription_service.transcribe_file(
                local_file_path, 
                enable_speaker_diarization=True
            )
            
            if not transcription_result:
                logger.error(f"Transcription failed for room {room_id}")
                call_data.processing_status = "failed"
                await self._store_failed_call(call_data, "Transcription failed")
                return None
            
            # Update call data with transcription results
            call_data.assembly_ai_transcript_id = transcription_result["transcript_id"]
            call_data.transcript_segments = transcription_result["segments"]
            
            # Step 3: Analyze for risk and bot performance
            logger.info("Step 3: Analyzing transcript")
            call_data.risk_analysis = self.analysis_service.analyze_risk(call_data.transcript_segments)
            call_data.bot_performance = self.analysis_service.analyze_bot_performance(call_data.transcript_segments)
            
            # Generate improvement suggestions
            call_data.improvement_suggestions = self.analysis_service.generate_improvement_suggestions(
                call_data.risk_analysis, 
                call_data.bot_performance
            )
            
            # Calculate LLM judge score (simple average for now)
            call_data.llm_judge_score = self._calculate_llm_judge_score(call_data)
            
            # Step 4: Store in Supabase
            logger.info("Step 4: Storing results in Supabase")
            call_data.processing_status = "completed"
            call_data.total_processing_time = time.time() - start_time
            
            call_id = self.supabase_service.store_call_data(call_data)
            
            if call_id:
                logger.info(f"Successfully processed call {room_id} with ID: {call_id}")
                logger.info(f"Risk Level: {call_data.risk_analysis.risk_level}")
                logger.info(f"Risk Score: {call_data.risk_analysis.risk_score:.2f}")
                logger.info(f"Bot Performance Score: {call_data.llm_judge_score:.2f}")
                return call_id
            else:
                logger.error(f"Failed to store call data for room {room_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing call {room_id}: {e}")
            if call_data:
                call_data.processing_status = "failed"
                await self._store_failed_call(call_data, str(e))
            return None
        
        finally:
            # Clean up temporary file
            if 'local_file_path' in locals() and local_file_path and os.path.exists(local_file_path):
                try:
                    os.remove(local_file_path)
                    logger.info(f"Cleaned up temporary file: {local_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
    
    async def _store_failed_call(self, call_data: CallData, error_message: str) -> None:
        """Store failed call data for debugging."""
        try:
            call_data.improvement_suggestions = [f"Processing failed: {error_message}"]
            self.supabase_service.store_call_data(call_data)
        except Exception as e:
            logger.error(f"Failed to store failed call data: {e}")
    
    def _calculate_llm_judge_score(self, call_data: CallData) -> float:
        """
        Calculate overall LLM judge score (0-1, higher is better).
        
        Args:
            call_data: CallData object with analysis results
            
        Returns:
            LLM judge score
        """
        if not call_data.bot_performance:
            return 0.0
        
        # Weight different performance metrics
        weights = {
            'repetition': 0.2,      # Lower repetition is better
            'negotiation': 0.2,     # More negotiation attempts is better
            'relevance': 0.3,       # Higher relevance is better
            'flow': 0.2,            # Better flow is better
            'professional': 0.1     # Professional behavior is better
        }
        
        # Calculate weighted score
        repetition_score = 1.0 - call_data.bot_performance.repetition_score  # Invert repetition
        negotiation_score = min(1.0, call_data.bot_performance.negotiation_attempts / 3.0)  # Normalize to 3 attempts
        relevance_score = call_data.bot_performance.relevance_score
        flow_score = call_data.bot_performance.conversation_flow_score
        professional_score = 1.0 if call_data.bot_performance.professional_maintained else 0.0
        
        total_score = (
            weights['repetition'] * repetition_score +
            weights['negotiation'] * negotiation_score +
            weights['relevance'] * relevance_score +
            weights['flow'] * flow_score +
            weights['professional'] * professional_score
        )
        
        return min(1.0, max(0.0, total_score))
    
    async def process_pending_calls(self) -> int:
        """
        Process any pending calls in the database.
        
        Returns:
            Number of calls processed
        """
        try:
            # Get pending calls
            pending_calls = self.supabase_service.get_calls_by_status("pending")
            
            if not pending_calls:
                logger.info("No pending calls to process")
                return 0
            
            logger.info(f"Found {len(pending_calls)} pending calls to process")
            
            processed_count = 0
            for call in pending_calls:
                room_id = call["room_id"]
                customer_context = call.get("customer_context")
                
                logger.info(f"Processing pending call: {room_id}")
                
                # Update status to processing
                self.supabase_service.update_call_status(call["id"], "processing")
                
                # Process the call
                result = await self.process_call(room_id, customer_context)
                
                if result:
                    processed_count += 1
                    logger.info(f"Successfully processed pending call: {room_id}")
                else:
                    logger.error(f"Failed to process pending call: {room_id}")
                    self.supabase_service.update_call_status(call["id"], "failed")
            
            logger.info(f"Processed {processed_count} pending calls")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing pending calls: {e}")
            return 0
    
    def get_call_summary(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of call processing results.
        
        Args:
            room_id: LiveKit room ID
            
        Returns:
            Call summary dictionary or None if not found
        """
        try:
            # Get call data
            call_data = self.supabase_service.get_call_by_room_id(room_id)
            if not call_data:
                return None
            
            # Get transcripts from the full_transcript JSON
            transcripts = self.supabase_service.get_full_transcript_by_room_id(room_id)
            
            # Get analysis
            analysis = self.supabase_service.get_call_analysis(call_data["id"])
            
            # Create summary
            summary = {
                "room_id": room_id,
                "call_id": call_data["id"],
                "status": call_data["call_status"],
                "created_at": call_data["created_at"],
                "recording_duration": call_data.get("recording_duration_seconds"),
                "transcript_segments": len(transcripts),
                "processing_time": call_data.get("total_processing_time"),
                "risk_analysis": analysis.get("risk_flags", {}) if analysis else {},
                "bot_performance": analysis.get("bot_performance", {}) if analysis else {},
                "llm_judge_score": analysis.get("llm_judge_score") if analysis else None,
                "improvement_suggestions": analysis.get("improvement_suggestions", []) if analysis else []
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting call summary for {room_id}: {e}")
            return None
