/**
 * URL validation utilities for image URLs
 * Validates that URLs are safe and point to publicly accessible image resources
 */

// Blocked IP ranges for SSRF protection
const BLOCKED_IP_PREFIXES = [
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

// Common image file extensions
const IMAGE_EXTENSIONS = [
  ".jpg",
  ".jpeg",
  ".png",
  ".gif",
  ".webp",
  ".svg",
  ".bmp",
  ".ico",
];

/**
 * Validates that a URL is safe and points to a publicly accessible resource
 * @param url - The URL to validate
 * @returns Object with isValid boolean and error message if invalid
 */
export function validateImageUrl(url: string): { isValid: boolean; error?: string } {
  if (!url || typeof url !== "string" || url.trim().length === 0) {
    return { isValid: false, error: "URL is required" };
  }

  // Trim whitespace
  const trimmedUrl = url.trim();

  // Basic URL format validation
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(trimmedUrl);
  } catch {
    return { isValid: false, error: "Invalid URL format" };
  }

  // Enforce http/https only
  if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
    return { isValid: false, error: "Only HTTP and HTTPS URLs are allowed" };
  }

  // Ensure the URL has a hostname
  if (!parsedUrl.hostname) {
    return { isValid: false, error: "Invalid URL: missing hostname" };
  }

  // Block localhost and private IPs by hostname
  const hostnameLower = parsedUrl.hostname.toLowerCase();
  if (
    BLOCKED_IP_PREFIXES.some(
      (prefix) =>
        hostnameLower.startsWith(prefix) || hostnameLower === prefix.replace(/\.$/, ""),
    )
  ) {
    return {
      isValid: false,
      error: "Access to internal network resources is not allowed",
    };
  }

  // Additional safety checks
  // Block URLs with credentials
  if (parsedUrl.username || parsedUrl.password) {
    return { isValid: false, error: "URLs with credentials are not allowed" };
  }

  // Block URLs that are too long (prevent DoS)
  if (trimmedUrl.length > 2048) {
    return { isValid: false, error: "URL is too long (maximum 2048 characters)" };
  }

  // Warn about non-standard ports (but allow them)
  // This is informational - we allow non-standard ports but they're less common for images

  // Optional: Check if URL looks like an image URL (heuristic, not strict)
  // This is a soft check - we don't reject if it doesn't match
  const pathnameLower = parsedUrl.pathname.toLowerCase();
  const hasImageExtension = IMAGE_EXTENSIONS.some((ext) =>
    pathnameLower.endsWith(ext),
  );
  const hasImageIndicator =
    hasImageExtension ||
    pathnameLower.includes("/image") ||
    pathnameLower.includes("/img") ||
    pathnameLower.includes("/photo") ||
    pathnameLower.includes("/picture");

  // Note: We don't reject if it doesn't look like an image URL
  // because some image URLs don't have extensions (e.g., CDN URLs with query params)

  return { isValid: true };
}

/**
 * Validates image URL and throws an error if invalid
 * @param url - The URL to validate
 * @throws Error if URL is invalid
 */
export function validateImageUrlOrThrow(url: string): void {
  const result = validateImageUrl(url);
  if (!result.isValid) {
    throw new Error(result.error || "Invalid image URL");
  }
}
