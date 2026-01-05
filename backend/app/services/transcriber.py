"""Transcription service using Deepgram API."""
import json
from typing import List, Optional
try:
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
except ImportError:
    # Fallback for different Deepgram SDK versions
    try:
        from deepgram_sdk import DeepgramClient, PrerecordedOptions, FileSource
    except ImportError:
        DeepgramClient = None

from app.config import settings
from app.models.video import TranscriptSegment, TranscriptWord


class Transcriber:
    """Transcribes audio using Deepgram API."""
    
    def __init__(self):
        if not settings.deepgram_api_key:
            raise ValueError("DEEPGRAM_API_KEY not set")
        
        if DeepgramClient is None:
            raise ValueError("Deepgram SDK not installed")
        
        self.client = DeepgramClient(settings.deepgram_api_key)
        
        # #region agent log
        try:
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "transcriber.py:26",
                "message": "Inspecting Deepgram client structure",
                "data": {
                    "client_type": str(type(self.client)),
                    "client_attrs": [attr for attr in dir(self.client) if not attr.startswith("_")],
                    "has_listen": hasattr(self.client, "listen")
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
    
    def transcribe_audio(
        self,
        audio_path: str,
        enable_speaker_diarization: bool = True,
        enable_word_timestamps: bool = True
    ) -> List[TranscriptSegment]:
        """
        Transcribe audio file using Deepgram.
        
        Args:
            audio_path: Path to audio file
            enable_speaker_diarization: Enable speaker diarization
            enable_word_timestamps: Enable word-level timestamps
        
        Returns:
            List of transcript segments
        """
        s3_key_to_cleanup = None  # Track S3 key for cleanup
        try:
            import os
            audio_file_size = os.path.getsize(audio_path)
            audio_file_size_mb = audio_file_size / (1024 * 1024)
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TIMEOUT_A",
                    "location": "transcriber.py:67",
                    "message": "Audio file size check before transcription",
                    "data": {
                        "audio_path": audio_path,
                        "file_size_bytes": audio_file_size,
                        "file_size_mb": round(audio_file_size_mb, 2),
                        "file_size_gb": round(audio_file_size_mb / 1024, 2)
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Deepgram has limits: free tier is 300MB, paid tiers vary
            # For large files, use URL-based transcription if available
            MAX_BUFFER_SIZE_MB = 200  # Conservative limit for buffer upload
            
            # Check if we should use URL-based transcription for large files
            use_url_transcription = (
                settings.deepgram_use_url_for_large_files and 
                audio_file_size_mb > settings.deepgram_large_file_threshold_mb and
                settings.s3_bucket_name  # Need S3 to host the file
            )
            
            if audio_file_size_mb > MAX_BUFFER_SIZE_MB and not use_url_transcription:
                raise RuntimeError(
                    f"Audio file too large ({audio_file_size_mb:.1f}MB). "
                    f"Deepgram buffer upload limit is typically 200-300MB. "
                    f"Please configure S3_BUCKET_NAME to enable URL-based transcription for large files."
                )
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TIMEOUT_B",
                    "location": "transcriber.py:90",
                    "message": "Reading audio file into buffer",
                    "data": {
                        "file_size_mb": round(audio_file_size_mb, 2),
                        "starting_read": True
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            with open(audio_path, "rb") as audio_file:
                buffer_data = audio_file.read()
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TIMEOUT_C",
                    "location": "transcriber.py:105",
                    "message": "Audio file read complete, preparing payload",
                    "data": {
                        "buffer_size_bytes": len(buffer_data),
                        "buffer_size_mb": round(len(buffer_data) / (1024 * 1024), 2),
                        "payload_ready": True
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Prepare options
            options = PrerecordedOptions(
                model="nova-2",
                language="en-US",
                punctuate=True,
                diarize=enable_speaker_diarization,
                smart_format=True,
                utterances=True,
                paragraphs=True
            )
            
            # Use URL-based transcription for large files if S3 is configured
            s3_key_to_cleanup = None
            if use_url_transcription:
                # #region agent log
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "TIMEOUT_URL",
                        "location": "transcriber.py:130",
                        "message": "Using URL-based transcription for large file",
                        "data": {
                            "file_size_mb": round(audio_file_size_mb, 2),
                            "s3_bucket": settings.s3_bucket_name
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
                
                # Upload to S3 first, then transcribe from URL
                import boto3
                from pathlib import Path
                import uuid
                
                client_kwargs = {
                    'aws_access_key_id': settings.aws_access_key_id,
                    'aws_secret_access_key': settings.aws_secret_access_key,
                    'region_name': settings.aws_region
                }
                if settings.aws_session_token:
                    client_kwargs['aws_session_token'] = settings.aws_session_token
                
                s3_client = boto3.client('s3', **client_kwargs)
                
                # Upload audio to S3
                audio_filename = Path(audio_path).name
                s3_key_to_cleanup = f"audio/{uuid.uuid4()}_{audio_filename}"
                
                try:
                    s3_client.upload_file(audio_path, settings.s3_bucket_name, s3_key)
                    # Generate presigned URL (valid for 1 hour)
                    audio_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': settings.s3_bucket_name, 'Key': s3_key_to_cleanup},
                        ExpiresIn=3600
                    )
                    
                    # Use URL-based transcription
                    payload: FileSource = {
                        "url": audio_url,
                    }
                except Exception as s3_err:
                    # Fallback to buffer if S3 upload fails
                    print(f"Warning: S3 upload failed ({s3_err}), falling back to buffer upload")
                    s3_key_to_cleanup = None  # Don't cleanup if upload failed
                    payload: FileSource = {
                        "buffer": buffer_data,
                    }
            else:
                # Use buffer-based transcription for smaller files
                payload: FileSource = {
                    "buffer": buffer_data,
                }
            
            # #region agent log
            try:
                listen_obj = getattr(self.client, "listen", None)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "transcriber.py:87",
                    "message": "Inspecting listen object structure",
                    "data": {
                        "listen_obj_type": str(type(listen_obj)) if listen_obj else None,
                        "listen_obj_attrs": [attr for attr in dir(listen_obj) if not attr.startswith("_")] if listen_obj else None,
                        "has_rest": hasattr(listen_obj, "rest") if listen_obj else False,
                        "has_prerecorded": hasattr(listen_obj, "prerecorded") if listen_obj else False,
                        "has_v": hasattr(listen_obj, "v") if listen_obj else False,
                        "has_transcribe_file": hasattr(listen_obj, "transcribe_file") if listen_obj else False
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception as log_err:
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A",
                        "location": "transcriber.py:87",
                        "message": "Error inspecting listen object",
                        "data": {"error": str(log_err)},
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
            # #endregion
            
            # #region agent log
            try:
                listen_obj = getattr(self.client, "listen", None)
                if listen_obj:
                    prerecorded_obj = getattr(listen_obj, "prerecorded", None) if hasattr(listen_obj, "prerecorded") else None
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "transcriber.py:120",
                        "message": "Inspecting prerecorded object if exists",
                        "data": {
                            "prerecorded_obj_type": str(type(prerecorded_obj)) if prerecorded_obj else None,
                            "prerecorded_obj_attrs": [attr for attr in dir(prerecorded_obj) if not attr.startswith("_")] if prerecorded_obj else None,
                            "has_v": hasattr(prerecorded_obj, "v") if prerecorded_obj else False,
                            "has_transcribe_file": hasattr(prerecorded_obj, "transcribe_file") if prerecorded_obj else False
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
            except Exception as log_err:
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "transcriber.py:120",
                        "message": "Error inspecting prerecorded object",
                        "data": {"error": str(log_err)},
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
            # #endregion
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "transcriber.py:150",
                    "message": "About to attempt API call - testing rest path",
                    "data": {
                        "attempting_path": "client.listen.rest.v('1').transcribe_file",
                        "payload_size": len(buffer_data),
                        "options_model": options.model if hasattr(options, "model") else None
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # #region agent log
            try:
                v1_obj = self.client.listen.prerecorded.v("1")
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "transcriber.py:200",
                    "message": "Inspecting v('1') return object",
                    "data": {
                        "v1_obj_type": str(type(v1_obj)),
                        "v1_obj_attrs": [attr for attr in dir(v1_obj) if not attr.startswith("_")],
                        "has_transcribe_file": hasattr(v1_obj, "transcribe_file"),
                        "has_transcribe": hasattr(v1_obj, "transcribe"),
                        "has_transcribe_url": hasattr(v1_obj, "transcribe_url")
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception as log_err:
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "transcriber.py:200",
                        "message": "Error inspecting v('1') object",
                        "data": {"error": str(log_err), "error_type": str(type(log_err).__name__)},
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
            # #endregion
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "FIX",
                    "location": "transcriber.py:225",
                    "message": "Attempting corrected API call",
                    "data": {
                        "corrected_path": "client.listen.prerecorded.v('1').transcribe_file"
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # #region agent log
            try:
                import time
                api_call_start = time.time()
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "TIMEOUT_D",
                    "location": "transcriber.py:250",
                    "message": "About to call Deepgram transcribe_file API",
                    "data": {
                        "buffer_size_mb": round(len(buffer_data) / (1024 * 1024), 2),
                        "api_call_start_time": api_call_start
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Use transcribe_file with timeout handling
            # Deepgram SDK should handle timeouts, but we'll wrap it to catch timeout errors
            # For very large files, URL-based transcription is more reliable
            try:
                # #region agent log
                try:
                    payload_type = "url" if "url" in payload else "buffer"
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "TIMEOUT_G",
                        "location": "transcriber.py:320",
                        "message": "Calling transcribe_file with payload",
                        "data": {
                            "payload_type": payload_type,
                            "has_url": "url" in payload,
                            "has_buffer": "buffer" in payload,
                            "buffer_size_mb": round(len(payload.get("buffer", b"")) / (1024 * 1024), 2) if "buffer" in payload else 0
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
                
                response = self.client.listen.prerecorded.v("1").transcribe_file(
                    payload, options
                )
                
                # #region agent log
                try:
                    api_call_end = time.time()
                    api_call_duration = api_call_end - api_call_start
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "TIMEOUT_E",
                        "location": "transcriber.py:270",
                        "message": "Deepgram API call completed successfully",
                        "data": {
                            "api_call_duration_seconds": round(api_call_duration, 2),
                            "success": True
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
            except Exception as api_err:
                # #region agent log
                try:
                    api_call_end = time.time()
                    api_call_duration = api_call_end - api_call_start if 'api_call_start' in locals() else None
                    error_str = str(api_err).lower()
                    is_timeout = 'timeout' in error_str or 'timed out' in error_str
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "TIMEOUT_F",
                        "location": "transcriber.py:285",
                        "message": "Deepgram API call failed",
                        "data": {
                            "error_type": str(type(api_err).__name__),
                            "error_message": str(api_err),
                            "is_timeout_error": is_timeout,
                            "api_call_duration_seconds": round(api_call_duration, 2) if api_call_duration else None,
                            "buffer_size_mb": round(len(buffer_data) / (1024 * 1024), 2)
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
                raise
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "G",
                    "location": "transcriber.py:240",
                    "message": "Inspecting response object structure",
                    "data": {
                        "response_type": str(type(response)),
                        "response_attrs": [attr for attr in dir(response) if not attr.startswith("_")],
                        "has_results": hasattr(response, "results")
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # #region agent log
            try:
                results_obj = getattr(response, "results", None)
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H",
                    "location": "transcriber.py:260",
                    "message": "Inspecting response.results structure",
                    "data": {
                        "results_type": str(type(results_obj)) if results_obj else None,
                        "results_attrs": [attr for attr in dir(results_obj) if not attr.startswith("_")] if results_obj else None,
                        "has_channels": hasattr(results_obj, "channels") if results_obj else False
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Parse response
            segments = []
            
            if response.results and response.results.channels:
                channel = response.results.channels[0]
                
                # #region agent log
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "I",
                        "location": "transcriber.py:285",
                        "message": "Inspecting channel structure",
                        "data": {
                            "channel_type": str(type(channel)),
                            "channel_attrs": [attr for attr in dir(channel) if not attr.startswith("_")],
                            "has_alternatives": hasattr(channel, "alternatives")
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
                
                if channel.alternatives:
                    alternative = channel.alternatives[0]
                    
                    # #region agent log
                    try:
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "J",
                            "location": "transcriber.py:305",
                            "message": "Inspecting alternative object structure",
                            "data": {
                                "alternative_type": str(type(alternative)),
                                "alternative_attrs": [attr for attr in dir(alternative) if not attr.startswith("_")],
                                "has_utterances": hasattr(alternative, "utterances"),
                                "has_words": hasattr(alternative, "words"),
                                "has_paragraphs": hasattr(alternative, "paragraphs"),
                                "has_transcript": hasattr(alternative, "transcript")
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                            f.write(json.dumps(log_data) + "\n")
                    except Exception:
                        pass
                    # #endregion
                    
                    # #region agent log
                    try:
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "K",
                            "location": "transcriber.py:325",
                            "message": "Checking if utterances exist at channel level",
                            "data": {
                                "channel_has_utterances": hasattr(channel, "utterances"),
                                "results_has_utterances": hasattr(response.results, "utterances") if hasattr(response, "results") else False
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                            f.write(json.dumps(log_data) + "\n")
                    except Exception:
                        pass
                    # #endregion
                    
                    # #region agent log
                    try:
                        utterances_list = getattr(response.results, "utterances", None) if hasattr(response, "results") else None
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "FIX2",
                            "location": "transcriber.py:360",
                            "message": "Accessing utterances from results level",
                            "data": {
                                "utterances_type": str(type(utterances_list)) if utterances_list else None,
                                "utterances_count": len(utterances_list) if utterances_list else 0,
                                "utterances_attrs": [attr for attr in dir(utterances_list[0]) if not attr.startswith("_")] if utterances_list and len(utterances_list) > 0 else None
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                            f.write(json.dumps(log_data) + "\n")
                    except Exception as log_err:
                        try:
                            log_data = {
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "FIX2",
                                "location": "transcriber.py:360",
                                "message": "Error accessing utterances from results",
                                "data": {"error": str(log_err)},
                                "timestamp": int(__import__("time").time() * 1000)
                            }
                            with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                                f.write(json.dumps(log_data) + "\n")
                        except Exception:
                            pass
                    # #endregion
                    
                    # Process utterances (segments) - utterances are at response.results.utterances, not alternative.utterances
                    if response.results.utterances:
                        for utterance in response.results.utterances:
                            words = []
                            
                            # Extract word-level timestamps
                            if alternative.words:
                                for word_obj in alternative.words:
                                    # Find words in this utterance
                                    if (word_obj.start >= utterance.start and
                                        word_obj.end <= utterance.end):
                                        words.append(TranscriptWord(
                                            word=word_obj.word,
                                            start=word_obj.start,
                                            end=word_obj.end,
                                            speaker=word_obj.speaker if hasattr(word_obj, 'speaker') else None
                                        ))
                            
                            segments.append(TranscriptSegment(
                                text=utterance.transcript,
                                start=utterance.start,
                                end=utterance.end,
                                words=words,
                                speaker=utterance.speaker if hasattr(utterance, 'speaker') else None
                            ))
                    else:
                        # Fallback: use paragraphs or full transcript
                        if alternative.paragraphs:
                            for para in alternative.paragraphs.transcript:
                                segments.append(TranscriptSegment(
                                    text=para,
                                    start=0.0,
                                    end=0.0,
                                    words=[],
                                    speaker=None
                                ))
                        elif alternative.transcript:
                            segments.append(TranscriptSegment(
                                text=alternative.transcript,
                                start=0.0,
                                end=0.0,
                                words=[],
                                speaker=None
                            ))
            
            # Clean up S3 file if we used URL-based transcription
            if s3_key_to_cleanup:
                try:
                    import boto3
                    client_kwargs = {
                        'aws_access_key_id': settings.aws_access_key_id,
                        'aws_secret_access_key': settings.aws_secret_access_key,
                        'region_name': settings.aws_region
                    }
                    if settings.aws_session_token:
                        client_kwargs['aws_session_token'] = settings.aws_session_token
                    s3_client = boto3.client('s3', **client_kwargs)
                    s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key_to_cleanup)
                except Exception as cleanup_err:
                    print(f"Warning: Failed to cleanup S3 file {s3_key_to_cleanup}: {cleanup_err}")
            
            return segments
        
        except Exception as e:
            # Clean up S3 file on error if we used URL-based transcription
            if 's3_key_to_cleanup' in locals() and s3_key_to_cleanup:
                try:
                    import boto3
                    client_kwargs = {
                        'aws_access_key_id': settings.aws_access_key_id,
                        'aws_secret_access_key': settings.aws_secret_access_key,
                        'region_name': settings.aws_region
                    }
                    if settings.aws_session_token:
                        client_kwargs['aws_session_token'] = settings.aws_session_token
                    s3_client = boto3.client('s3', **client_kwargs)
                    s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key_to_cleanup)
                except Exception:
                    pass
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "transcriber.py:124",
                    "message": "Exception caught during transcription",
                    "data": {
                        "error_type": str(type(e).__name__),
                        "error_message": str(e),
                        "error_args": str(e.args) if hasattr(e, "args") else None
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            raise RuntimeError(f"Deepgram transcription error: {str(e)}") from e

