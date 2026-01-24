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
    python server.py
    curl "http://localhost:5000/generate?imageUrl=https://example.com/image.jpg"
"""

import os
import base64
import logging
from contextlib import suppress
from urllib.parse import urlparse, urljoin
import socket
import ipaddress

import requests
from flask import Flask, request, jsonify

# Configure logging
# Set up logging to output timestamps, logger name, level, and message
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
# Get Ollama host from environment variable, default to localhost
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# Get model name from environment variable, default to qwen3-vl:4b
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen3-vl:4b")
# Default prompt used for generating alt text if user doesn't provide one
DEFAULT_PROMPT = "Describe this image in one concise sentence for alt text."

# Image fetch constraints
# Maximum allowed image size: 10 MiB (prevents memory exhaustion)
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MiB
# Only allow these image MIME types to prevent malicious file uploads
ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/jpg",
}
# Maximum number of HTTP redirects to follow (prevents redirect loops)
MAX_REDIRECTS = 5
# Maximum prompt length to prevent DoS attacks
MAX_PROMPT_LENGTH = 2000  # characters

# Blocked IP ranges for SSRF protection
# These are private/internal IP ranges that should not be accessible
# Prevents Server-Side Request Forgery attacks
BLOCKED_IP_PREFIXES = (
    "100.",
    "127.",
    "10.",
    "192.168.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "0.",
    "169.254.",
    "::1",
    "fc00:",
    "fe80:",
    "localhost",
)

# Initialize Flask app
app = Flask(__name__)


def validate_url(url: str) -> None:
    """
    Validate URL to prevent SSRF attacks.
    Raises ValueError if URL is invalid or points to blocked resources.
    """
    # Check URL length to prevent DoS attacks
    if len(url) > 2048:
        raise ValueError("URL is too long (maximum 2048 characters)")

    # Parse the URL into components (scheme, netloc, path, etc.)
    parsed = urlparse(url)

    # Enforce http/https only
    # Block file://, ftp://, and other potentially dangerous schemes
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed")

    # Ensure the URL has a hostname/netloc component
    if not parsed.netloc:
        raise ValueError("Invalid URL: missing host")

    # Block URLs with credentials (username:password@host)
    # This prevents leaking credentials and reduces attack surface
    if parsed.username or parsed.password:
        raise ValueError("URLs with credentials are not allowed")

    # Extract hostname (handle port if present)
    # parsed.hostname already strips the port, but fallback handles edge cases
    hostname = parsed.hostname or parsed.netloc.split(":")[0]

    # Block localhost and private IPs by hostname
    # Check if hostname matches any blocked prefix (e.g., "localhost", "127.0.0.1")
    hostname_lower = hostname.lower()
    if any(
        hostname_lower.startswith(prefix) or hostname_lower == prefix.rstrip(".")
        for prefix in BLOCKED_IP_PREFIXES
    ):
        raise ValueError("Access to internal network resources is not allowed")

    # Resolve hostname and check IP (IPv4 and IPv6)
    # Even if hostname looks safe, resolve it to IP and check if IP is blocked
    # This prevents DNS rebinding attacks where a public hostname resolves to private IP
    try:
        # Use getaddrinfo to handle both IPv4 and IPv6 addresses
        addrinfos = socket.getaddrinfo(hostname, None)

        # Explicit network ranges for private / loopback / link-local addresses
        # Using ip_network here avoids brittle string-prefix checks
        private_networks = (
            ipaddress.ip_network("10.0.0.0/8"),        # IPv4 private
            ipaddress.ip_network("172.16.0.0/12"),      # IPv4 private
            ipaddress.ip_network("192.168.0.0/16"),    # IPv4 private
            ipaddress.ip_network("127.0.0.0/8"),       # IPv4 loopback
            ipaddress.ip_network("169.254.0.0/16"),    # IPv4 link-local
            ipaddress.ip_network("::1/128"),            # IPv6 loopback
            ipaddress.ip_network("fc00::/7"),           # IPv6 unique local
            ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
        )

        for family, _, _, _, sockaddr in addrinfos:
            ip_str = sockaddr[0]

            # Normalize to an ipaddress object (handles both IPv4 and IPv6)
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                # Skip any unusual/non-IP results
                continue

            # Block clearly non-public targets
            # Check built-in properties and explicit network ranges
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or any(ip_obj in net for net in private_networks)
            ):
                raise ValueError("Access to internal network resources is not allowed")

    except socket.gaierror as e:
        # DNS resolution failed - reject the URL
        raise ValueError(f"Unable to resolve hostname: {hostname}") from e


def fetch_image_as_base64(image_url: str) -> str:
    """
    Download an image from URL and return as base64 string.
    Includes validation for content type, size limits, and redirect restrictions.
    Manually handles redirects with validation to prevent SSRF attacks.
    """
    # Validate URL before fetching to prevent SSRF attacks
    validate_url(image_url)

    # Use a session for connection pooling (but disable automatic redirects)
    with requests.Session() as session:
        current_url = image_url
        redirect_count = 0
        response = None

        # Manually follow redirects with validation
        while True:
            # Fetch the URL with redirects disabled to validate each target
            response = session.get(
                current_url,
                timeout=30,  # 30 second timeout to prevent hanging requests
                stream=True,  # Stream the response instead of loading it all at once
                allow_redirects=False,  # Disable automatic redirects - we'll handle them manually
            )

            # Check if this is a redirect response (3xx status codes)
            if response.status_code in {301, 302, 303, 307, 308}:
                redirect_count += 1

                # Enforce maximum redirect depth
                if redirect_count > MAX_REDIRECTS:
                    raise ValueError(
                        f"Too many redirects (maximum {MAX_REDIRECTS} allowed)"
                    )

                # Extract the redirect target from Location header
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("Redirect response missing Location header")

                # Resolve relative redirects against the current URL
                # urljoin handles both absolute and relative URLs correctly
                redirect_url = urljoin(current_url, location)

                # Validate the redirect target URL to prevent SSRF
                # This is critical - we must validate every redirect target
                validate_url(redirect_url)

                # Optional: Forbid cross-host redirects for additional security
                # This prevents redirects from public hosts to internal hosts
                current_parsed = urlparse(current_url)
                redirect_parsed = urlparse(redirect_url)
                if current_parsed.netloc.lower() != redirect_parsed.netloc.lower():
                    # Cross-host redirect detected - reject for security
                    raise ValueError(
                        "Cross-host redirects are not allowed for security reasons"
                    )

                # Follow the redirect
                current_url = redirect_url
                continue

            # Not a redirect - check for errors and proceed with content validation
            response.raise_for_status()

            # Validate content type
            # Extract MIME type from Content-Type header (ignore charset and other parameters)
            content_type = response.headers.get("Content-Type", "")
            mime_type = content_type.split(";", 1)[0].strip().lower()
            # Only allow known image types to prevent downloading malicious files
            if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
                raise ValueError(
                    f"Unsupported content type: {mime_type}. Expected an image."
                )

            # Check declared content length if available
            # This is an early check before downloading the entire file
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                # Suppress ValueError if Content-Length is not a valid integer
                with suppress(ValueError):
                    length = int(content_length)
                    # Reject files that are too large before downloading
                    if length > MAX_IMAGE_BYTES:
                        raise ValueError(
                            f"Image too large ({length // (1024*1024)}MB). "
                            f"Maximum allowed: {MAX_IMAGE_BYTES // (1024*1024)}MB"
                        )

            # Stream content and enforce max size
            # Read the image in chunks to avoid loading everything into memory
            chunks = bytearray()
            for chunk in response.iter_content(chunk_size=8192):  # 8KB chunks
                if chunk:
                    chunks.extend(chunk)
                    # Check size after each chunk to stop early if too large
                    # (Some servers don't send Content-Length header)
                    if len(chunks) > MAX_IMAGE_BYTES:
                        raise ValueError(
                            f"Image exceeded maximum size of {MAX_IMAGE_BYTES // (1024*1024)}MB"
                        )

            # Convert binary image data to base64 string for Ollama API
            return base64.b64encode(bytes(chunks)).decode("utf-8")


def generate_caption(image_base64: str, prompt: str = DEFAULT_PROMPT) -> str:
    """Generate a caption using Ollama's API."""
    # Send POST request to Ollama's generate endpoint
    # The image is passed as base64-encoded string in the images array
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL_NAME,  # Specify which vision model to use
            "prompt": prompt,  # The text prompt describing what to generate
            "images": [image_base64],  # Base64-encoded image(s) to analyze
            "stream": False,  # Get complete response at once (not streaming)
        },
        timeout=120,  # 2 minute timeout (image processing can take time)
    )
    # Raise exception if HTTP request failed
    response.raise_for_status()
    # Parse JSON response from Ollama
    result = response.json()

    # Check if Ollama returned an error in the response
    if "error" in result:
        raise RuntimeError(result["error"])

    # Extract and return the generated text, stripping whitespace
    return result.get("response", "").strip()


