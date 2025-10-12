"""
Data models for call analysis and processing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class TranscriptSegment:
    """Individual transcript segment with speaker information."""
    speaker: str  # 'agent' or 'customer'
    text: str
    start_time: float  # seconds from start
    end_time: float
    confidence: Optional[float] = None
    words: Optional[List[Dict[str, Any]]] = None


@dataclass
class RiskAnalysis:
    """Risk analysis results for a call."""
    payment_agreed: bool = False
    payment_refused: bool = False
    financial_hardship_mentioned: bool = False
    dispute_raised: bool = False
    bankruptcy_mentioned: bool = False
    abusive_language: bool = False
    wrong_number: bool = False
    callback_requested: bool = False
    payment_plan_requested: bool = False
    risk_score: float = 0.0  # 0-1 scale
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH


@dataclass
class BotPerformance:
    """Bot performance metrics for a call."""
    repetition_score: float = 0.0  # 0-1, lower is better
    negotiation_attempts: int = 0
    relevance_score: float = 0.0  # 0-1, higher is better
    conversation_flow_score: float = 0.0  # 0-1, higher is better
    empathy_shown: bool = False
    professional_maintained: bool = True
    call_terminated_appropriately: bool = True


@dataclass
class CallData:
    """Complete call data structure."""
    room_id: str
    customer_context: Optional[Dict[str, Any]] = None
    gcs_recording_path: Optional[str] = None
    recording_duration_seconds: Optional[float] = None
    call_status: str = "completed"
    assembly_ai_transcript_id: Optional[str] = None
    
    # Processing results
    transcript_segments: List[TranscriptSegment] = field(default_factory=list)
    risk_analysis: Optional[RiskAnalysis] = None
    bot_performance: Optional[BotPerformance] = None
    llm_judge_score: Optional[float] = None
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    processing_status: str = "pending"  # pending, processing, completed, failed
    total_processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        # Convert transcript segments to JSON format
        transcript_json = []
        for segment in self.transcript_segments:
            transcript_json.append({
                "speaker": segment.speaker,
                "text": segment.text,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "confidence": segment.confidence
            })
        
        return {
            "room_id": self.room_id,
            "customer_context": self.customer_context,
            "gcs_recording_path": self.gcs_recording_path,
            "recording_duration_seconds": self.recording_duration_seconds,
            "call_status": self.call_status,
            "assembly_ai_transcript_id": self.assembly_ai_transcript_id,
            "full_transcript": transcript_json,  # Store complete transcript as JSON
        }
