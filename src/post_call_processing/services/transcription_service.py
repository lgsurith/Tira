"""
AssemblyAI transcription service with speaker diarization.
"""

import os
import time
import logging
from typing import List, Optional
import assemblyai as aai
from ..models.call_data import TranscriptSegment

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio files using AssemblyAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize transcription service.
        
        Args:
            api_key: AssemblyAI API key. If None, will use ASSEMBLY_AI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ASSEMBLY_AI_API_KEY")
        if not self.api_key:
            raise ValueError("AssemblyAI API key is required")
        
        # Configure AssemblyAI
        aai.settings.api_key = self.api_key
        self.transcriber = aai.Transcriber()
    
    def transcribe_file(self, file_path: str, enable_speaker_diarization: bool = True) -> Optional[dict]:
        """
        Transcribe an audio file with optional speaker diarization.
        
        Args:
            file_path: Path to the audio file
            enable_speaker_diarization: Whether to enable speaker diarization
            
        Returns:
            Dictionary with transcription results, or None if failed
        """
        try:
            logger.info(f"Starting transcription for file: {file_path}")
            start_time = time.time()
            
            # Configure transcription settings
            config = aai.TranscriptionConfig(
                speaker_labels=enable_speaker_diarization,
                speakers_expected=2,  # Agent and customer
                auto_highlights=True,
                sentiment_analysis=True,
                entity_detection=True,
                iab_categories=True
            )
            
            # Submit transcription job
            transcript = self.transcriber.transcribe(file_path, config=config)
            
            # Wait for completion
            while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
                time.sleep(1)
                transcript = self.transcriber.get_transcript(transcript.id)
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription failed: {transcript.error}")
                return None
            
            processing_time = time.time() - start_time
            logger.info(f"Transcription completed in {processing_time:.2f} seconds")
            
            # Extract results
            result = {
                "transcript_id": transcript.id,
                "full_text": transcript.text,
                "processing_time": processing_time,
                "confidence": transcript.confidence,
                "language_code": getattr(transcript, 'language_code', 'en'),
                "audio_duration": getattr(transcript, 'audio_duration', 0),
                "segments": self._extract_segments(transcript),
                "highlights": getattr(transcript, 'auto_highlights', []),
                "sentiment": getattr(transcript, 'sentiment_analysis_results', []),
                "entities": getattr(transcript, 'entities', []),
                "iab_categories": getattr(transcript, 'iab_categories_results', [])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing file {file_path}: {e}")
            return None
    
    def _extract_segments(self, transcript) -> List[TranscriptSegment]:
        """
        Extract transcript segments with speaker information.
        
        Args:
            transcript: AssemblyAI transcript object
            
        Returns:
            List of TranscriptSegment objects
        """
        segments = []
        
        try:
            if hasattr(transcript, 'utterances') and transcript.utterances:
                # Use utterances for speaker diarization
                for utterance in transcript.utterances:
                    segment = TranscriptSegment(
                        speaker=self._map_speaker_label(utterance.speaker),
                        text=utterance.text,
                        start_time=utterance.start / 1000.0,  # Convert ms to seconds
                        end_time=utterance.end / 1000.0,
                        confidence=utterance.confidence
                    )
                    segments.append(segment)
            else:
                # Fallback to word-level segments if utterances not available
                if hasattr(transcript, 'words') and transcript.words:
                    current_speaker = None
                    current_text = ""
                    start_time = 0
                    
                    for word in transcript.words:
                        if word.speaker != current_speaker:
                            # Save previous segment
                            if current_text.strip():
                                segment = TranscriptSegment(
                                    speaker=self._map_speaker_label(current_speaker),
                                    text=current_text.strip(),
                                    start_time=start_time / 1000.0,
                                    end_time=word.start / 1000.0,
                                    confidence=word.confidence
                                )
                                segments.append(segment)
                            
                            # Start new segment
                            current_speaker = word.speaker
                            current_text = word.text
                            start_time = word.start
                        else:
                            current_text += " " + word.text
                    
                    # Add final segment
                    if current_text.strip():
                        final_word = transcript.words[-1]
                        segment = TranscriptSegment(
                            speaker=self._map_speaker_label(current_speaker),
                            text=current_text.strip(),
                            start_time=start_time / 1000.0,
                            end_time=final_word.end / 1000.0,
                            confidence=final_word.confidence
                        )
                        segments.append(segment)
            
        except Exception as e:
            logger.error(f"Error extracting segments: {e}")
            # Fallback: create single segment with full text
            if transcript.text:
                segment = TranscriptSegment(
                    speaker="unknown",
                    text=transcript.text,
                    start_time=0.0,
                    end_time=transcript.audio_duration / 1000.0 if transcript.audio_duration else 0.0,
                    confidence=transcript.confidence
                )
                segments.append(segment)
        
        return segments
    
    def _map_speaker_label(self, speaker_label: str) -> str:
        """
        Map AssemblyAI speaker labels to our standard labels.
        
        Args:
            speaker_label: AssemblyAI speaker label (e.g., "A", "B", "SPEAKER_00")
            
        Returns:
            Mapped speaker label ("agent" or "customer")
        """
        if not speaker_label:
            return "unknown"
        
        # AssemblyAI typically uses "A", "B" or "SPEAKER_00", "SPEAKER_01"
        # Based on the actual conversation flow:
        # - Customer answers first: "Foreign. Hello?" (first speaker)
        # - Agent responds: "Hi, this is Tira calling from Riverline Bank..." (second speaker)
        # So the first speaker (A/SPEAKER_00) should be the customer, second speaker (B/SPEAKER_01) should be agent
        if speaker_label in ["A", "SPEAKER_00", "0"]:
            return "customer"  # First speaker is customer
        elif speaker_label in ["B", "SPEAKER_01", "1"]:
            return "agent"     # Second speaker is agent
        else:
            # Default mapping - first speaker is customer, second is agent
            return "customer" if "0" in str(speaker_label) else "agent"
    
    def get_transcript_status(self, transcript_id: str) -> Optional[str]:
        """
        Get the status of a transcription job.
        
        Args:
            transcript_id: AssemblyAI transcript ID
            
        Returns:
            Status string, or None if error
        """
        try:
            transcript = self.transcriber.get_transcript(transcript_id)
            return transcript.status.value if transcript.status else None
        except Exception as e:
            logger.error(f"Error getting transcript status for {transcript_id}: {e}")
            return None
