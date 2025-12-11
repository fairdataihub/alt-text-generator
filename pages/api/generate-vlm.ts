import type { NextApiRequest, NextApiResponse } from "next";

/**
 * Alt text generation using local R-4B VLM service
 * 
 * This endpoint calls the local Python VLM service instead of Replicate.
 * Make sure the VLM service is running: `python vlm_service/server.py`
 * 
 * Model: YannQi/R-4B (4.82B params, MMStar: 72.6)
 */

type ResponseData = {
  alt_text?: string;
  error?: string;
  model?: string;
};

// VLM service URL (can be configured via environment variable)
const VLM_SERVICE_URL = process.env.VLM_SERVICE_URL || "http://localhost:5000";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData | string>
) {
  const { imageUrl } = req.query;

  if (!imageUrl || typeof imageUrl !== "string") {
    return res.status(400).json({ error: "imageUrl query parameter is required" });
  }

  try {
    // Call local VLM service
    const response = await fetch(
      `${VLM_SERVICE_URL}/generate?imageUrl=${encodeURIComponent(imageUrl)}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `VLM service error: ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    // Return just the alt text string for backwards compatibility
    // Or return full JSON if Accept header indicates JSON preference
    const acceptHeader = req.headers.accept || "";
    if (acceptHeader.includes("application/json")) {
      return res.status(200).json(data);
    }

    return res.status(200).json(data.alt_text);

  } catch (error) {
    console.error("VLM generation error:", error);
    
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    
    // Check if VLM service is not running
    if (errorMessage.includes("ECONNREFUSED") || errorMessage.includes("fetch failed")) {
      return res.status(503).json({
        error: "VLM service not running. Start it with: python vlm_service/server.py",
      });
    }

    return res.status(500).json({ error: errorMessage });
  }
}

