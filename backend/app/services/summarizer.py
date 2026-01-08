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
        
        self.aws_access_key_id = settings.aws_access_key_id
        self.aws_secret_access_key = settings.aws_secret_access_key
        self.aws_session_token = settings.aws_session_token
        self.aws_region = settings.aws_region
        self.model_id = settings.bedrock_model_id
        self._create_bedrock_client()
    
    def _create_bedrock_client(self):
        """Create or recreate the Bedrock runtime client with current credentials."""
        client_kwargs = {
            'aws_access_key_id': self.aws_access_key_id,
            'aws_secret_access_key': self.aws_secret_access_key,
            'region_name': self.aws_region
        }
        if self.aws_session_token:
            client_kwargs['aws_session_token'] = self.aws_session_token
        
        # #region agent log
        try:
            import json as json_module
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "TOKEN_H1",
                "location": "summarizer.py:_create_bedrock_client",
                "message": "Creating Bedrock client",
                "data": {
                    "has_session_token": bool(self.aws_session_token),
                    "session_token_preview": self.aws_session_token[:10] + "..." if self.aws_session_token else None,
                    "region": self.aws_region
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
        
        self.bedrock_runtime = boto3.client('bedrock-runtime', **client_kwargs)
    
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
    
    def _get_transcript_for_time_range(
        self,
        transcript: List[TranscriptSegment],
        start_time: float,
        end_time: float
    ) -> List[TranscriptSegment]:
        """Get transcript segments that overlap with a time range."""
        matching_segments = []
        for segment in transcript:
            # Check if segment overlaps with the time range
            if (segment.start <= end_time and segment.end >= start_time):
                matching_segments.append(segment)
        return matching_segments
    
    def generate_slide_summary(
        self,
        slide: UniqueSlide,
        transcript: List[TranscriptSegment]
    ) -> str:
        """
        Generate a summary for a single slide based on its OCR text and discussion during its appearance.
        
        Args:
            slide: The slide to summarize
            transcript: Full transcript segments
        
        Returns:
            Summary string for the slide
        """
        # Collect all transcript segments that overlap with any slide appearance
        relevant_segments = []
        for appearance in slide.appearances:
            segments = self._get_transcript_for_time_range(
                transcript,
                appearance.start,
                appearance.end
            )
            relevant_segments.extend(segments)
        
        # Remove duplicates (segments might overlap multiple appearances)
        seen = set()
        unique_segments = []
        for seg in relevant_segments:
            seg_id = (seg.start, seg.end, seg.text)
            if seg_id not in seen:
                seen.add(seg_id)
                unique_segments.append(seg)
        
        # Sort by timestamp
        unique_segments.sort(key=lambda x: x.start)
        
        # Format transcript for this slide
        transcript_text = ""
        if unique_segments:
            transcript_lines = []
            for segment in unique_segments:
                timestamp = f"[{int(segment.start//60)}:{int(segment.start%60):02d}]"
                speaker = f"Speaker {segment.speaker}: " if segment.speaker is not None else ""
                transcript_lines.append(f"{timestamp} {speaker}{segment.text}")
            transcript_text = "\n".join(transcript_lines)
        
        # Create prompt for slide-specific summary
        prompt = f"""You are analyzing a specific slide from a Microsoft Teams meeting recording along with the discussion that occurred while this slide was shown.

IMPORTANT CONTEXT ABOUT OCR TEXT:
- This slide was captured from a Teams meeting screen share
- Names appearing in the OCR text are typically participant names (real names from their Teams profiles)
- These names may appear in meeting participant lists, chat panels, or video call participant galleries visible on screen
- When you see names like "John Smith", "Jane Doe", etc. in the OCR text, these are likely meeting attendees
- Use these names to attribute discussion points or identify who was present/speaking

SLIDE CONTENT (OCR Text):
{slide.ocr_text}

DISCUSSION DURING SLIDE APPEARANCE:
{transcript_text if transcript_text else "No discussion captured during this slide's appearance."}

SLIDE APPEARANCE TIMES:
{', '.join([f"{int(app.start//60)}:{int(app.start%60):02d}" for app in slide.appearances])}

Please provide a concise summary (2-3 sentences) that:
1. Describes what the slide shows based on its text content
2. Summarizes the key points discussed while this slide was shown
3. Highlights any decisions, questions, or important information related to this slide
4. If participant names are visible in the OCR text, note who was present or being discussed

If there was no discussion during the slide's appearance, focus on summarizing what the slide content indicates.

Respond with only the summary text, no additional formatting or labels."""

        try:
            import json as json_module
            import time
            from botocore.exceptions import ClientError
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            # Try alternative model IDs if the configured one fails (same as main summary)
            model_ids_to_try = [
                self.model_id,
                "anthropic.claude-3-5-sonnet-v2:0",
                "anthropic.claude-3-5-sonnet-v1:0",
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "us.anthropic.claude-3-5-sonnet-v1:0",
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
            ]
            
            last_error = None
            for model_id_attempt in model_ids_to_try:
                try:
                    response = self.bedrock_runtime.invoke_model(
                        modelId=model_id_attempt,
                        body=body
                    )
                    break
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    error_msg = str(e)
                    if 'ValidationException' in error_code and ('inference profile' in error_msg.lower() or 'invalid' in error_msg.lower()):
                        last_error = e
                        continue
                    else:
                        raise
            
            if 'response' not in locals():
                if last_error:
                    raise last_error
                else:
                    raise RuntimeError("Failed to invoke Bedrock model for slide summary")
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            if content:
                summary_text = content[0].get('text', '').strip()
                return summary_text
            else:
                return None
        
        except Exception as e:
            print(f"Warning: Failed to generate slide summary: {e}")
            return None
    
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
        prompt = f"""You are an expert meeting analyst tasked with creating a comprehensive, detailed summary of a business meeting. Analyze the transcript and slide presentations thoroughly to extract all meaningful information.

TRANSCRIPT:
{transcript_text}

SLIDES SHOWN:
{slides_text}

INSTRUCTIONS FOR ANALYSIS:

1. EXECUTIVE SUMMARY:
   - Provide a comprehensive overview of the entire meeting
   - Include the meeting's primary purpose and objectives
   - Summarize the main discussion points and their context
   - Highlight the most important outcomes and conclusions
   - Note any significant concerns, challenges, or opportunities discussed
   - Connect the slide content to the discussion where relevant
   - Mention key participants and their roles/contributions if identifiable
   - Include the overall tone and sentiment of the meeting

2. KEY DECISIONS MADE:
   - List ALL decisions reached during the meeting, not just major ones
   - Include the rationale or context for each decision when mentioned
   - Note any decisions that were deferred or require follow-up
   - Include decisions about processes, strategies, priorities, or resource allocation
   - Specify any decisions related to the slide content presented
   - If decisions are conditional or have dependencies, note those details

3. ACTION ITEMS:
   - Extract ALL action items mentioned, even if not explicitly stated as such
   - Include the owner/assignee name if mentioned (e.g., "John will...", "Team needs to...")
   - Include deadlines or timeframes if mentioned (e.g., "by next week", "Q1 deadline")
   - Note the context or reason for each action item
   - Include follow-up tasks, next steps, and commitments made
   - Specify any action items related to slide content or presentations
   - If action items are vague, provide as much context as possible from the discussion

4. KEY TOPICS DISCUSSED:
   - List all major topics and themes covered in the meeting
   - Include subtopics and related discussion points
   - Note topics that were introduced by the slides
   - Include any recurring themes or concerns raised multiple times
   - Mention topics that generated significant discussion or debate
   - Include strategic, tactical, and operational topics
   - Note any topics that were mentioned but not fully explored (may need follow-up)

ANALYSIS GUIDELINES:
- Pay close attention to the relationship between slide content and discussion
- Identify patterns, trends, or themes across the conversation
- Note any contradictions, disagreements, or areas of uncertainty
- Extract specific metrics, numbers, dates, or quantitative information mentioned
- Identify stakeholders, departments, or external parties referenced
- Note any risks, concerns, or challenges raised
- Capture any opportunities, wins, or positive developments discussed
- Be thorough and comprehensive - it's better to include more detail than less

Format your response as JSON with the following structure:
{{
    "executive_summary": "A detailed 2-4 paragraph summary covering all aspects above...",
    "decisions": ["Decision 1 with context...", "Decision 2 with rationale...", "..."],
    "action_items": ["Action item with owner and deadline if mentioned...", "..."],
    "key_topics": ["Topic 1 with brief context...", "Topic 2...", "..."]
}}

Ensure each list item is comprehensive and self-contained. Respond only with valid JSON, no additional text."""

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
                            "hypothesisId": "TOKEN_H2",
                            "location": "summarizer.py:358",
                            "message": "Bedrock API call failed with ClientError",
                            "data": {
                                "model_id_attempt": model_id_attempt,
                                "error_code": error_code,
                                "error_message": error_msg,
                                "is_expired_token": error_code == 'ExpiredTokenException',
                                "has_session_token": bool(self.aws_session_token)
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("/Users/william.holden/Documents/meeting_summary_demo/.cursor/debug.log", "a") as f:
                            f.write(json_module.dumps(log_data) + "\n")
                    except Exception:
                        pass
                    # #endregion
                    
                    # Handle expired token by refreshing credentials and retrying
                    if error_code == 'ExpiredTokenException':
                        # #region agent log
                        try:
                            log_data = {
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "TOKEN_H3",
                                "location": "summarizer.py:384",
                                "message": "Detected ExpiredTokenException, attempting to refresh credentials",
                                "data": {
                                    "old_session_token_preview": self.aws_session_token[:10] + "..." if self.aws_session_token else None,
                                    "reloading_from_settings": True
                                },
                                "timestamp": int(__import__("time").time() * 1000)
                            }
                            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                                f.write(json_module.dumps(log_data) + "\n")
                        except Exception:
                            pass
                        # #endregion
                        
                        # Reload credentials from settings (in case they were updated)
                        from app.config import settings as current_settings
                        self.aws_access_key_id = current_settings.aws_access_key_id
                        self.aws_secret_access_key = current_settings.aws_secret_access_key
                        self.aws_session_token = current_settings.aws_session_token
                        
                        # Recreate the client with fresh credentials
                        self._create_bedrock_client()
                        
                        # #region agent log
                        try:
                            log_data = {
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "TOKEN_H4",
                                "location": "summarizer.py:406",
                                "message": "Recreated Bedrock client, retrying API call",
                                "data": {
                                    "new_session_token_preview": self.aws_session_token[:10] + "..." if self.aws_session_token else None,
                                    "retrying_model_id": model_id_attempt
                                },
                                "timestamp": int(__import__("time").time() * 1000)
                            }
                            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                                f.write(json_module.dumps(log_data) + "\n")
                        except Exception:
                            pass
                        # #endregion
                        
                        # Retry the API call once with the new client
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
                                    "hypothesisId": "TOKEN_H5",
                                    "location": "summarizer.py:425",
                                    "message": "Retry after token refresh succeeded",
                                    "data": {
                                        "successful_model_id": model_id_attempt
                                    },
                                    "timestamp": int(__import__("time").time() * 1000)
                                }
                                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                                    f.write(json_module.dumps(log_data) + "\n")
                            except Exception:
                                pass
                            # #endregion
                            
                            # Success - break out of loop
                            if model_id_attempt != self.model_id:
                                print(f"Warning: Using alternative model ID {model_id_attempt} instead of {self.model_id}")
                            break
                        except ClientError as retry_error:
                            # If retry also fails, raise the original error
                            last_error = e
                            continue
                    
                    elif 'ValidationException' in error_code and ('inference profile' in error_msg.lower() or 'invalid' in error_msg.lower()):
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
