# R-4B VLM Service

Local vision-language model service for alt text generation using the **R-4B** model.

## Model Info

| Property | Value |
|----------|-------|
| **Model** | [YannQi/R-4B](https://huggingface.co/YannQi/R-4B) |
| **Parameters** | 4.82B |
| **Base LLM** | Qwen3-4B |
| **Vision Encoder** | SigLip-400M |
| **MMStar Score** | 72.6 |
| **Release Date** | 2025/08/11 |

## Why R-4B?

Based on the [OpenVLM Leaderboard](https://huggingface.co/spaces/opencompass/open_vlm_leaderboard), R-4B is the top-performing model under 5B parameters for the MMStar benchmark, which measures multimodal reasoning and visual understanding.

## Requirements

- Python 3.12+
- NVIDIA GPU with ~10GB VRAM (or ~5GB with 4-bit quantization)
- CPU inference is possible but slow

## Setup

### 1. Create the virtual environment

```bash
# From project root
python3 -m venv vlm-env
source vlm-env/bin/activate
```

### 2. Install dependencies

```bash
pip install -r vlm_service/requirements.txt
```

### 3. (Optional) Enable 4-bit quantization for lower VRAM

```bash
pip install bitsandbytes
export VLM_4BIT=true
```

## Usage

### Start the server

```bash
source vlm-env/bin/activate
python vlm_service/server.py
```

The server runs on `http://localhost:5000` by default.

### API Endpoints

#### `GET /health`
Health check endpoint.

```bash
curl http://localhost:5000/health
```

#### `GET /generate?imageUrl=<url>`
Generate alt text for an image.

```bash
curl "http://localhost:5000/generate?imageUrl=https://dub.sh/confpic"
```

#### `POST /generate`
Generate alt text with more options.

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://example.com/image.jpg",
    "prompt": "Describe this image for a visually impaired user.",
    "thinking_mode": "short"
  }'
```

**Thinking modes:**
- `short` (default): Direct answer, fastest
- `auto`: Model decides based on complexity
- `long`: Detailed step-by-step reasoning

### Python API

```python
from vlm_service.inference import VLMInference

# Initialize (loads model into GPU memory)
vlm = VLMInference()

# Generate caption
caption = vlm.generate_caption("https://example.com/image.jpg")
print(caption)

# With custom prompt
caption = vlm.generate_caption(
    "https://example.com/image.jpg",
    prompt="What objects are visible in this image?",
    thinking_mode="long"
)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VLM_PORT` | 5000 | Port for Flask server |
| `VLM_4BIT` | false | Enable 4-bit quantization |

## Integration with Next.js

The Next.js API at `/api/generate` can be updated to call this local service instead of Replicate:

```typescript
// pages/api/generate.ts
const VLM_SERVICE_URL = process.env.VLM_SERVICE_URL || "http://localhost:5000";

export default async function handler(req, res) {
  const { imageUrl } = req.query;
  
  const response = await fetch(
    `${VLM_SERVICE_URL}/generate?imageUrl=${encodeURIComponent(imageUrl)}`
  );
  const data = await response.json();
  
  res.status(200).json(data.alt_text);
}
```

## Comparison with Previous Setup

| Aspect | Old (BLIP/Replicate) | New (R-4B Local) |
|--------|---------------------|------------------|
| Model | BLIP | R-4B |
| Parameters | ~500M | 4.82B |
| MMStar | N/A | 72.6 |
| Hosting | Replicate (paid) | Local (free) |
| Latency | ~2-5s (API calls) | ~1-2s (local GPU) |
| Cost | Per-request | One-time GPU |

## Troubleshooting

### CUDA out of memory
Enable 4-bit quantization:
```bash
pip install bitsandbytes
export VLM_4BIT=true
```

### Model download issues
Ensure you're logged into Hugging Face:
```bash
huggingface-cli login
```

### Slow inference on CPU
R-4B is designed for GPU inference. For CPU-only systems, consider:
- Using a smaller model like Moondream 0.5B
- Running on a cloud GPU instance

