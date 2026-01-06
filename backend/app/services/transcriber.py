"""Transcription service using AWS Transcribe."""
import json
import time
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.models.video import TranscriptSegment, TranscriptWord


class Transcriber:
    """Transcribes audio using AWS Transcribe."""
    
    def __init__(self):
        if not (settings.aws_access_key_id and settings.aws_secret_access_key):
            raise ValueError("AWS credentials not set")
        
        if not settings.s3_bucket_name:
            raise ValueError("S3_BUCKET_NAME not set (required for AWS Transcribe)")
        
        client_kwargs = {
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': settings.aws_region
        }
        if settings.aws_session_token:
            client_kwargs['aws_session_token'] = settings.aws_session_token
        
        self.transcribe_client = boto3.client('transcribe', **client_kwargs)
        self.s3_client = boto3.client('s3', **client_kwargs)
        self.s3_bucket = settings.s3_bucket_name
    
    def transcribe_audio(
        self,
        audio_path: str,
        enable_speaker_diarization: bool = True,
        enable_word_timestamps: bool = True
    ) -> List[TranscriptSegment]:
        """
        Transcribe audio file using AWS Transcribe.
        
        Args:
            audio_path: Path to audio file
            enable_speaker_diarization: Enable speaker diarization
            enable_word_timestamps: Enable word-level timestamps
        
        Returns:
            List of transcript segments
        """
        import os
        import uuid
        from pathlib import Path
        
        # Validate that we're receiving an audio file, not a video file
        audio_path_obj = Path(audio_path)
        if not audio_path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Check file extension to ensure it's an audio file
        audio_ext = audio_path_obj.suffix.lower()
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv', '.wmv'}
        if audio_ext in video_extensions:
            raise ValueError(
                f"Expected audio file but received video file: {audio_path}. "
                f"Please extract audio from video first using AudioExtractor."
            )
        
        # Get file size to log (audio files should be much smaller than video)
        file_size_mb = audio_path_obj.stat().st_size / (1024 * 1024)
        
        job_name = f"transcribe-{uuid.uuid4()}"
        audio_filename = audio_path_obj.name
        s3_audio_key = f"audio/{job_name}/{audio_filename}"
        s3_output_key = f"transcripts/{job_name}.json"
        
        try:
            # Upload audio file to S3
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TRANSCRIBE_A",
                    "location": "transcriber.py:upload",
                    "message": "Uploading audio to S3 for transcription",
                    "data": {
                        "audio_path": audio_path,
                        "audio_file_size_mb": round(file_size_mb, 2),
                        "audio_extension": audio_ext,
                        "s3_key": s3_audio_key,
                        "job_name": job_name
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Upload audio file to S3 (required for AWS Transcribe)
            # Note: Only the extracted audio file is uploaded, not the full video
            print(f"Uploading audio file to S3 for transcription: {audio_filename} ({file_size_mb:.2f} MB)")
            try:
                self.s3_client.upload_file(audio_path, self.s3_bucket, s3_audio_key)
                print(f"Successfully uploaded audio to S3: s3://{self.s3_bucket}/{s3_audio_key}")
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                error_message = str(e)
                # #region agent log
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "TRANSCRIBE_S3_UPLOAD_FAILED",
                        "location": "transcriber.py:upload_audio",
                        "message": "S3 upload failed for transcription",
                        "data": {
                            "error_code": error_code,
                            "error_message": error_message,
                            "s3_bucket": self.s3_bucket,
                            "s3_key": s3_audio_key,
                            "audio_path": audio_path
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
                
                if error_code == 'InvalidAccessKeyId':
                    raise ValueError(
                        f"AWS Access Key ID is invalid. Please check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables. "
                        f"Error: {error_message}"
                    )
                elif error_code == 'NoSuchBucket':
                    raise ValueError(
                        f"S3 bucket '{self.s3_bucket}' does not exist. Please create the bucket or update S3_BUCKET_NAME. "
                        f"Error: {error_message}"
                    )
                elif error_code == 'AccessDenied':
                    raise ValueError(
                        f"Access denied to S3 bucket '{self.s3_bucket}'. Please check IAM permissions for s3:PutObject. "
                        f"Error: {error_message}"
                    )
                else:
                    raise ValueError(
                        f"Failed to upload audio to S3 for transcription: {error_code} - {error_message}"
                    )
            
            # Get S3 URI
            s3_uri = f"s3://{self.s3_bucket}/{s3_audio_key}"
            
            # Determine media format from file extension
            audio_ext = Path(audio_path).suffix.lower()
            media_format_map = {
                '.mp3': 'mp3',
                '.mp4': 'mp4',
                '.wav': 'wav',
                '.flac': 'flac',
                '.ogg': 'ogg',
                '.amr': 'amr',
                '.webm': 'webm',
                '.m4a': 'mp4'
            }
            media_format = media_format_map.get(audio_ext, 'mp3')
            
            # Configure transcription settings
            transcription_settings = {
                'TranscriptionJobName': job_name,
                'Media': {'MediaFileUri': s3_uri},
                'MediaFormat': media_format,
                'LanguageCode': 'en-US',
                'OutputBucketName': self.s3_bucket,
                'OutputKey': s3_output_key,
                'Settings': {
                    'ShowSpeakerLabels': enable_speaker_diarization,
                    'MaxSpeakerLabels': 10 if enable_speaker_diarization else 0
                }
            }
            
            # Start transcription job
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TRANSCRIBE_B",
                    "location": "transcriber.py:start_job",
                    "message": "Starting AWS Transcribe job",
                    "data": {
                        "job_name": job_name,
                        "media_format": media_format,
                        "speaker_diarization": enable_speaker_diarization
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            self.transcribe_client.start_transcription_job(**transcription_settings)
            
            # Poll for job completion
            max_wait_time = 3600  # 1 hour max wait
            poll_interval = 5  # Check every 5 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                response = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                
                job_status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                # #region agent log
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "TRANSCRIBE_C",
                        "location": "transcriber.py:poll",
                        "message": "Polling transcription job status",
                        "data": {
                            "job_name": job_name,
                            "status": job_status,
                            "elapsed_seconds": elapsed_time
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
                
                if job_status == 'COMPLETED':
                    break
                elif job_status == 'FAILED':
                    failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                    raise RuntimeError(f"AWS Transcribe job failed: {failure_reason}")
                
                time.sleep(poll_interval)
                elapsed_time += poll_interval
            
            if elapsed_time >= max_wait_time:
                raise RuntimeError("AWS Transcribe job timed out")
            
            # Get transcription results
            transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            
            # Download transcript from S3
            import urllib.parse
            import urllib.request
            import re
            
            # Parse the transcript URI - AWS Transcribe can return either:
            # 1. S3 URI: s3://bucket-name/key/path.json
            # 2. HTTPS URL: https://s3.region.amazonaws.com/bucket-name/key/path.json
            # 3. HTTPS URL: https://bucket-name.s3.region.amazonaws.com/key/path.json
            
            parsed_uri = urllib.parse.urlparse(transcript_uri)
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TRANSCRIBE_URI_PARSE",
                    "location": "transcriber.py:parse_uri",
                    "message": "Parsing transcript URI",
                    "data": {
                        "transcript_uri": transcript_uri,
                        "scheme": parsed_uri.scheme,
                        "netloc": parsed_uri.netloc,
                        "path": parsed_uri.path
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Extract bucket and key based on URI format
            if parsed_uri.scheme == 's3':
                # S3 URI format: s3://bucket-name/key/path
                transcript_bucket = parsed_uri.netloc
                transcript_key = parsed_uri.path.lstrip('/')
            elif parsed_uri.scheme in ('https', 'http'):
                # HTTPS URL format - need to extract bucket from path or hostname
                # Format 1: https://s3.region.amazonaws.com/bucket-name/key/path
                # Format 2: https://bucket-name.s3.region.amazonaws.com/key/path
                
                # Check if bucket is in hostname (format 2)
                s3_hostname_match = re.match(r'^([^.]+)\.s3[.-]([^.]+)\.amazonaws\.com$', parsed_uri.netloc)
                if s3_hostname_match:
                    transcript_bucket = s3_hostname_match.group(1)
                    transcript_key = parsed_uri.path.lstrip('/')
                else:
                    # Format 1: bucket is first part of path
                    path_parts = parsed_uri.path.lstrip('/').split('/', 1)
                    if len(path_parts) >= 2:
                        transcript_bucket = path_parts[0]
                        transcript_key = path_parts[1]
                    else:
                        # Fallback: try to extract from netloc if it's a bucket subdomain
                        # This handles edge cases
                        transcript_bucket = None
                        transcript_key = parsed_uri.path.lstrip('/')
                        raise ValueError(f"Could not parse bucket from transcript URI: {transcript_uri}")
            else:
                raise ValueError(f"Unsupported URI scheme in transcript URI: {transcript_uri}")
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TRANSCRIBE_D",
                    "location": "transcriber.py:download",
                    "message": "Downloading transcription results",
                    "data": {
                        "transcript_uri": transcript_uri,
                        "parsed_bucket": transcript_bucket,
                        "parsed_key": transcript_key,
                        "configured_bucket": self.s3_bucket,
                        "output_key": s3_output_key
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Try to download transcript JSON
            # AWS Transcribe writes to the bucket/key we specified, so try that first
            transcript_data = None
            try:
                # First, try the configured bucket with the output key we specified
                # This is the most reliable method since we control these values
                print(f"Attempting to download transcript from configured bucket: s3://{self.s3_bucket}/{s3_output_key}")
                transcript_obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_output_key)
                transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))
                print(f"Successfully downloaded transcript from configured bucket")
            except ClientError as configured_error:
                # If that fails, try the parsed bucket/key from the URI
                try:
                    print(f"Configured bucket failed, trying parsed URI bucket: s3://{transcript_bucket}/{transcript_key}")
                    transcript_obj = self.s3_client.get_object(Bucket=transcript_bucket, Key=transcript_key)
                    transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))
                    print(f"Successfully downloaded transcript from parsed URI bucket")
                except ClientError as s3_error:
                    error_code = s3_error.response.get('Error', {}).get('Code', '')
                    # If AccessDenied or other error, try HTTP download
                    if error_code == 'AccessDenied' or error_code:
                        try:
                            print(f"Warning: S3 access failed ({error_code}), attempting HTTP download from transcript URI")
                            # Try the original transcript URI (might be HTTPS)
                            req = urllib.request.Request(transcript_uri)
                            # Add headers to avoid 403 errors
                            req.add_header('User-Agent', 'Mozilla/5.0')
                            with urllib.request.urlopen(req, timeout=30) as response:
                                transcript_data = json.loads(response.read().decode('utf-8'))
                            print(f"Successfully downloaded transcript via HTTP")
                        except urllib.error.HTTPError as http_error:
                            # If HTTP fails, the transcript should be in the configured bucket with output key
                            try:
                                print(f"Warning: HTTP download failed ({http_error.code}), trying configured bucket with output key")
                                transcript_obj = self.s3_client.get_object(
                                    Bucket=self.s3_bucket,
                                    Key=s3_output_key
                                )
                                transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))
                                print(f"Successfully downloaded transcript from configured bucket")
                            except Exception as final_error:
                                raise RuntimeError(
                                    f"Failed to download transcript from S3. Tried multiple methods:\n"
                                    f"1. Configured bucket '{self.s3_bucket}' with output key '{s3_output_key}': {str(configured_error)}\n"
                                    f"2. Parsed URI bucket '{transcript_bucket}' with key '{transcript_key}': {str(s3_error)}\n"
                                    f"3. HTTP download from URI: {str(http_error)}\n"
                                    f"4. Configured bucket with output key (retry): {str(final_error)}\n"
                                    f"Please ensure your AWS credentials have s3:GetObject permission for bucket '{self.s3_bucket}'."
                                ) from final_error
                        except Exception as http_error:
                            # If HTTP fails for other reasons, try the configured bucket with output key
                            try:
                                print(f"Warning: HTTP download failed, trying configured bucket with output key")
                                transcript_obj = self.s3_client.get_object(
                                    Bucket=self.s3_bucket,
                                    Key=s3_output_key
                                )
                                transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))
                                print(f"Successfully downloaded transcript from configured bucket")
                            except Exception as final_error:
                                raise RuntimeError(
                                    f"Failed to download transcript from S3. Tried multiple methods:\n"
                                    f"1. Configured bucket '{self.s3_bucket}' with output key '{s3_output_key}': {str(configured_error)}\n"
                                    f"2. Parsed URI bucket '{transcript_bucket}' with key '{transcript_key}': {str(s3_error)}\n"
                                    f"3. HTTP download from URI: {str(http_error)}\n"
                                    f"4. Configured bucket with output key (retry): {str(final_error)}\n"
                                    f"Please ensure your AWS credentials have s3:GetObject permission for bucket '{self.s3_bucket}'."
                                ) from final_error
                    else:
                        raise RuntimeError(
                            f"Failed to download transcript from S3 bucket '{transcript_bucket}'. "
                            f"Please ensure your AWS credentials have s3:GetObject permission. "
                            f"Error: {str(s3_error)}"
                        ) from s3_error
            
            # Parse transcript into segments
            segments = self._parse_transcript(transcript_data, enable_word_timestamps)
            
            # Clean up S3 files
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_audio_key)
                self.s3_client.delete_object(Bucket=transcript_bucket, Key=transcript_key)
            except Exception as cleanup_err:
                print(f"Warning: Failed to cleanup S3 files: {cleanup_err}")
            
            # Delete transcription job
            try:
                self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
            except Exception:
                pass  # Job deletion is optional
            
            return segments
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = str(e)
            raise RuntimeError(f"AWS Transcribe error ({error_code}): {error_message}") from e
        except Exception as e:
            # Clean up on error
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_audio_key)
            except Exception:
                pass
            raise RuntimeError(f"AWS Transcribe error: {str(e)}") from e
    
    def _parse_transcript(
        self,
        transcript_data: dict,
        enable_word_timestamps: bool
    ) -> List[TranscriptSegment]:
        """Parse AWS Transcribe JSON response into transcript segments."""
        segments = []
        
        results = transcript_data.get('results', {})
        items = results.get('items', [])
        
        if not items:
            return segments
        
        # Group items into segments (by speaker if available, or by punctuation)
        current_segment_items = []
        current_speaker = None
        segment_start = None
        
        speaker_labels = results.get('speaker_labels', {}).get('segments', [])
        speaker_map = {}
        for label in speaker_labels:
            speaker_map[label['start_time']] = label.get('speaker_label', 'spk_0')
        
        for item in items:
            item_type = item.get('type')
            if item_type == 'punctuation':
                # Add punctuation to current segment
                if current_segment_items:
                    current_segment_items.append(item)
            else:
                # Check if we should start a new segment
                start_time = float(item.get('start_time', 0))
                end_time = float(item.get('end_time', 0))
                
                # Get speaker for this item
                item_speaker = None
                for label in speaker_labels:
                    if float(label['start_time']) <= start_time <= float(label['end_time']):
                        speaker_label = label.get('speaker_label', 'spk_0')
                        # Convert spk_0, spk_1 to 0, 1
                        item_speaker = int(speaker_label.replace('spk_', '')) if 'spk_' in speaker_label else None
                        break
                
                # Start new segment if speaker changed or if this is first item
                if current_speaker is not None and item_speaker != current_speaker:
                    # Finalize current segment
                    if current_segment_items:
                        segment = self._create_segment_from_items(
                            current_segment_items,
                            current_speaker,
                            enable_word_timestamps
                        )
                        if segment:
                            segments.append(segment)
                    
                    # Start new segment
                    current_segment_items = [item]
                    current_speaker = item_speaker
                    segment_start = start_time
                else:
                    # Continue current segment
                    if current_speaker is None:
                        current_speaker = item_speaker
                        segment_start = start_time
                    current_segment_items.append(item)
        
        # Finalize last segment
        if current_segment_items:
            segment = self._create_segment_from_items(
                current_segment_items,
                current_speaker,
                enable_word_timestamps
            )
            if segment:
                segments.append(segment)
        
        # If no segments created (no speaker labels), create one segment from all items
        if not segments and items:
            segment = self._create_segment_from_items(items, None, enable_word_timestamps)
            if segment:
                segments.append(segment)
        
        return segments
    
    def _create_segment_from_items(
        self,
        items: List[dict],
        speaker: Optional[int],
        enable_word_timestamps: bool
    ) -> Optional[TranscriptSegment]:
        """Create a transcript segment from a list of items."""
        if not items:
            return None
        
        words = []
        text_parts = []
        
        for item in items:
            content = item.get('alternatives', [{}])[0].get('content', '')
            if content:
                text_parts.append(content)
            
            if enable_word_timestamps and item.get('type') == 'pronunciation':
                start_time = float(item.get('start_time', 0))
                end_time = float(item.get('end_time', 0))
                words.append(TranscriptWord(
                    word=content,
                    start=start_time,
                    end=end_time,
                    speaker=speaker
                ))
        
        if not text_parts:
            return None
        
        # Get segment timing from first and last items
        first_item = items[0]
        last_item = items[-1]
        segment_start = float(first_item.get('start_time', 0))
        segment_end = float(last_item.get('end_time', segment_start))
        
        text = ' '.join(text_parts)
        
        return TranscriptSegment(
            text=text,
            start=segment_start,
            end=segment_end,
            words=words,
            speaker=speaker
        )
