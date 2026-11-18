export const MAX_UPLOAD_BYTES = Number(import.meta.env.VITE_MAX_UPLOAD_BYTES || 10 * 1024 * 1024);

const imageTypes = new Map([
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".png", "image/png"],
  [".webp", "image/webp"],
]);

export function validateImageFile(file, maxBytes = MAX_UPLOAD_BYTES) {
  if (!file) return "Choose a leaf image to continue.";
  if (file.size <= 0) return "The selected image is empty.";
  if (file.size > maxBytes) return `Image is too large. Choose a file under ${formatBytes(maxBytes)}.`;
  const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
  const expectedType = imageTypes.get(extension);
  if (!expectedType) return "Unsupported image type. Choose a JPEG, PNG, or WEBP file.";
  if (file.type && file.type !== expectedType) return "File extension and image type do not match.";
  return null;
}

export function validateLesionMask(file, maxBytes = MAX_UPLOAD_BYTES) {
  if (!file) return null;
  if (file.size <= 0) return "The lesion mask is empty.";
  if (file.size > maxBytes) return `Lesion mask is too large. Choose a file under ${formatBytes(maxBytes)}.`;
  if (!file.name.toLowerCase().endsWith(".png") || (file.type && file.type !== "image/png")) {
    return "Lesion masks must be PNG files.";
  }
  return null;
}

export function formatBytes(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(0)} MB`;
}

export function errorMessage(error) {
  const code = error?.code;
  if (error?.status === 404) return "This saved prediction could not be found. Refresh history and try again.";
  if (error?.status === 503 && !code) return "Prediction history is unavailable. Check the API and database configuration, then try again.";
  if (error?.kind === "malformed") return error.message;
  if (code === "model_unavailable") return "The production classifier is unavailable. Add a trained production checkpoint and class mapping; the smoke-test model is never used.";
  if (code === "database_unavailable") return "Prediction history storage is unavailable. Configure the database and apply its migrations.";
  if (code === "persistence_failed") return "The analysis could not be saved to prediction history. Please try again later.";
  if (code === "request_too_large") return "The request exceeds the API's JSON size limit.";
  if (code === "invalid_crop") return "An unrecognised crop was submitted. Choose Tomato, Potato, or Grape from the crop selector.";
  if (["invalid_image", "empty_upload", "missing_filename"].includes(code)) return "This file could not be decoded as an image. Choose a valid JPEG, PNG, or WEBP image.";
  if (["unsupported_image_type", "unsupported_image_content", "content_type_mismatch"].includes(code)) return "Unsupported image type. Choose a matching JPEG, PNG, or WEBP file.";
  if (["upload_too_large", "image_dimensions_too_large"].includes(code)) return "This image exceeds the server upload or dimension limit.";
  if (["unsupported_mask_type", "mask_dimensions_mismatch"].includes(code)) return "The lesion mask must be a PNG aligned with the uploaded leaf image.";
  if (error?.kind === "network") return "Could not reach the API. Check that the backend is running and try again.";
  return error?.message || "The request failed. Please try again.";
}

export function calculateHistoryAnalytics(rows = []) {
  const classes = {};
  const severities = {};
  let confidenceTotal = 0;
  let confidenceCount = 0;
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    if (typeof row.predicted_class_id === "string" && row.predicted_class_id) {
      classes[row.predicted_class_id] = (classes[row.predicted_class_id] || 0) + 1;
    }
    if (typeof row.confidence === "number" && Number.isFinite(row.confidence) && row.confidence >= 0 && row.confidence <= 1) {
      confidenceTotal += row.confidence;
      confidenceCount += 1;
    }
    const category = row.severity?.category;
    if (typeof category === "string" && category) severities[category] = (severities[category] || 0) + 1;
  }
  return {
    total: rows.filter((row) => row && typeof row === "object").length,
    uniqueClasses: Object.keys(classes).length,
    averageConfidence: confidenceCount ? confidenceTotal / confidenceCount : null,
    classDistribution: classes,
    severityDistribution: severities,
  };
}

export function safeImageDataUrl(value) {
  if (typeof value !== "string" || value.length > 2_000_000) return null;
  return /^data:image\/jpeg;base64,[A-Za-z0-9+/]*={0,2}$/.test(value) ? value : null;
}

export function safeExternalUrl(value) {
  if (typeof value !== "string" || value.length > 2048) return null;
  try {
    const parsed = new URL(value);
    if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) return null;
    return parsed.href;
  } catch {
    return null;
  }
}

export function displayClass(classId = "") {
  return classId.split("_").filter(Boolean).map((part) => part[0].toUpperCase() + part.slice(1)).join(" ");
}

export function formatDate(value) {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleString();
}
