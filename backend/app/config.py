"""Configuration management for the application."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None  # For temporary credentials
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # AWS Transcribe Configuration
    # Note: AWS Transcribe requires S3 for audio storage
    
    # Bedrock Configuration
    # Use inference profile format for on-demand throughput
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-v2:0"
    
    # Application Configuration
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    results_dir: str = "./results"
    
    # Processing Configuration
    frame_extraction_interval: float = 5.0  # Extract frame every N seconds (increased from 2.0 to reduce processing)
    skip_periodic_extraction: bool = False  # If True, only extract at scene boundaries (faster but may miss slides)
    use_fast_prefilter: bool = True  # Use fast perceptual hash to skip similar frames before expensive CLIP/OCR
    clip_similarity_threshold: float = 0.95  # CLIP cosine similarity threshold
    ocr_text_similarity_threshold: float = 0.8  # OCR text similarity threshold
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables (like AWS_SESSION_TOKEN)
    )


settings = Settings()
# #region agent log
try:
    import json as json_module
    import os
    log_data = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "CONFIG_LOAD",
        "location": "config.py:settings_init",
        "message": "Settings loaded from environment",
        "data": {
            "has_access_key_id": bool(settings.aws_access_key_id),
            "access_key_id_length": len(settings.aws_access_key_id) if settings.aws_access_key_id else 0,
            "access_key_id_preview": settings.aws_access_key_id[:8] + "..." if settings.aws_access_key_id and len(settings.aws_access_key_id) > 8 else (settings.aws_access_key_id if settings.aws_access_key_id else None),
            "has_secret_access_key": bool(settings.aws_secret_access_key),
            "secret_key_length": len(settings.aws_secret_access_key) if settings.aws_secret_access_key else 0,
            "has_session_token": bool(settings.aws_session_token),
            "aws_region": settings.aws_region,
            "s3_bucket_name": settings.s3_bucket_name,
            "env_aws_access_key_id": bool(os.getenv("AWS_ACCESS_KEY_ID")),
            "env_aws_secret_access_key": bool(os.getenv("AWS_SECRET_ACCESS_KEY")),
            "env_aws_region": os.getenv("AWS_REGION"),
            "env_s3_bucket_name": os.getenv("S3_BUCKET_NAME")
        },
        "timestamp": int(__import__("time").time() * 1000)
    }
    with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
        f.write(json_module.dumps(log_data) + "\n")
except Exception:
    pass
# #endregion

