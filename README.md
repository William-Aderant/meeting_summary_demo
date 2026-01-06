# Meeting Video Processing Application

A full-stack web application that automatically processes meeting videos to extract transcripts, generate summaries, and identify unique slides using multimodal AI.

## Features

- **Automated Transcription**: Uses AWS Transcribe for high-quality speech-to-text with word-level timestamps and speaker diarization
- **Intelligent Summarization**: Claude 3.5 Sonnet via Amazon Bedrock generates executive summaries, decisions, and action items
- **Slide Detection & Deduplication**: 
  - Scene detection using AWS Rekognition
  - CLIP embeddings for visual similarity
  - OCR text extraction for content matching
  - Automatic deduplication of repeated slides
- **Modern UI**: Next.js frontend with drag-and-drop upload and real-time status updates

## Architecture

```
Frontend (Next.js) → Backend (FastAPI) → Processing Pipeline
  ├─ Video Upload
  ├─ Status Polling
  └─ Results Display
```

### Processing Pipeline

1. Audio extraction (FFmpeg)
2. Scene detection (AWS Rekognition)
3. Frame extraction (FFmpeg)
4. Slide fingerprinting (CLIP + OCR)
5. Deduplication
6. Transcription (AWS Transcribe)
7. Summarization (Claude Bedrock)
8. Results assembly

## Prerequisites

- Python 3.9+
- Node.js 18+
- FFmpeg installed and in PATH
- AWS account with access to:
  - S3 (for video storage and transcription)
  - Transcribe (for speech-to-text)
  - Rekognition (for scene detection and OCR)
  - Bedrock (for Claude API)

## Installation

### Backend

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file (see `.env.example`):
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

5. Create necessary directories:
```bash
mkdir -p uploads temp results
```

6. Run the server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Usage

1. Open the application in your browser
2. Drag and drop a meeting video file (MP4, MOV, AVI, MKV, WebM, M4V)
3. Wait for processing to complete (may take several minutes for long videos)
4. View the results:
   - Executive summary
   - Key decisions
   - Action items
   - Unique slides gallery

## Configuration

### Environment Variables

**Backend:**
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (default: us-east-1)
- `S3_BUCKET_NAME`: S3 bucket for video storage and transcription (required)
- `BEDROCK_MODEL_ID`: Bedrock model ID (default: Claude 3.5 Sonnet)
- `UPLOAD_DIR`: Local upload directory (default: ./uploads)
- `TEMP_DIR`: Temporary processing directory (default: ./temp)
- `RESULTS_DIR`: Results storage directory (default: ./results)

**Frontend:**
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

### Processing Settings

Edit `backend/app/config.py` to adjust:
- `frame_extraction_interval`: Interval for periodic frame extraction (default: 2.0 seconds)
- `clip_similarity_threshold`: CLIP similarity threshold for deduplication (default: 0.95)
- `ocr_text_similarity_threshold`: OCR text similarity threshold (default: 0.8)

## Project Structure

```
meeting_summary_demo/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Data models
│   │   ├── services/     # Processing services
│   │   ├── config.py     # Configuration
│   │   └── main.py       # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # Utilities
│   └── package.json
└── README.md
```

## API Endpoints

### Backend (FastAPI)

- `POST /api/upload` - Upload video file
- `GET /api/status/{job_id}` - Get processing status
- `GET /api/results/{job_id}` - Get final results
- `GET /api/results/{job_id}/slide/{slide_id}` - Get slide image

## Troubleshooting

### FFmpeg not found
Install FFmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: Download from https://ffmpeg.org/

### CLIP model download
The first run will download the CLIP model (~500MB). Ensure you have internet connectivity.

### AWS credentials
Ensure AWS credentials are properly configured. The application will fall back to local processing if AWS services are unavailable.

### AWS Transcribe/Bedrock errors
Check that AWS credentials are correct and services are accessible. Ensure S3_BUCKET_NAME is configured as it's required for AWS Transcribe. The application will show warnings if services are unavailable.

## License

MIT
