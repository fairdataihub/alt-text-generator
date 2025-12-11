"""
Flask API Server for R-4B VLM Inference
========================================

Provides a REST API for the Next.js frontend to call for image captioning.

Endpoints:
    GET /health - Health check
    POST /generate - Generate alt text for an image
    GET /generate?imageUrl=<url> - Generate alt text (GET variant)

Usage:
    source vlm-env/bin/activate
    python vlm_service/server.py
    
    # Then the Next.js app can call:
    curl "http://localhost:5000/generate?imageUrl=https://example.com/image.jpg"
"""

import os
import logging

# Force use of GPU 0 (e.g., RTX 4090) to avoid multi-GPU memory issues
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

from flask import Flask, request, jsonify
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


@app.route("/", methods=["GET"])
def index():
    """Root endpoint with API info."""
    return jsonify({
        "name": "R-4B Alt Text Generator API",
        "model": "YannQi/R-4B",
        "mmstar_score": 72.6,
        "parameters": "4.82B",
        "endpoints": {
            "/health": "GET - Health check",
            "/generate": "GET/POST - Generate alt text (requires imageUrl param)",
        },
        "example": "/generate?imageUrl=https://example.com/image.jpg"
    })


if __name__ == "__main__":
    # Pre-load model on startup
    logger.info("Starting R-4B VLM server...")
    get_vlm()
    
    # Run server
    port = int(os.environ.get("VLM_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

