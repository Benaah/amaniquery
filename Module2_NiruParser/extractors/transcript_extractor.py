"""
YouTube Transcript Extractor
Fetches transcripts with timestamps for YouTube videos
"""
from typing import Dict, List, Optional
from loguru import logger


class TranscriptExtractor:
    """Extract transcripts from YouTube videos"""
    
    def __init__(self):
        """Initialize transcript extractor"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                TranscriptsDisabled,
                NoTranscriptFound,
                VideoUnavailable
            )
            self.api = YouTubeTranscriptApi
            self.TranscriptsDisabled = TranscriptsDisabled
            self.NoTranscriptFound = NoTranscriptFound
            self.VideoUnavailable = VideoUnavailable
            self.available = True
            logger.info("YouTube Transcript API initialized")
        except ImportError:
            logger.warning("youtube-transcript-api not installed. Transcript extraction disabled.")
            self.available = False
    
    def extract_transcript(
        self,
        video_id: str,
        languages: List[str] = None
    ) -> Optional[Dict]:
        """
        Extract transcript from YouTube video
        
        Args:
            video_id: YouTube video ID (11 characters)
            languages: Preferred languages (default: ['en', 'sw'])
            
        Returns:
            Dictionary with transcript data or None if unavailable
        """
        if not self.available:
            logger.warning("Transcript API not available")
            return None
        
        if languages is None:
            languages = ['en', 'sw']  # English and Swahili
        
        try:
            # Fetch transcript
            transcript_list = self.api.list_transcripts(video_id)
            
            # Try to get transcript in preferred languages
            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except self.NoTranscriptFound:
                    continue
            
            # If no preferred language, get any available transcript
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                    # Get first available transcript
                    available = list(transcript_list)
                    if available:
                        transcript = available[0]
            
            if not transcript:
                logger.warning(f"No transcript available for video {video_id}")
                return None
            
            # Fetch transcript data
            transcript_data = transcript.fetch()
            
            # Process transcript
            result = {
                'video_id': video_id,
                'language': transcript.language_code,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable,
                'segments': self._process_segments(transcript_data),
                'full_text': self._combine_text(transcript_data),
                'total_duration': transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0,
            }
            
            logger.info(f"Extracted transcript for {video_id}: {len(transcript_data)} segments, {result['language']}")
            return result
            
        except self.TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
            return None
        except self.VideoUnavailable:
            logger.error(f"Video {video_id} is unavailable")
            return None
        except Exception as e:
            logger.error(f"Error extracting transcript for {video_id}: {e}")
            return None
    
    def _process_segments(self, transcript_data: List[Dict]) -> List[Dict]:
        """
        Process transcript segments with timestamps
        
        Args:
            transcript_data: Raw transcript data from API
            
        Returns:
            List of processed segments
        """
        segments = []
        
        for segment in transcript_data:
            segments.append({
                'text': segment['text'].strip(),
                'start': segment['start'],  # Start time in seconds
                'duration': segment['duration'],
                'end': segment['start'] + segment['duration'],
            })
        
        return segments
    
    def _combine_text(self, transcript_data: List[Dict]) -> str:
        """Combine all transcript text into a single string"""
        return " ".join([segment['text'].strip() for segment in transcript_data])
    
    def get_text_at_timestamp(
        self,
        transcript_data: Dict,
        timestamp: float,
        context_seconds: int = 30
    ) -> str:
        """
        Get transcript text around a specific timestamp
        
        Args:
            transcript_data: Transcript dictionary from extract_transcript()
            timestamp: Time in seconds
            context_seconds: Seconds of context before/after timestamp
            
        Returns:
            Text excerpt around the timestamp
        """
        segments = transcript_data.get('segments', [])
        
        # Find segments within the time range
        start_time = max(0, timestamp - context_seconds)
        end_time = timestamp + context_seconds
        
        relevant_segments = [
            seg for seg in segments
            if seg['start'] <= end_time and seg['end'] >= start_time
        ]
        
        if not relevant_segments:
            return ""
        
        return " ".join([seg['text'] for seg in relevant_segments])
    
    def search_transcript(
        self,
        transcript_data: Dict,
        query: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search for query term in transcript and return matching segments
        
        Args:
            transcript_data: Transcript dictionary
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of matching segments with timestamps
        """
        segments = transcript_data.get('segments', [])
        query_lower = query.lower()
        
        matches = []
        for segment in segments:
            if query_lower in segment['text'].lower():
                matches.append({
                    'text': segment['text'],
                    'start': segment['start'],
                    'timestamp_formatted': self._format_timestamp(segment['start']),
                    'video_url_with_timestamp': f"https://www.youtube.com/watch?v={transcript_data['video_id']}&t={int(segment['start'])}s"
                })
                
                if len(matches) >= max_results:
                    break
        
        return matches
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as HH:MM:SS or MM:SS
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def chunk_transcript(
        self,
        transcript_data: Dict,
        chunk_duration: int = 60,
        overlap_duration: int = 10
    ) -> List[Dict]:
        """
        Split transcript into chunks for vector database storage
        
        Args:
            transcript_data: Transcript dictionary
            chunk_duration: Duration of each chunk in seconds
            overlap_duration: Overlap between chunks in seconds
            
        Returns:
            List of chunks with metadata
        """
        segments = transcript_data.get('segments', [])
        
        if not segments:
            return []
        
        chunks = []
        current_chunk_text = []
        current_chunk_start = segments[0]['start']
        current_duration = 0
        
        for segment in segments:
            current_chunk_text.append(segment['text'])
            current_duration = segment['end'] - current_chunk_start
            
            # Create chunk if duration threshold reached
            if current_duration >= chunk_duration:
                chunk = {
                    'text': " ".join(current_chunk_text),
                    'start_time': current_chunk_start,
                    'end_time': segment['end'],
                    'duration': current_duration,
                    'video_id': transcript_data['video_id'],
                    'timestamp_url': f"https://www.youtube.com/watch?v={transcript_data['video_id']}&t={int(current_chunk_start)}s",
                    'timestamp_formatted': self._format_timestamp(current_chunk_start),
                }
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_start = segment['start'] - overlap_duration
                current_chunk_text = [
                    seg['text'] for seg in segments
                    if seg['start'] >= overlap_start and seg['start'] <= segment['end']
                ]
                current_chunk_start = max(current_chunk_start, overlap_start)
                current_duration = 0
        
        # Add final chunk if there's remaining text
        if current_chunk_text:
            chunks.append({
                'text': " ".join(current_chunk_text),
                'start_time': current_chunk_start,
                'end_time': segments[-1]['end'],
                'duration': segments[-1]['end'] - current_chunk_start,
                'video_id': transcript_data['video_id'],
                'timestamp_url': f"https://www.youtube.com/watch?v={transcript_data['video_id']}&t={int(current_chunk_start)}s",
                'timestamp_formatted': self._format_timestamp(current_chunk_start),
            })
        
        logger.info(f"Created {len(chunks)} chunks from transcript")
        return chunks
