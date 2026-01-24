export default defineEventHandler(async (event) => {
  const query = getQuery(event);
  const imageUrl = query.imageUrl as string;
  const prompt = query.prompt as string | undefined;

  // Validate imageUrl is provided
  if (!imageUrl || typeof imageUrl !== "string" || !imageUrl.trim()) {
    throw createError({
      statusCode: 400,
      message: "imageUrl parameter is required",
    });
  }

  // Validate URL format and safety before forwarding to backend
  const trimmedUrl = imageUrl.trim();
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(trimmedUrl);
  } catch {
    throw createError({
      statusCode: 400,
      message: "Invalid URL format",
    });
  }

  // Enforce http/https only
  if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
    throw createError({
      statusCode: 400,
      message: "Only HTTP and HTTPS URLs are allowed",
    });
  }

  // Ensure the URL has a hostname
  if (!parsedUrl.hostname) {
    throw createError({
      statusCode: 400,
      message: "Invalid URL: missing hostname",
    });
  }

  // Block localhost and private IPs by hostname
  const blockedPrefixes = [
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
  ];

  const hostnameLower = parsedUrl.hostname.toLowerCase();
  if (
    blockedPrefixes.some(
      (prefix) =>
        hostnameLower.startsWith(prefix) || hostnameLower === prefix.replace(/\.$/, ""),
    )
  ) {
    throw createError({
      statusCode: 400,
      message: "Access to internal network resources is not allowed",
    });
  }

  // Block URLs with credentials
  if (parsedUrl.username || parsedUrl.password) {
    throw createError({
      statusCode: 400,
      message: "URLs with credentials are not allowed",
    });
  }

  // Block URLs that are too long (prevent DoS)
  if (trimmedUrl.length > 2048) {
    throw createError({
      statusCode: 400,
      message: "URL is too long (maximum 2048 characters)",
    });
  }

  // Validate and sanitize prompt
  const MAX_PROMPT_LENGTH = 2000;
  let sanitizedPrompt: string | undefined;
  if (prompt && typeof prompt === "string") {
    sanitizedPrompt = prompt.trim();
    if (sanitizedPrompt.length > MAX_PROMPT_LENGTH) {
      throw createError({
        statusCode: 400,
        message: `Prompt is too long (maximum ${MAX_PROMPT_LENGTH} characters)`,
      });
    }
    // Only include prompt if it's not empty after trimming
    if (sanitizedPrompt.length === 0) {
      sanitizedPrompt = undefined;
    }
  }

  const apiServerUrl = process.env.API_SERVER_URL || "http://localhost:23711";

  try {
    // Forward the validated request to the Python server
    return await $fetch<string>(`${apiServerUrl}/generate`, {
      method: "GET",
      query: {
        imageUrl: trimmedUrl,
        ...(sanitizedPrompt && { prompt: sanitizedPrompt }),
      },
    });
  } catch (error: any) {
    // Forward the error from Python server
    throw createError({
      statusCode: error.statusCode || 500,
      message: error.message || "Failed to generate alt text",
    });
  }
});
