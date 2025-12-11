"""
R-4B Vision Language Model Inference Service
=============================================

This module provides image captioning using the R-4B model (YannQi/R-4B).
R-4B is a 4.82B parameter VLM that achieves MMStar score of 72.6.

Model details:
- Base LLM: Qwen3-4B
- Vision encoder: SigLip-400M
- Total params: 4.82B
- Released: 2025/08/11

Usage:
    from inference import VLMInference
    
    vlm = VLMInference()
    caption = vlm.generate_caption("https://example.com/image.jpg")
"""

import torch
from PIL import Image
import requests
from io import BytesIO
from typing import Optional, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "YannQi/R-4B"
DEFAULT_THINKING_MODE = "short"  # "auto", "long", or "short" for direct answers


class VLMInference:
    """R-4B Vision Language Model for image captioning."""
    
    def __init__(
        self,
        model_name: str = MODEL_NAME,
        device: Optional[str] = None,
        torch_dtype: torch.dtype = torch.float32,  # R-4B requires float32 for LayerNorm
        load_in_4bit: bool = False,
    ):
        """
        Initialize the VLM inference engine.
        
        Args:
            model_name: HuggingFace model identifier
            device: Device to use ("cuda", "cpu", or None for auto-detect)
            torch_dtype: Torch dtype for model weights
            load_in_4bit: Whether to use 4-bit quantization (reduces VRAM)
        """
        from transformers import AutoModel, AutoProcessor
        
        self.model_name = model_name
        # Explicitly use cuda:0 (the 4090) if available
        if device:
            self.device = device
        elif torch.cuda.is_available():
            self.device = "cuda:0"
        else:
            self.device = "cpu"
        self.torch_dtype = torch_dtype
        
        logger.info(f"Loading {model_name} on {self.device}...")
        
        # Load processor
        self.processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Load model - avoid device_map="auto" to prevent multi-GPU issues
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch_dtype,
        }
        
        if load_in_4bit:
            from transformers import BitsAndBytesConfig
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch_dtype,
            )
            model_kwargs["device_map"] = {"": self.device}
        
        self.model = AutoModel.from_pretrained(model_name, **model_kwargs)
        
        # Move to device explicitly if not using quantization
        if not load_in_4bit:
            self.model = self.model.to(self.device)
        
        self.model.eval()
        logger.info(f"Model loaded successfully on {self.device}")
    
    def load_image(self, image_source: Union[str, Image.Image]) -> Image.Image:
        """
        Load an image from URL, file path, or PIL Image.
        
        Args:
            image_source: URL, file path, or PIL Image
            
        Returns:
            PIL Image object
        """
        if isinstance(image_source, Image.Image):
            return image_source
        
        if image_source.startswith(("http://", "https://")):
            response = requests.get(image_source, timeout=30)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        else:
            return Image.open(image_source).convert("RGB")
    
    def generate_caption(
        self,
        image_source: Union[str, Image.Image],
        prompt: str = "Describe this image concisely for use as alt text.",
        thinking_mode: str = DEFAULT_THINKING_MODE,
        max_new_tokens: int = 256,
    ) -> str:
        """
        Generate a caption for an image.
        
        Args:
            image_source: URL, file path, or PIL Image
            prompt: Text prompt for the model
            thinking_mode: "auto", "long" (detailed reasoning), or "short" (direct)
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated caption string
        """
        # Load image
        image = self.load_image(image_source)
        
        # Build conversation
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        
        # Apply chat template
        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            thinking_mode=thinking_mode,
        )
        
        # Process inputs
        inputs = self.processor(
            images=image,
            text=text,
            return_tensors="pt",
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
            )
        
        # Decode output (skip input tokens)
        output_ids = generated_ids[0][len(inputs.input_ids[0]):]
        output_text = self.processor.decode(
            output_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        
        return output_text.strip()


def main():
    """Test the inference service."""
    print("Initializing VLM inference...")
    vlm = VLMInference()
    
    # Test with a sample image
    test_url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    print(f"\nGenerating caption for: {test_url}")
    
    caption = vlm.generate_caption(test_url)
    print(f"\nGenerated caption:\n{caption}")


if __name__ == "__main__":
    main()

