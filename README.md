# Alt Text Generator

Lightweight alt text generation service using **Ollama** - no Python ML dependencies required.

A Flask-based REST API that generates accessible alt text descriptions for images using vision-language models. The service uses Ollama for model inference, eliminating the need for heavy Python ML dependencies like PyTorch or Transformers.

## Features

- 🚀 **Lightweight**: Minimal dependencies (just Flask and Requests)
- 🔒 **Secure**: Built-in SSRF protection and input validation
- 🖼️ **Flexible**: Supports JPEG, PNG, GIF, and WebP images
- ⚡ **Fast**: Efficient streaming image downloads with size limits
- 🎯 **Customizable**: Optional custom prompts for specialized descriptions
- 🏥 **Health Checks**: Built-in health monitoring endpoints (`/health` and `/up`)

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

| Aspect           | Transformers Version                 | Ollama Version              |
| ---------------- | ------------------------------------ | --------------------------- |
| Python deps      | PyTorch, Transformers, etc (~5-10GB) | Flask, Requests (~1MB)      |
| Model management | Manual HF cache                      | `ollama pull/list/rm`       |
| Setup complexity | Virtual env, CUDA, etc               | Single binary + one command |
| Portability      | Python 3.12+, CUDA                   | Any system Ollama supports  |

## Model

| Property       | Value       |
| -------------- | ----------- |
| **Model**      | qwen3-vl:4b |
| **Parameters** | 4B          |
| **Size**       | 3.3 GB      |
| **Runtime**    | Ollama      |

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

Returns API information including version, model name, and available endpoints.

**Response:**

```json
{
  "name": "Alt Text Generator API",
  "version": "1.0.0",
  "model": "qwen3-vl:4b",
  "endpoints": {
    "up": "/up",
    "health": "/health",
    "generate": "/generate"
  }
}
```

**Example:**

```bash
curl http://localhost:5000/
```

#### `GET /up`

Uptime check endpoint that verifies the model is available and loaded. Returns 200 if the service is ready, 503 if not. Useful for load balancer health checks.

**Response:**

**Success (200):**

```json
{
  "status": "up",
  "model": "qwen3-vl:4b",
  "model_available": true,
  "model_loaded": true
}
```

**Service Unavailable (503):**

```json
{
  "status": "down",
  "reason": "Model not available" | "Model not loaded" | "Ollama unreachable",
  "model": "qwen3-vl:4b",
  "model_available": false,
  "model_loaded": false
}
```

**Example:**

```bash
curl http://localhost:5000/up
```

#### `GET /health`

Health check endpoint that verifies Ollama is running and the required model is available. Provides detailed status information including all available models.

**Response:**

```json
{
  "status": "healthy",
  "ollama_reachable": true,
  "model": "qwen3-vl:4b",
  "model_available": true,
  "available_models": ["qwen3-vl:4b", ...]
}
```

**Example:**

```bash
curl http://localhost:5000/health
```

#### `GET /generate?imageUrl=<url>&prompt=<optional>`

Generate alt text for an image. Returns plain text response.

**Query Parameters:**

- `imageUrl` (required): URL of the image to caption. Supports both `imageUrl` and `image_url` parameter names.
- `prompt` (optional): Custom prompt for the model. Default: "Describe this image in one concise sentence for alt text."

**Response:**

- **Success (200)**: Plain text alt text description
- **Error (400)**: Validation error message (invalid URL, unsupported format, etc.)
- **Error (500)**: Internal server error message
- **Error (503)**: Ollama service unavailable

**Examples:**

Basic usage:

```bash
curl "http://localhost:5000/generate?imageUrl=https://fairdataihub.org/images/blog/ismb-2025/dorian-team.jpeg"
```

With custom prompt:

```bash
curl "http://localhost:5000/generate?imageUrl=https://example.com/image.jpg&prompt=Describe%20this%20image%20for%20a%20visually%20impaired%20user."
```

Using snake_case parameter:

```bash
curl "http://localhost:5000/generate?image_url=https://example.com/image.jpg"
```

## Configuration

### Environment Variables

