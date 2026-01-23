# Alt Text Generator (Ollama Edition)

Lightweight alt text generation service using **Ollama** - no Python ML dependencies required.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/fairdataihub/alt-text-generator.git
cd alt-text-generator

# Install Ollama and pull the vision model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3-vl:4b

# Install Python dependencies and start the server
pip install -r requirements.txt
python server.py
```

## Why Ollama?

| Aspect | Transformers Version | Ollama Version |
|--------|---------------------|----------------|
| Python deps | PyTorch, Transformers, etc (~5-10GB) | Flask, Requests (~1MB) |
| Model management | Manual HF cache | `ollama pull/list/rm` |
| Setup complexity | Virtual env, CUDA, etc | Single binary + one command |
| Portability | Python 3.10+, CUDA | Any system Ollama supports |

## Model

| Property | Value |
|----------|-------|
| **Model** | qwen3-vl:4b |
| **Parameters** | 4B |
| **Size** | 3.3 GB |
| **Runtime** | Ollama |

## Prerequisites

### 1. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull the model

```bash
ollama pull qwen3-vl:4b
```

### 3. Start Ollama (if not running as a service)

```bash
ollama serve
```

## Setup

### Install Python dependencies (minimal!)

```bash
pip install -r requirements.txt
# That's it! No PyTorch, no Transformers, no CUDA toolkit
```

Or install directly:

```bash
pip install flask requests
```

## Usage

### Start the server

```bash
python server.py
```

Server runs on `http://localhost:5000` by default.

### API Endpoints

#### `GET /`
Landing page with API info.

#### `GET /health`
Health check - verifies Ollama is running and model is available.

```bash
curl http://localhost:5000/health
```

#### `GET /generate?imageUrl=<url>`
Generate alt text for an image.

```bash
curl "http://localhost:5000/generate?imageUrl=https://fairdataihub.org/images/blog/ismb-2025/dorian-team.jpeg"
```

#### `POST /generate`
Generate alt text with custom prompt.

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://example.com/image.jpg",
    "prompt": "Describe this image for a visually impaired user."
  }'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Server port |
| `OLLAMA_HOST` | http://localhost:11434 | Ollama API URL |
| `OLLAMA_MODEL` | qwen3-vl:4b | Model to use |

## Comparison with Transformers Version

| Metric | Transformers (R-4B) | Ollama (qwen3-vl:4b) |
|--------|--------------------|-----------------------|
| MMStar Score | 72.6 | TBD (likely lower) |
| Parameters | 4.82B | 4B |
| Python deps | ~5-10GB | ~1MB |
| Setup time | 10-15 min | 2 min |
| Model download | ~10GB (HF) | 3.3GB (Ollama) |

## Troubleshooting

### "Cannot connect to Ollama"
Make sure Ollama is running:
```bash
ollama serve
```

### Model not found
Pull the model:
```bash
ollama pull qwen3-vl:4b
```

### Check available models
```bash
ollama list
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for more information.
