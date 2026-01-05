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
    
    # Deepgram Configuration
    deepgram_api_key: Optional[str] = None
    
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