@app.route("/", methods=["GET"])
def index():
    """API information endpoint."""
    # Return API metadata as JSON
    # Provides basic information about the API and available endpoints
    return jsonify(
        {
            "name": "Alt Text Generator API",
            "version": "1.0.0",
            "model": MODEL_NAME,  # Show which model is being used
            "endpoints": {"up": "/up", "health": "/health", "generate": "/generate"},
        }
    )


@app.route("/up", methods=["GET"])
def up():
    """Uptime check endpoint - verifies model is available and loaded."""
    try:
        # Check if Ollama is reachable
        tags_response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        ollama_reachable = tags_response.status_code == 200
        
        if not ollama_reachable:
            return jsonify({"status": "down", "reason": "Ollama unreachable"}), 503
        
        # Check if model is available (downloaded)
        models = [m["name"] for m in tags_response.json().get("models", [])]
        model_available = MODEL_NAME in models
        
        if not model_available:
            return jsonify({
                "status": "down",
                "reason": "Model not available",
                "model": MODEL_NAME,
                "available_models": models
            }), 503
        
        # Check if model is loaded by querying the show endpoint
        show_response = requests.post(
            f"{OLLAMA_HOST}/api/show",
            json={"name": MODEL_NAME},
            timeout=5
        )
        model_loaded = show_response.status_code == 200
        
        if model_loaded:
            return jsonify({
                "status": "up",
                "model": MODEL_NAME,
                "model_available": True,
                "model_loaded": True
            }), 200
        else:
            return jsonify({
                "status": "down",
                "reason": "Model not loaded",
                "model": MODEL_NAME,
                "model_available": True,
                "model_loaded": False
            }), 503
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking model status: {e}")
        return jsonify({
            "status": "down",
            "reason": "Error connecting to Ollama",
            "error": str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error in /up endpoint: {e}", exc_info=True)
        return jsonify({
            "status": "down",
            "reason": "Internal error"
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    # Check if Ollama is reachable and the required model is available
    try:
        # Query Ollama's tags endpoint to get list of available models
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        # Ollama is reachable if we get a 200 status code
        ollama_ok = response.status_code == 200
        # Extract model names from the response
        models = [m["name"] for m in response.json().get("models", [])]
        # Use exact matching to avoid false positives from similar model names
        # (e.g., "qwen3-vl:4b" vs "qwen3-vl:7b")
        model_available = MODEL_NAME in models
    except Exception:
        # If any error occurs (connection, timeout, etc.), mark as unavailable
        ollama_ok = False
        model_available = False
        models = []

    # Return health status: "healthy" if both Ollama and model are available, else "degraded"
    return jsonify(
        {
            "status": "healthy" if ollama_ok and model_available else "degraded",
            "ollama_reachable": ollama_ok,  # Whether Ollama service is accessible
            "model": MODEL_NAME,  # The model we're trying to use
            "model_available": model_available,  # Whether that specific model is available
            "available_models": models,  # List of all models Ollama has available
        }
    )


@app.route("/generate", methods=["GET"])
def generate():
    """
    Generate alt text for an image.

    Query parameters:
        imageUrl: URL of the image to caption (required)
        prompt: (optional) Custom prompt for the model

    Returns:
        Plain text alt text on success, or error message on failure
    """
    try:
        # Get parameters from URL query string
        # Support both camelCase (imageUrl) and snake_case (image_url) for flexibility
        image_url = request.args.get("imageUrl") or request.args.get("image_url")
        # Use custom prompt if provided, otherwise use default
        prompt = request.args.get("prompt", DEFAULT_PROMPT)

        # Validate that image URL was provided
        if not image_url:
            return "imageUrl parameter is required", 400

        # Validate and sanitize prompt
        if prompt and isinstance(prompt, str):
            prompt = prompt.strip()
            if len(prompt) > MAX_PROMPT_LENGTH:
                return (
                    f"Prompt is too long (maximum {MAX_PROMPT_LENGTH} characters)",
                    400,
                    {"Content-Type": "text/plain; charset=utf-8"},
                )
            # Use default if prompt is empty after trimming
            if not prompt:
                prompt = DEFAULT_PROMPT
        else:
            prompt = DEFAULT_PROMPT

        # Log the request for debugging/monitoring
        logger.info(f"Generating caption for: {image_url}")

        # Fetch image and convert to base64
        # This function validates the URL, downloads the image, and converts it to base64
        image_b64 = fetch_image_as_base64(image_url)

        # Generate caption via Ollama
        # Send base64 image and prompt to Ollama API and get back the alt text
        alt_text = generate_caption(image_b64, prompt)

        # Log the generated text (truncated to first 100 chars for brevity)
        logger.info(f"Generated: {alt_text[:100]}...")

        # Return plain text response with appropriate content type
        return alt_text, 200, {"Content-Type": "text/plain; charset=utf-8"}

    except requests.exceptions.ConnectionError:
        # Ollama service is not reachable (not running, wrong host, network issue)
        logger.error("Cannot connect to Ollama")
        return (
            "Cannot connect to Ollama. Is it running?",
            503,  # Service Unavailable
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    except ValueError as e:
        # ValueError is raised by our validation functions with safe messages
        # These are user input errors (invalid URL, wrong content type, etc.)
        logger.warning(f"Validation error: {e}")
        return str(e), 400, {"Content-Type": "text/plain; charset=utf-8"}
    except requests.exceptions.RequestException as e:
        # Network/HTTP errors when fetching image from the provided URL
        # (timeout, 404, 500, etc.)
        logger.error(f"Error fetching image: {e}", exc_info=True)
        return (
            "Failed to fetch image from the provided URL",
            400,  # Bad Request
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    except Exception as e:
        # Catch-all for any other unexpected errors
        # Log full exception internally but return generic message to client
        # (prevents leaking internal details that could help attackers)
        logger.error(f"Error generating caption: {e}", exc_info=True)
        return (
            "An internal error occurred while processing the request",
            500,  # Internal Server Error
            {"Content-Type": "text/plain; charset=utf-8"},
        )


if __name__ == "__main__":
    # Log startup information
    logger.info("Starting Ollama-based alt text server...")
    logger.info("Using model: %s", MODEL_NAME)
    logger.info("Ollama host: %s", OLLAMA_HOST)

    # Get port from environment variable (useful for deployment platforms like Heroku)
    # Default to 5000 if not specified
    port = int(os.environ.get("PORT", 5000))
    # Start Flask server
    # host="0.0.0.0" makes it accessible from all network interfaces (not just localhost)
    # debug=False for production (set to True for development to enable auto-reload)
    app.run(host="0.0.0.0", port=port, debug=False)
