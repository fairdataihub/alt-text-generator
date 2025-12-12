"""
R-4B Alt Text Generator API
============================

Standalone Flask API server for generating image alt text using the R-4B VLM.

Endpoints:
    GET /         - Landing page
    GET /health   - Health check (JSON)
    GET/POST /generate?imageUrl=<url> - Generate alt text

Usage:
    source vlm-env/bin/activate
    python vlm_service/server.py
    
    curl "http://localhost:5000/generate?imageUrl=https://example.com/image.jpg"
"""

import os
import logging

# Force use of GPU 0 (e.g., RTX 4090) to avoid multi-GPU memory issues
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

from flask import Flask, request, jsonify, render_template_string
from inference import VLMInference

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global VLM instance (loaded on startup)
vlm: VLMInference = None


def get_vlm() -> VLMInference:
    """Get or initialize the VLM instance."""
    global vlm
    if vlm is None:
        logger.info("Initializing VLM model...")
        vlm = VLMInference(
            load_in_4bit=os.environ.get("VLM_4BIT", "false").lower() == "true"
        )
    return vlm


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "model": "YannQi/R-4B",
        "model_loaded": vlm is not None,
    })


@app.route("/generate", methods=["GET", "POST"])
def generate():
    """
    Generate alt text for an image.
    
    Query params (GET) or JSON body (POST):
        imageUrl: URL of the image to caption
        prompt: (optional) Custom prompt for the model
        thinking_mode: (optional) "auto", "long", or "short" (default: "short")
    
    Returns:
        JSON with "alt_text" field or "error" on failure
    """
    try:
        # Get parameters
        if request.method == "POST":
            data = request.get_json() or {}
            image_url = data.get("imageUrl") or data.get("image_url")
            prompt = data.get("prompt")
            thinking_mode = data.get("thinking_mode", "short")
        else:
            image_url = request.args.get("imageUrl") or request.args.get("image_url")
            prompt = request.args.get("prompt")
            thinking_mode = request.args.get("thinking_mode", "short")
        
        if not image_url:
            return jsonify({"error": "imageUrl parameter is required"}), 400
        
        logger.info(f"Generating caption for: {image_url}")
        
        # Get VLM and generate caption
        model = get_vlm()
        
        kwargs = {
            "image_source": image_url,
            "thinking_mode": thinking_mode,
        }
        if prompt:
            kwargs["prompt"] = prompt
        
        alt_text = model.generate_caption(**kwargs)
        
        logger.info(f"Generated: {alt_text[:100]}...")
        
        return jsonify({
            "alt_text": alt_text,
            "model": "YannQi/R-4B",
        })
        
    except Exception as e:
        logger.error(f"Error generating caption: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alt Text Generator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { 
            font-size: 2.5rem; 
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { color: #888; margin-bottom: 2rem; }
        .model-info {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .model-info h2 { font-size: 1rem; color: #888; margin-bottom: 1rem; }
        .stats { display: flex; gap: 2rem; flex-wrap: wrap; }
        .stat { }
        .stat-value { font-size: 1.5rem; font-weight: bold; color: #00d4ff; }
        .stat-label { font-size: 0.85rem; color: #888; }
        .endpoint {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
        }
        .endpoint code { color: #00d4ff; }
        a { color: #7b2cbf; }
        .try-it {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(123, 44, 191, 0.2);
            border-radius: 8px;
            border: 1px solid rgba(123, 44, 191, 0.3);
        }
        .try-it a { 
            color: #00d4ff; 
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Alt Text Generator</h1>
        <p class="subtitle">Generate image descriptions using AI</p>
        
        <div class="model-info">
            <h2>MODEL</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">R-4B</div>
                    <div class="stat-label">YannQi/R-4B</div>
                </div>
                <div class="stat">
                    <div class="stat-value">72.6</div>
                    <div class="stat-label">MMStar Score</div>
                </div>
                <div class="stat">
                    <div class="stat-value">4.82B</div>
                    <div class="stat-label">Parameters</div>
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
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    """Landing page."""
    return render_template_string(LANDING_PAGE)


if __name__ == "__main__":
    # Pre-load model on startup
    logger.info("Starting R-4B VLM server...")
    get_vlm()
    
    # Run server
    port = int(os.environ.get("VLM_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