| Variable       | Default                | Description                        |
| -------------- | ---------------------- | ---------------------------------- |
| `PORT`         | 5000                   | Server port                        |
| `OLLAMA_HOST`  | http://localhost:11434 | Ollama API URL                     |
| `OLLAMA_MODEL` | qwen3-vl:4b            | Vision model to use for generation |

### Image Constraints

The service enforces the following limits for security and performance:

- **Maximum image size**: 10 MiB
- **Supported formats**: JPEG, PNG, GIF, WebP
- **Maximum redirects**: 5 (prevents redirect loops)
- **Request timeout**: 30 seconds for image download, 120 seconds for generation

### Security Features

The service includes several security measures:

- **SSRF Protection**: Blocks access to private/internal IP ranges (localhost, 127.0.0.1, 10.x.x.x, 192.168.x.x, etc.)
- **URL Validation**: Only allows HTTP/HTTPS URLs
- **Content-Type Validation**: Only accepts known image MIME types
- **Size Limits**: Prevents memory exhaustion with configurable size limits
- **DNS Resolution Checks**: Validates resolved IP addresses to prevent DNS rebinding attacks

## Comparison with Transformers Version

| Metric         | Transformers (R-4B) | Ollama (qwen3-vl:4b) |
| -------------- | ------------------- | -------------------- |
| MMStar Score   | 72.6                | TBD (likely lower)   |
| Parameters     | 4.82B               | 4B                   |
| Python deps    | ~5-10GB             | ~1MB                 |
| Setup time     | 10-15 min           | 2 min                |
| Model download | ~10GB (HF)          | 3.3GB (Ollama)       |

## How It Works

1. **Image Fetching**: The service validates the provided URL, checks for SSRF vulnerabilities, and downloads the image with streaming to enforce size limits.

2. **Image Processing**: The downloaded image is converted to base64 format for transmission to Ollama.

3. **Caption Generation**: The base64 image and prompt are sent to Ollama's API, which uses the vision-language model to generate descriptive text.

4. **Response**: The generated alt text is returned as plain text to the client.

## Troubleshooting

### "Cannot connect to Ollama"

Make sure Ollama is running:

```bash
ollama serve
```

Check if Ollama is accessible:

```bash
curl http://localhost:11434/api/tags
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

### "Access to internal network resources is not allowed"

This error occurs when trying to access private/internal IP addresses. The service blocks these for security reasons. Use publicly accessible image URLs only.

### "Image too large" or "Unsupported content type"

- Ensure the image is under 10 MiB
- Verify the image format is JPEG, PNG, GIF, or WebP
- Check that the server returns the correct Content-Type header

### Health check shows "degraded" status

- Verify Ollama is running and accessible
- Check that the model specified in `OLLAMA_MODEL` is available
- Review the `available_models` list in the health check response

## Docker Deployment

### Using Docker Compose

The project includes a `docker-compose.yml` file for easy deployment with GPU support.

**Prerequisites:**

- Docker and Docker Compose installed
- Ollama running in an external network named `ollama-network`
- GPU access (if using GPU-accelerated inference)

**Deploy:**

```bash
# Set environment variables (optional)
export APP_PORT=23711
export RESTART_POLICY=unless-stopped

# Start the service
docker compose up -d --build
```

**Health Check:**

The Docker Compose configuration includes a health check that uses the `/up` endpoint:

```bash
# Check container health status
docker compose ps

# Manually test the /up endpoint
curl http://localhost:23711/up
```

**Configuration:**

- The service connects to Ollama via the `ollama-network` Docker network
- GPU device 0 is used by default (configured in `docker-compose.yml`)
- Port mapping: Host port (default: 23711) → Container port 5000
- Health check runs every 20 seconds with a 120-second startup grace period

### Using Dockerfile

Build and run the container manually:

```bash
# Build the image
docker build -t alt-text-generator .

# Run the container
docker run -p 5000:5000 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  alt-text-generator
```

## Development

### Code Quality

The project includes linting configuration:

- `.flake8` - Flake8 configuration for PEP 8 style checking
- `.pylint.ini` - Pylint configuration for code analysis

### Project Structure

```
alt-text-generator/
├── server.py           # Main Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image configuration
├── docker-compose.yml  # Docker Compose configuration
├── README.md           # This file
└── LICENSE             # MIT License
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for more information.
