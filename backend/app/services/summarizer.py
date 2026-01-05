"""Summarization service using Amazon Bedrock Claude."""
import json
from typing import List
import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.models.video import MeetingSummary, UniqueSlide, TranscriptSegment


class Summarizer:
    """Generates meeting summaries using Claude via Amazon Bedrock."""
    
    def __init__(self):
        if not (settings.aws_access_key_id and settings.aws_secret_access_key):
            raise ValueError("AWS credentials not set")
        
        client_kwargs = {
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': settings.aws_region
        }
        if settings.aws_session_token:
            client_kwargs['aws_session_token'] = settings.aws_session_token
        self.bedrock_runtime = boto3.client('bedrock-runtime', **client_kwargs)
        self.model_id = settings.bedrock_model_id
    
    def _format_transcript(self, segments: List[TranscriptSegment]) -> str:
        """Format transcript segments into a readable text."""
        lines = []
        for segment in segments:
            timestamp = f"[{int(segment.start//60)}:{int(segment.start%60):02d}]"
            speaker = f"Speaker {segment.speaker}: " if segment.speaker else ""
            lines.append(f"{timestamp} {speaker}{segment.text}")
        return "\n".join(lines)
    
    def _format_slides(self, slides: List[UniqueSlide]) -> str:
        """Format slide information for the prompt."""
        lines = []
        for slide in slides:
            appearances_str = ", ".join([
                f"{int(app.start//60)}:{int(app.start%60):02d}"
                for app in slide.appearances
            ])
            lines.append(f"- Slide {slide.slide_id} (shown at: {appearances_str}): {slide.ocr_text[:100]}...")
        return "\n".join(lines)
    
    def generate_summary(
        self,
        transcript: List[TranscriptSegment],
        slides: List[UniqueSlide]
    ) -> MeetingSummary:
        """
        Generate meeting summary using Claude.
        
        Args:
            transcript: List of transcript segments
            slides: List of unique slides
        
        Returns:
            MeetingSummary object
        """
        # Format inputs
        transcript_text = self._format_transcript(transcript)
        slides_text = self._format_slides(slides)
        
        # Create prompt
        prompt = f"""You are analyzing a meeting transcript and slide presentations. Please provide a comprehensive summary.

TRANSCRIPT:
{transcript_text}

SLIDES SHOWN:
{slides_text}

Please analyze this meeting and provide:
1. An executive summary (2-3 paragraphs)
2. Key decisions made (bullet points)
3. Action items with owners if mentioned (bullet points)
4. Key topics discussed (bullet points)

Format your response as JSON with the following structure:
{{
    "executive_summary": "...",
    "decisions": ["...", "..."],
    "action_items": ["...", "..."],
    "key_topics": ["...", "..."]
}}

Respond only with valid JSON, no additional text."""

        try:
            # #region agent log
            import json as json_module
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "summarizer.py:92",
                    "message": "About to invoke Bedrock model",
                    "data": {
                        "model_id": self.model_id,
                        "model_id_type": str(type(self.model_id)),
                        "region": settings.aws_region
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json_module.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Try to list available foundation models to find correct ID
            # #region agent log
            try:
                bedrock_client = boto3.client(
                    'bedrock',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
                if settings.aws_session_token:
                    bedrock_client = boto3.client(
                        'bedrock',
                        aws_access_key_id=settings.aws_access_key_id,
                        aws_secret_access_key=settings.aws_secret_access_key,
                        aws_session_token=settings.aws_session_token,
                        region_name=settings.aws_region
                    )
                
                try:
                    models_response = bedrock_client.list_foundation_models()
                    all_models = models_response.get('modelSummaries', [])
                    claude_models = [
                        m for m in all_models
                        if 'claude' in m.get('modelId', '').lower()
                    ]
                    claude_35_models = [
                        m for m in claude_models
                        if '3.5' in m.get('modelId', '') or 'sonnet' in m.get('modelId', '').lower()
                    ]
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "summarizer.py:110",
                        "message": "Found available Claude models",
                        "data": {
                            "total_models": len(all_models),
                            "all_claude_models": [m.get('modelId') for m in claude_models],
                            "claude_35_models": [m.get('modelId') for m in claude_35_models],
                            "model_details": [
                                {
                                    "modelId": m.get('modelId'),
                                    "modelName": m.get('modelName'),
                                    "providerName": m.get('providerName'),
                                    "inferenceTypesSupported": m.get('inferenceTypesSupported', [])
                                }
                                for m in claude_35_models[:10]
                            ],
                            "first_5_all_models": [
                                {
                                    "modelId": m.get('modelId'),
                                    "providerName": m.get('providerName')
                                }
                                for m in all_models[:5]
                            ]
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json_module.dumps(log_data) + "\n")
                except Exception as list_err:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "summarizer.py:110",
                        "message": "Error listing foundation models",
                        "data": {"error": str(list_err)},
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json_module.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Invoke Claude
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "summarizer.py:150",
                    "message": "Attempting invoke_model with current model_id",
                    "data": {
                        "model_id": self.model_id,
                        "body_size": len(body)
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json_module.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Try alternative model IDs if the configured one fails
            # Common Bedrock model ID formats for Claude 3.5 Sonnet
            model_ids_to_try = [
                self.model_id,  # Try configured ID first
                "anthropic.claude-3-5-sonnet-v2:0",
                "anthropic.claude-3-5-sonnet-v1:0",
                "anthropic.claude-3-sonnet-20240229-v1:0",  # Older format
                "us.anthropic.claude-3-5-sonnet-v1:0",
                "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Original format
            ]
            
            last_error = None
            for model_id_attempt in model_ids_to_try:
                # #region agent log
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "summarizer.py:200",
                        "message": "Trying model ID",
                        "data": {
                            "model_id_attempt": model_id_attempt,
                            "attempt_number": model_ids_to_try.index(model_id_attempt) + 1,
                            "total_attempts": len(model_ids_to_try)
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                        f.write(json_module.dumps(log_data) + "\n")
                except Exception:
                    pass
                # #endregion
                
                try:
                    response = self.bedrock_runtime.invoke_model(
                        modelId=model_id_attempt,
                        body=body
                    )
                    # #region agent log
                    try:
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "F",
                            "location": "summarizer.py:210",
                            "message": "Successfully invoked model",
                            "data": {
                                "successful_model_id": model_id_attempt
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                            f.write(json_module.dumps(log_data) + "\n")
                    except Exception:
                        pass
                    # #endregion
                    
                    # Success - break out of loop
                    if model_id_attempt != self.model_id:
                        print(f"Warning: Using alternative model ID {model_id_attempt} instead of {self.model_id}")
                    break
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    error_msg = str(e)
                    
                    # #region agent log
                    try:
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "G",
                            "location": "summarizer.py:230",
                            "message": "Model ID attempt failed",
                            "data": {
                                "model_id_attempt": model_id_attempt,
                                "error_code": error_code,
                                "error_message": error_msg,
                                "will_retry": 'ValidationException' in error_code and ('inference profile' in error_msg.lower() or 'invalid' in error_msg.lower())
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                            f.write(json_module.dumps(log_data) + "\n")
                    except Exception:
                        pass
                    # #endregion
                    
                    if 'ValidationException' in error_code and ('inference profile' in error_msg.lower() or 'invalid' in error_msg.lower()):
                        last_error = e
                        continue  # Try next model ID
                    else:
                        # Different error - re-raise
                        raise
                except Exception as e:
                    last_error = e
                    # #region agent log
                    try:
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "H",
                            "location": "summarizer.py:250",
                            "message": "Non-ClientError exception during model invocation",
                            "data": {
                                "model_id_attempt": model_id_attempt,
                                "error": str(e),
                                "error_type": str(type(e).__name__)
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                            f.write(json_module.dumps(log_data) + "\n")
                    except Exception:
                        pass
                    # #endregion
                    continue
            
            # If we exhausted all attempts, raise the last error
            if 'response' not in locals():
                if last_error:
                    raise last_error
                else:
                    raise RuntimeError("Failed to invoke Bedrock model with any available model ID")
            
            response_body = json.loads(response['body'].read())
            
            # Extract content
            content = response_body.get('content', [])
            if content:
                text = content[0].get('text', '')
                
                # Parse JSON from response
                # Claude might wrap JSON in markdown code blocks
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0].strip()
                elif '```' in text:
                    text = text.split('```')[1].split('```')[0].strip()
                
                summary_data = json.loads(text)
                
                return MeetingSummary(
                    executive_summary=summary_data.get('executive_summary', ''),
                    decisions=summary_data.get('decisions', []),
                    action_items=summary_data.get('action_items', []),
                    key_topics=summary_data.get('key_topics', [])
                )
            else:
                raise RuntimeError("Empty response from Claude")
        
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Claude response as JSON: {e}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = str(e)
            
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "D",
                    "location": "summarizer.py:137",
                    "message": "Bedrock ClientError caught",
                    "data": {
                        "error_code": error_code,
                        "error_message": error_message,
                        "model_id_used": self.model_id,
                        "response": str(e.response) if hasattr(e, 'response') else None
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
            
            # If ValidationException about inference profile, suggest alternatives
            if 'ValidationException' in error_code and 'inference profile' in error_message.lower():
                raise RuntimeError(
                    f"AWS Bedrock error: {error_message}\n"
                    f"Current model ID: {self.model_id}\n"
                    f"Try using an inference profile ID like 'anthropic.claude-3-5-sonnet-v2:0' "
                    f"or check available models in AWS Bedrock console."
                )
            raise RuntimeError(f"AWS Bedrock error: {error_message}")
        except Exception as e:
            raise RuntimeError(f"Summarization error: {str(e)}") from e



