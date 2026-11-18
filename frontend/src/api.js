const configuredBase = import.meta.env.VITE_API_BASE_URL || "";
export const API_BASE_URL = configuredBase.replace(/\/$/, "");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch (error) {
    error.kind = "network";
    throw error;
  }
  if (!response.ok) {
    let payload = {};
    try {
      payload = await response.json();
    } catch {
      // Keep the HTTP status when a proxy returns non-JSON error content.
    }
    const error = new Error(payload.detail?.message || payload.detail || `HTTP ${response.status}`);
    error.status = response.status;
    error.code = payload.detail?.code;
    throw error;
  }
  return response.json();
}

export const SUPPORTED_CROPS = ["tomato", "potato", "grape"];

export async function submitPrediction({ image, crop, lesionMask, location, signal }) {
  const form = new FormData();
  form.append("image", image);
  if (crop) form.append("crop", crop);
  if (lesionMask) form.append("lesion_mask", lesionMask);
  if (location?.trim()) form.append("location", location.trim());
  return normalizePrediction(await request("/predict", { method: "POST", body: form, signal }));
}

export async function fetchHistory({ limit = 21, offset = 0, classId, signal } = {}) {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (classId) query.set("class_id", classId);
  const payload = await request(`/predictions?${query}`, { signal });
  return { items: normalizeRecords(payload), hasMore: payload.length === limit };
}

export async function fetchHistoryRecord(recordId, { signal } = {}) {
  const payload = await request(`/predictions/${encodeURIComponent(recordId)}`, { signal });
  const [record] = normalizeRecords([payload]);
  return record;
}

function normalizeRecords(payload) {
  if (!Array.isArray(payload)) throw malformedHistoryError();
  if (payload.some((item) => !item || typeof item !== "object" || Array.isArray(item)
    || typeof item.id !== "string" || !item.id.trim()
    || typeof item.predicted_class_id !== "string" || !item.predicted_class_id.trim()
    || typeof item.confidence !== "number" || !Number.isFinite(item.confidence)
    || item.confidence < 0 || item.confidence > 1)) throw malformedHistoryError();
  return payload;
}

function normalizePrediction(payload) {
  const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
  const confidenceValid = (value) => typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1;
  const prediction = payload?.prediction;
  const probabilities = prediction?.probabilities;
  const probabilitiesValid = probabilities == null || (isObject(probabilities)
    && Object.values(probabilities).every(confidenceValid));
  if (!isObject(payload)
    || typeof payload.status !== "string"
    || typeof payload.prediction_status !== "string"
    || typeof payload.recommendation_status !== "string"
    || !isObject(prediction)
    || typeof prediction.class_id !== "string" || !prediction.class_id.trim()
    || !confidenceValid(prediction.confidence)
    || !probabilitiesValid
    || !isObject(payload.model) || typeof payload.model.version !== "string"
    || !isObject(payload.severity) || typeof payload.severity.status !== "string"
    || !Array.isArray(payload.general_guidance)
    || !isObject(payload.weather_context) || typeof payload.weather_context.status !== "string"
    || !Array.isArray(payload.weather_guidance)
    || !isObject(payload.explainability) || typeof payload.explainability.status !== "string"
    || !isObject(payload.history) || typeof payload.history.record_id !== "string" || !payload.history.record_id.trim()
    || !(payload.disease_information === null || isObject(payload.disease_information))
    || !(payload.recommendation_message === null || typeof payload.recommendation_message === "string")) {
    throw malformedPredictionError();
  }
  return payload;
}

function malformedPredictionError() {
  const error = new Error("The API returned an incomplete prediction result. Please try again.");
  error.kind = "malformed";
  return error;
}

function malformedHistoryError() {
  const error = new Error("The history response was not in the expected format. Refresh and try again.");
  error.kind = "malformed";
  return error;
}
