"""
Google Cloud Storage service for downloading audio recordings.
"""

import os
import tempfile
import logging
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class GCSService:
    """Service for interacting with Google Cloud Storage."""
    
    def __init__(self, bucket_name: str, credentials_path: str = "key.json"):
        """
        Initialize GCS service.
        
        Args:
            bucket_name: Name of the GCS bucket
            credentials_path: Path to the service account credentials JSON file
        """
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self._client = None
        
    def _get_client(self) -> storage.Client:
        """Get or create GCS client with authentication."""
        if self._client is None:
            try:
                # Load service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self._client = storage.Client(credentials=credentials)
                logger.info("GCS client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")
                raise
        return self._client
    
    def find_recording_file(self, room_id: str) -> Optional[str]:
        """
        Find the recording file for a given room ID.
        
        Args:
            room_id: The LiveKit room ID
            
        Returns:
            The GCS path to the recording file, or None if not found
        """
        try:
            client = self._get_client()
            bucket = client.bucket(self.bucket_name)
            
            # Look for recordings in the recordings/{room_id}/ directory
            prefix = f"recordings/{room_id}/"
            blobs = bucket.list_blobs(prefix=prefix)
            
            # Find the .ogg file (LiveKit egress creates .ogg files)
            for blob in blobs:
                if blob.name.endswith('.ogg'):
                    logger.info(f"Found recording file: {blob.name}")
                    return blob.name
            
            logger.warning(f"No recording file found for room_id: {room_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding recording file for room {room_id}: {e}")
            return None
    
    def download_recording(self, room_id: str, local_path: Optional[str] = None) -> Optional[str]:
        """
        Download the recording file for a given room ID.
        
        Args:
            room_id: The LiveKit room ID
            local_path: Local path to save the file. If None, creates a temp file.
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        try:
            # Find the recording file
            gcs_path = self.find_recording_file(room_id)
            if not gcs_path:
                return None
            
            # Determine local path
            if local_path is None:
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                filename = f"{room_id}_recording.ogg"
                local_path = os.path.join(temp_dir, filename)
            
            # Download the file
            client = self._get_client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded recording to: {local_path}")
            
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading recording for room {room_id}: {e}")
            return None
    
    def get_recording_info(self, room_id: str) -> Optional[dict]:
        """
        Get information about the recording file.
        
        Args:
            room_id: The LiveKit room ID
            
        Returns:
            Dictionary with recording info, or None if not found
        """
        try:
            gcs_path = self.find_recording_file(room_id)
            if not gcs_path:
                return None
            
            client = self._get_client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            
            # Reload blob to get metadata
            blob.reload()
            
            return {
                "gcs_path": gcs_path,
                "size_bytes": blob.size,
                "created": blob.time_created,
                "updated": blob.updated,
                "content_type": blob.content_type
            }
            
        except Exception as e:
            logger.error(f"Error getting recording info for room {room_id}: {e}")
            return None
