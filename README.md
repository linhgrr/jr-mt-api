# Japanese Railway Translation API

A FastAPI-based service for translating Japanese railway announcements to English.

## Overview

This API translates Japanese railway-related text to English while properly handling railway entities like station names and line names. It uses specialized machine learning models for both Named Entity Recognition (NER) and translation, ensuring accurate translation of railway-specific terminology.

## Features

- **Intelligent Entity Recognition**: Identifies and handles railway entities (stations, lines, etc.)
- **Hybrid Translation Approach**: Combines CSV mappings, Wikidata lookup, and machine translation
- **Railway-Specific Models**: Uses fine-tuned models for Japanese railway domain
- **RESTful API**: Clean and well-documented API endpoints
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Health Monitoring**: Built-in health check endpoints
- **Error Handling**: Comprehensive error handling with fallback mechanisms

## Architecture

The application follows SOLID principles with a modular architecture:

```
app/
├── core/           # Configuration and settings
├── models/         # Pydantic models for request/response
├── services/       # Business logic services
│   ├── ner_service.py         # Named Entity Recognition
│   ├── translation_service.py # Translation logic
│   └── orchestrator.py        # Main service orchestrator
├── routers/        # API route handlers
├── utils/          # Utility functions
└── main.py         # FastAPI application
```

## API Endpoints

### POST `/api/v1/translate`

Translate Japanese text to English.

**Request:**
```json
{
  "text": "まもなく、品川、品川。お出口は右側です。"
}
```

**Response:**
```json
{
  "translation": "Soon, Shinagawa, Shinagawa. The exit is on the right side."
}
```

### GET `/api/v1/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Japanese Railway Translation API"
}
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB of available RAM
- Internet connection for downloading models

### 1. Clone and Setup

```bash
git clone <repository-url>
cd japanese-railway-translation-api
```

### 2. Build and Run with Docker Compose

```bash
# Build and start the service
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The API will be available at `http://localhost:8000`

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Translation test
curl -X POST "http://localhost:8000/api/v1/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "まもなく、品川、品川。お出口は右側です。"}'
```

## Manual Installation

### Prerequisites

- Python 3.11+
- MeCab (Japanese morphological analyzer)

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mecab mecab-ipadic-utf8 libmecab-dev build-essential
```

**macOS:**
```bash
brew install mecab mecab-ipadic
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker Usage

### Build Image

```bash
docker build -t japanese-railway-translation-api .
```

### Run Container

```bash
docker run -d \
  --name translation-api \
  -p 8000:8000 \
  -v $(pwd)/train_entity.csv:/app/train_entity.csv:ro \
  japanese-railway-translation-api
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Usage Examples

### Python

```python
import requests

url = "http://localhost:8000/api/v1/translate"
data = {"text": "この電車は大阪行きです。"}

response = requests.post(url, json=data)
result = response.json()
print(result["translation"])
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "この電車は大阪行きです。次は新宿、新宿です。"}'
```

### JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

async function translate(text) {
  const response = await fetch('http://localhost:8000/api/v1/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  
  const result = await response.json();
  return result.translation;
}

translate("まもなく、品川、品川。").then(console.log);
```

## Configuration

The application can be configured using environment variables or a `.env` file:

```env
# Application Settings
DEBUG=false
APP_NAME="Japanese Railway Translation API"

# Model Settings
NER_MODEL_NAME="linhdzqua148/xlm-roberta-ner-japanese-railway"
TRANSLATION_MODEL_NAME="linhdzqua148/jrw-mt-ja-en"

# File Paths
ENTITY_CSV_PATH="./train_entity.csv"

# Device Settings
USE_CUDA=true

# API Settings
MAX_TEXT_LENGTH=1000
REQUEST_TIMEOUT=30
```

## Translation Process

The API follows a sophisticated translation pipeline:

![Translation Process Diagram](https://i.ibb.co/pBJzYTqT/Untitled-1.png)

1. **Entity Recognition**: Identifies railway entities (stations, lines) in the input text
2. **Entity Normalization**: Normalizes entity names (removes suffixes, splits numbers)
3. **Placeholder Replacement**: Replaces entities with placeholders in the text
4. **Entity Translation**: Translates entities using:
   - CSV mapping (highest priority)
   - Wikidata lookup (fallback)
   - Original text (if no translation found)
5. **Text Translation**: Translates the main text using the specialized model
6. **Result Merging**: Combines translated text with translated entities
7. **Post-processing**: Removes duplicates and fixes formatting

## Models Used

- **NER Model**: `linhdzqua148/xlm-roberta-ner-japanese-railway`
  - Fine-tuned XLM-RoBERTa for Japanese railway entity recognition
  
- **Translation Model**: `linhdzqua148/jrw-mt-ja-en`
  - Fine-tuned MarianMT for Japanese-English railway domain translation

## Performance

- **Cold Start**: ~30-60 seconds (model loading)
- **Warm Requests**: ~1-3 seconds per translation
- **Memory Usage**: ~2-4GB (depending on GPU usage)
- **Throughput**: ~10-20 requests/second

## Monitoring and Health Checks

The API includes built-in health monitoring:

- **Health Endpoint**: `/api/v1/health`
- **Docker Health Check**: Automatic container health monitoring
- **Graceful Shutdown**: Proper cleanup on container stop

## Error Handling

The API implements comprehensive error handling:

- **Input Validation**: Validates request format and text length
- **Model Fallbacks**: Falls back to simpler translation if advanced pipeline fails
- **Graceful Degradation**: Returns partial results rather than complete failure
- **Detailed Logging**: Comprehensive logging for debugging

## Limitations

- **Domain Specific**: Optimized for railway announcements and related text
- **Model Size**: Requires significant memory for model loading
- **Language Support**: Currently supports Japanese to English only
- **Entity Coverage**: Entity recognition limited to railway domain

## Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce batch size or disable CUDA
2. **Model Loading Fails**: Check internet connection and model availability
3. **MeCab Errors**: Ensure MeCab is properly installed
4. **Permission Errors**: Check file permissions for CSV files

### Logs

```bash
# View application logs
docker-compose logs translation-api

# Follow logs in real-time
docker-compose logs -f translation-api
```

## Development

### Project Structure

```
├── app/
│   ├── core/               # Configuration
│   ├── models/             # Pydantic models
│   ├── services/           # Business logic
│   ├── routers/            # API routes
│   ├── utils/              # Utilities
│   └── main.py             # FastAPI app
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose
├── requirements.txt        # Python dependencies
├── train_entity.csv        # Entity mappings
└── README.md              # Documentation
```

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```
