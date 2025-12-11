"""
R-4B VLM Service for Alt Text Generation
=========================================

This package provides local VLM inference using the R-4B model.

Model: YannQi/R-4B
Parameters: 4.82B (Qwen3-4B + SigLip-400M)
MMStar Score: 72.6

Usage:
    from vlm_service.inference import VLMInference
    
    vlm = VLMInference()
    caption = vlm.generate_caption("https://example.com/image.jpg")
"""

from .inference import VLMInference

__all__ = ["VLMInference"]
__version__ = "0.1.0"

