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
        try:
            with open(audio_path, "rb") as audio_file:
                buffer_data = audio_file.read()
            
            payload: FileSource = {
                "buffer": buffer_data,
            }
            
            options = PrerecordedOptions(
                model="nova-2",
                language="en-US",
                punctuate=True,
                diarize=enable_speaker_diarization,
                smart_format=True,
                utterances=True,
                paragraphs=True
            )
            
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
            
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )
            
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
            
            return segments
        
        except Exception as e:
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

