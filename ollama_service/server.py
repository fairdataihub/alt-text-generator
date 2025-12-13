"""
Ollama-based Alt Text Generator API
====================================

Lightweight Flask API server using Ollama for VLM inference.
No Python ML dependencies required - just requests and flask.

Model: qwen3-vl:4b (via Ollama)

Prerequisites:
    1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh
    2. Pull the model: ollama pull qwen3-vl:4b
    3. Start Ollama: ollama serve

Usage:
    python ollama_service/server.py
    curl "http://localhost:5000/generate?imageUrl=https://example.com/image.jpg"
"""

import os
import base64
import logging
from io import BytesIO

import requests
from flask import Flask, request, jsonify, render_template_string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen3-vl:4b")
DEFAULT_PROMPT = "Describe this image in one concise sentence for alt text."

# Initialize Flask app
app = Flask(__name__)


def fetch_image_as_base64(image_url: str) -> str:
    """Download an image from URL and return as base64 string."""
    response = requests.get(image_url, timeout=30)
    response.raise_for_status()
    return base64.b64encode(response.content).decode('utf-8')


def generate_caption(image_base64: str, prompt: str = DEFAULT_PROMPT) -> str:
    """Generate a caption using Ollama's API."""
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()
    
    if "error" in result:
        raise RuntimeError(result["error"])
    
    return result.get("response", "").strip()


LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alt Text Generator (Ollama)</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { 
            font-size: 2.5rem; 
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #22c55e, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { color: #888; margin-bottom: 2rem; }
        .badge {
            display: inline-block;
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            margin-bottom: 1rem;
        }
        .model-info {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .model-info h2 { font-size: 1rem; color: #888; margin-bottom: 1rem; }
        .stats { display: flex; gap: 2rem; flex-wrap: wrap; }
        .stat-value { font-size: 1.5rem; font-weight: bold; color: #22c55e; }
        .stat-label { font-size: 0.85rem; color: #888; }
        .endpoint {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
        }
        .endpoint code { color: #22c55e; }
        .try-it {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(59, 130, 246, 0.2);
            border-radius: 8px;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .try-it a { color: #3b82f6; word-break: break-all; }
        .zero-deps {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(34, 197, 94, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(34, 197, 94, 0.2);
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="badge">Powered by Ollama</div>
        <h1>Alt Text Generator</h1>
        <p class="subtitle">Generate image descriptions using AI - zero Python ML dependencies</p>
        
        <div class="model-info">
            <h2>MODEL</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">qwen3-vl</div>
                    <div class="stat-label">4B parameters</div>
                </div>
                <div class="stat">
                    <div class="stat-value">3.3 GB</div>
                    <div class="stat-label">Model size</div>
                </div>
                <div class="stat">
                    <div class="stat-value">Ollama</div>
                    <div class="stat-label">Runtime</div>
                </div>
            </div>
        </div>
        
        <h2 style="margin-bottom: 1rem; font-size: 1rem; color: #888;">API USAGE</h2>
        
        <div class="endpoint">
            <code>GET /generate?imageUrl=&lt;url&gt;</code>
        </div>
        
        <div class="endpoint">
            <code>POST /generate</code> with JSON body: <code>{"imageUrl": "..."}</code>
        </div>
        
        <div class="try-it">
            <strong>Try it:</strong><br>
            <a href="/generate?imageUrl=https://dub.sh/confpic">/generate?imageUrl=https://dub.sh/confpic</a>
        </div>
        
        <div class="zero-deps">
            <strong>Zero ML Dependencies:</strong> This service uses Ollama for inference. 
            No PyTorch, TensorFlow, or heavy Python ML libraries required.
            Just <code>pip install flask requests</code>.
        </div>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    """Landing page."""
    return render_template_string(LANDING_PAGE)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    # Check if Ollama is reachable
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        ollama_ok = response.status_code == 200
        models = [m["name"] for m in response.json().get("models", [])]
        model_available = any(MODEL_NAME in m for m in models)
    except Exception as e:
        ollama_ok = False
        model_available = False
        models = []
    
    return jsonify({
        "status": "healthy" if ollama_ok and model_available else "degraded",
        "ollama_reachable": ollama_ok,
        "model": MODEL_NAME,
        "model_available": model_available,
        "available_models": models,
    })


@app.route("/generate", methods=["GET", "POST"])
def generate():
    """
    Generate alt text for an image.
    
    Query params (GET) or JSON body (POST):
        imageUrl: URL of the image to caption
        prompt: (optional) Custom prompt for the model
    
    Returns:
        JSON with "alt_text" field or "error" on failure
    """
    try:
        # Get parameters
        if request.method == "POST":
            data = request.get_json() or {}
            image_url = data.get("imageUrl") or data.get("image_url")
            prompt = data.get("prompt", DEFAULT_PROMPT)
        else:
            image_url = request.args.get("imageUrl") or request.args.get("image_url")
            prompt = request.args.get("prompt", DEFAULT_PROMPT)
        
        if not image_url:
            return jsonify({"error": "imageUrl parameter is required"}), 400
        
        logger.info(f"Generating caption for: {image_url}")
        
        # Fetch image and convert to base64
        image_b64 = fetch_image_as_base64(image_url)
        
        # Generate caption via Ollama
        alt_text = generate_caption(image_b64, prompt)
        
        logger.info(f"Generated: {alt_text[:100]}...")
        
        return jsonify({
            "alt_text": alt_text,
            "model": MODEL_NAME,
            "runtime": "ollama",
        })
        
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama")
        return jsonify({
            "error": "Cannot connect to Ollama. Is it running? Start with: ollama serve"
        }), 503
    except Exception as e:
        logger.error(f"Error generating caption: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info(f"Starting Ollama-based alt text server...")
    logger.info(f"Using model: {MODEL_NAME}")
    logger.info(f"Ollama host: {OLLAMA_HOST}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

