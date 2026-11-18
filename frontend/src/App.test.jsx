import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import App, { PredictionResult } from "./App.jsx";
import { calculateHistoryAnalytics, errorMessage, safeExternalUrl, safeImageDataUrl, validateImageFile, validateLesionMask } from "./workflow.js";

const goodFile = () => new File([new Uint8Array([1, 2, 3])], "leaf.png", { type: "image/png" });
const resultPayload = {
  status: "completed", prediction_status: "accepted", recommendation_status: "available",
  crop: "tomato",
  prediction: { class_id: "tomato_early_blight", confidence: 0.91, probabilities: { tomato_early_blight: 0.91, tomato_late_blight: 0.09 } },
  model: { version: "efficientnet-b0-field" },
  severity: { status: "estimated", estimate: { category: "Moderate", severity_percentage: 22.4 } },
  disease_information: { id: "tomato_early_blight", crop: "Tomato", name: "Early blight", description: "Dark spots may form concentric rings.", symptoms: ["Target-like rings"], trace: { sources: [{ title: "Extension guide", url: "https://example.test/guide" }] } },
  general_guidance: [{ id: "g1", category: "prevention", text: "Use disease-free planting material.", trace: { sources: [{ title: "Extension guide", url: "https://example.test/guide" }] } }],
  weather_context: { status: "available", location: { name: "Pune" }, observed_at: "2026-09-30T10:00", weather: { temperature_c: 25, relative_humidity_percent: 92, precipitation_mm: 0.2, wind_speed_kmh: 5 } },
  weather_guidance: [{ id: "wet-rule", text: "Current observations match a context only; they do not show cause.", trace: { sources: [] } }],
  recommendation_message: null,
  explainability: { status: "available", heatmap_data_url: "data:image/jpeg;base64,YWJj", overlay_data_url: "data:image/jpeg;base64,ZA==" },
  history: { record_id: "abc-123", created_at: "2026-09-30T10:00:00Z" },
};

const grapeResultPayload = {
  status: "completed", prediction_status: "accepted", recommendation_status: "available",
  crop: "grape",
  prediction: { class_id: "grape_black_rot", confidence: 0.99, probabilities: { grape_black_rot: 0.99, grape_esca: 0.005, grape_isariopsis_leaf_blight: 0.005 } },
  model: { version: "efficientnet-b0-grape" },
  severity: { status: "not_requested" },
  disease_information: { id: "grape_black_rot", crop: "Grape", name: "Black Rot", description: "Fungal disease caused by Guignardia bidwellii.", symptoms: ["Circular reddish-brown spots"], trace: { sources: [{ title: "OSU Extension", url: "https://ohioline.osu.edu/factsheet/plpath-fru-24" }] } },
  general_guidance: [{ id: "g-grape-1", category: "prevention", text: "Remove mummified berries.", trace: { sources: [] } }],
  weather_context: { status: "not_requested" },
  weather_guidance: [],
  recommendation_message: null,
  explainability: { status: "available", heatmap_data_url: "data:image/jpeg;base64,YWJj", overlay_data_url: "data:image/jpeg;base64,ZA==" },
  history: { record_id: "grape-rec-1", created_at: "2026-11-17T10:00:00Z" },
};

const potatoResultPayload = {
  status: "completed", prediction_status: "accepted", recommendation_status: "available",
  crop: "potato",
  prediction: { class_id: "potato_late_blight", confidence: 0.88, probabilities: { potato_late_blight: 0.88, potato_early_blight: 0.12 } },
  model: { version: "efficientnet-b0-field" },
  severity: { status: "not_requested" },
  disease_information: { id: "potato_late_blight", crop: "Potato", name: "Late blight", description: "Caused by Phytophthora infestans.", symptoms: ["Water-soaked lesions"], trace: { sources: [] } },
  general_guidance: [{ id: "g-potato-1", category: "prevention", text: "Use certified disease-free seed.", trace: { sources: [] } }],
  weather_context: { status: "not_requested" },
  weather_guidance: [],
  recommendation_message: null,
  explainability: { status: "unavailable" },
  history: { record_id: "potato-rec-1", created_at: "2026-11-17T11:00:00Z" },
};

function jsonResponse(payload, status = 200) {
  return Promise.resolve({ ok: status >= 200 && status < 300, status, json: () => Promise.resolve(payload) });
}

function selectLeaf() {
  fireEvent.change(screen.getByLabelText("Leaf image"), { target: { files: [goodFile()] } });
}

// ─── upload validation ────────────────────────────────────────────────────────
describe("upload validation", () => {
  it("accepts JPEG, PNG and WEBP with matching media types", () => {
    expect(validateImageFile(new File(["x"], "leaf.jpg", { type: "image/jpeg" }))).toBeNull();
    expect(validateImageFile(new File(["x"], "leaf.png", { type: "image/png" }))).toBeNull();
    expect(validateImageFile(new File(["x"], "leaf.webp", { type: "image/webp" }))).toBeNull();
  });
  it("rejects unsupported types, mismatched MIME and over-limit files", () => {
    expect(validateImageFile(new File(["x"], "leaf.gif", { type: "image/gif" }))).toMatch(/Unsupported/);
    expect(validateImageFile(new File(["x"], "leaf.png", { type: "image/jpeg" }))).toMatch(/do not match/);
    expect(validateImageFile(new File([new Uint8Array(8)], "leaf.png", { type: "image/png" }), 4)).toMatch(/too large/);
  });
  it("limits optional lesion masks to PNG", () => {
    expect(validateLesionMask(new File(["x"], "mask.png", { type: "image/png" }))).toBeNull();
    expect(validateLesionMask(new File(["x"], "mask.jpg", { type: "image/jpeg" }))).toMatch(/PNG/);
  });
  it("only returns bounded JPEG data URLs for Grad-CAM images", () => {
    expect(safeImageDataUrl("data:image/jpeg;base64,YWJj")).toBe("data:image/jpeg;base64,YWJj");
    expect(safeImageDataUrl("javascript:alert(1)")).toBeNull();
    expect(safeImageDataUrl(`data:image/jpeg;base64,${"a".repeat(2_000_001)}`)).toBeNull();
  });
  it("allows only bounded absolute HTTP(S) source links", () => {
    expect(safeExternalUrl("https://extension.example/guide")).toBe("https://extension.example/guide");
    expect(safeExternalUrl("http://extension.example/guide")).toBe("http://extension.example/guide");
    expect(safeExternalUrl("javascript:alert(1)")).toBeNull();
    expect(safeExternalUrl("data:text/html,<script>alert(1)</script>")).toBeNull();
    expect(safeExternalUrl("//extension.example/path")).toBeNull();
    expect(safeExternalUrl("https://user:pass@example.test/")).toBeNull();
    expect(safeExternalUrl("https://" + "a".repeat(2049))).toBeNull();
  });
});

// ─── crop selector ────────────────────────────────────────────────────────────
describe("crop selector", () => {
  it("renders all three crop options: Tomato, Potato, Grape", () => {
    render(<App />);
    expect(screen.getByRole("radio", { name: "Tomato" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Potato" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Grape" })).toBeInTheDocument();
  });

  it("defaults to Tomato selected", () => {
    render(<App />);
    expect(screen.getByRole("radio", { name: "Tomato" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Potato" })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: "Grape" })).not.toBeChecked();
  });

  it("changes selection when another crop is clicked", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("radio", { name: "Grape" }));
    expect(screen.getByRole("radio", { name: "Grape" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Tomato" })).not.toBeChecked();
  });

  it("changes selection to Potato", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("radio", { name: "Potato" }));
    expect(screen.getByRole("radio", { name: "Potato" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Tomato" })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: "Grape" })).not.toBeChecked();
  });

  it("includes the selected crop in the FormData sent to /predict", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(grapeResultPayload));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    fireEvent.click(screen.getByRole("radio", { name: "Grape" }));
    selectLeaf();
    fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [, options] = fetchMock.mock.calls[0];
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get("crop")).toBe("grape");
  });

  it("sends tomato crop in FormData by default", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(resultPayload));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    selectLeaf();
    fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [, options] = fetchMock.mock.calls[0];
    expect(options.body.get("crop")).toBe("tomato");
  });
});

// ─── prediction workflow UI ───────────────────────────────────────────────────
describe("prediction workflow UI", () => {
  it("submits a valid upload and renders prediction, recommendation, weather and Grad-CAM", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(resultPayload));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    selectLeaf();
    expect(screen.getByAltText("Selected leaf preview")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("LOCATION OPTIONAL"), { target: { value: "Pune" } });
    fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    expect(await screen.findByRole("heading", { name: "Your crop health summary" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tomato Early Blight" })).toBeInTheDocument();
    expect(screen.getAllByText("91.0%")).toHaveLength(2);
    expect(screen.getByText("9.0%")).toBeInTheDocument();
    expect(screen.getByText("efficientnet-b0-field")).toBeInTheDocument();
    expect(screen.getByText("Moderate")).toBeInTheDocument();
    expect(screen.getByText(/Affected area estimate: 22.4%/)).toBeInTheDocument();
    expect(screen.getByText("Dark spots may form concentric rings.")).toBeInTheDocument();
    expect(screen.getByText("Use disease-free planting material.")).toBeInTheDocument();
    expect(screen.getByText("25°C")).toBeInTheDocument();
    expect(screen.getByText(/Current observations match a context only/)).toBeInTheDocument();
    expect(screen.getByAltText("Grad-CAM heatmap highlighting model activation areas")).toHaveAttribute("src", resultPayload.explainability.heatmap_data_url);
    expect(screen.getByText("abc-123")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/predict$/), expect.objectContaining({ method: "POST", body: expect.any(FormData) }));
  });

  it("renders crop badge in result when backend echoes crop field", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(resultPayload)));
    render(<App />);
    selectLeaf();
    fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    await screen.findByRole("heading", { name: "Your crop health summary" });
    // "Tomato" appears in the crop selector label AND in the result stats badge (≥2 matches)
    expect(screen.getAllByText("Tomato").length).toBeGreaterThanOrEqual(2);
  });

  it("renders Grape prediction result correctly", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(grapeResultPayload)));
    render(<App />);
    fireEvent.click(screen.getByRole("radio", { name: "Grape" }));
    selectLeaf();
    fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    expect(await screen.findByRole("heading", { name: "Your crop health summary" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Grape Black Rot" })).toBeInTheDocument();
    expect(screen.getByText(/Guignardia bidwellii/)).toBeInTheDocument();
    // "Grape" appears in the crop selector label AND in the result stats badge (≥2 matches)
    expect(screen.getAllByText("Grape").length).toBeGreaterThanOrEqual(2);
    // 99.0% appears in confidence stat AND in the probability bar (≥2 matches)
    expect(screen.getAllByText("99.0%").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Remove mummified berries.")).toBeInTheDocument();
    expect(screen.getByText("Grad-CAM visualizes model activation; it does not prove biological cause.")).toBeInTheDocument();
  });

  it("renders Potato prediction result correctly", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(potatoResultPayload)));
    render(<App />);
    fireEvent.click(screen.getByRole("radio", { name: "Potato" }));
    selectLeaf();
    fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    expect(await screen.findByRole("heading", { name: "Your crop health summary" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Potato Late Blight" })).toBeInTheDocument();
    expect(screen.getByText(/Phytophthora infestans/)).toBeInTheDocument();
    // "Potato" appears in the crop selector label AND in the result stats badge (≥2 matches)
    expect(screen.getAllByText("Potato").length).toBeGreaterThanOrEqual(2);
    // 88.0% appears in confidence stat AND in the probability bar (≥2 matches)
    expect(screen.getAllByText("88.0%").length).toBeGreaterThanOrEqual(2);
  });

  it("renders confidence and class probability bars correctly", () => {
    render(<PredictionResult result={resultPayload} />);
    expect(screen.getAllByText("91.0%")).toHaveLength(2);
    expect(screen.getByText("9.0%")).toBeInTheDocument();
    expect(screen.getByText("Class probabilities")).toBeInTheDocument();
  });

  it("renders Grad-CAM heatmap and overlay images", () => {
    render(<PredictionResult result={resultPayload} />);
    expect(screen.getByAltText("Grad-CAM heatmap highlighting model activation areas")).toHaveAttribute("src", "data:image/jpeg;base64,YWJj");
    expect(screen.getByAltText("Grad-CAM heatmap overlaid on the uploaded leaf image")).toHaveAttribute("src", "data:image/jpeg;base64,ZA==");
  });

  it("renders severity estimate when present", () => {
    render(<PredictionResult result={resultPayload} />);
    expect(screen.getByText("Moderate")).toBeInTheDocument();
    expect(screen.getByText(/Affected area estimate: 22.4%/)).toBeInTheDocument();
  });

  it("renders weather metrics and guidance when available", () => {
    render(<PredictionResult result={resultPayload} />);
    expect(screen.getByText("25°C")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
    expect(screen.getByText(/Current observations match a context only/)).toBeInTheDocument();
  });

  it("displays severity-not-requested message when no mask supplied", () => {
    render(<PredictionResult result={grapeResultPayload} />);
    expect(screen.getByText(/Severity needs an aligned lesion mask/)).toBeInTheDocument();
  });

  it("displays weather-not-requested state when weather is not requested", () => {
    render(<PredictionResult result={grapeResultPayload} />);
    expect(screen.getByText("Not requested")).toBeInTheDocument();
  });

  it("handles missing optional fields safely without crashing", () => {
    const minimal = {
      ...resultPayload,
      crop: null,
      disease_information: null,
      general_guidance: [],
      weather_guidance: [],
      weather_context: { status: "not_requested" },
      explainability: { status: "unavailable" },
      severity: { status: "unavailable" },
      recommendation_message: null,
    };
    render(<PredictionResult result={minimal} />);
    expect(screen.getByText("The prediction did not map to a supported knowledge-base entry.")).toBeInTheDocument();
    expect(screen.getByText("Explainability image is unavailable for this result.")).toBeInTheDocument();
    expect(screen.getByText("No disease-specific guidance is available for this result. Consult a local agricultural extension professional if you are concerned.")).toBeInTheDocument();
  });

  it("shows the explicit production model unavailable response without a fabricated result", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: { code: "model_unavailable", message: "missing production model" } }, 503)));
    render(<App />); selectLeaf(); fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    expect(await screen.findByText("Production model unavailable")).toBeInTheDocument();
    expect(screen.getByText(/smoke-test model is never used/)).toBeInTheDocument();
    expect(screen.queryByTestId("prediction-result")).not.toBeInTheDocument();
  });

  it("displays invalid_crop error clearly", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: { code: "invalid_crop", message: "must be one of: grape, potato, tomato" } }, 422)));
    render(<App />); selectLeaf(); fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("crop selector");
    expect(screen.queryByTestId("prediction-result")).not.toBeInTheDocument();
  });

  it("shows an immediate client-side error for unsupported uploads", () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText("Leaf image"), { target: { files: [new File(["x"], "leaf.gif", { type: "image/gif" })] } });
    expect(screen.getByRole("alert")).toHaveTextContent("Unsupported image type");
    expect(screen.getByRole("button", { name: /Analyze leaf/ })).toBeDisabled();
  });

  it("maps invalid image response into a readable error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: { code: "invalid_image", message: "bad bytes" } }, 400)));
    render(<App />); selectLeaf(); fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("valid JPEG, PNG, or WEBP");
  });

  it("renders result sections directly when supplied a response", () => {
    render(<PredictionResult result={resultPayload} />);
    expect(screen.getByText("Class probabilities")).toBeInTheDocument();
    expect(screen.getByAltText("Grad-CAM heatmap overlaid on the uploaded leaf image")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Extension guide/ }).every((link) => link.getAttribute("rel") === "noreferrer")).toBe(true);
  });

  it("does not render untrusted non-HTTP knowledge-base links", () => {
    const untrusted = structuredClone(resultPayload);
    untrusted.disease_information.trace.sources = [{ title: "Unsafe", url: "javascript:alert(1)" }];
    render(<PredictionResult result={untrusted} />);
    expect(screen.queryByRole("link", { name: /Unsafe/ })).not.toBeInTheDocument();
  });

  it("rejects a malformed successful prediction response without rendering a prediction", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      status: "completed",
      prediction_status: "accepted",
      recommendation_status: "available",
      prediction: { class_id: "tomato_early_blight", confidence: 1.4, probabilities: { tomato_early_blight: 1.4 } },
    })));
    render(<App />); selectLeaf(); fireEvent.click(screen.getByRole("button", { name: /Analyze leaf/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("incomplete prediction result");
    expect(screen.queryByTestId("prediction-result")).not.toBeInTheDocument();
  });

  it("starts with no fabricated prediction result", () => {
    render(<App />);
    expect(screen.queryByTestId("prediction-result")).not.toBeInTheDocument();
    expect(screen.queryByText("Tomato Early Blight")).not.toBeInTheDocument();
  });
});

// ─── prediction history ───────────────────────────────────────────────────────
describe("prediction history", () => {
  it("shows loading then renders history and loads the selected record", async () => {
    let resolveList;
    const historyRecord = { id: "h-1", predicted_class_id: "tomato_early_blight", confidence: 0.81, created_at: "2026-09-30T10:00:00Z", severity: { category: "Moderate" }, model_version: "field-v1", recommendation_result: { disease_information: { description: "Saved description." } }, result_metadata: { explainability_status: "available" } };
    const fetchMock = vi.fn()
      .mockImplementationOnce(() => new Promise((resolve) => { resolveList = resolve; }))
      .mockResolvedValueOnce(jsonResponse(historyRecord));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    expect(screen.getByText(/Loading prediction history/)).toBeInTheDocument();
    resolveList({ ok: true, status: 200, json: () => Promise.resolve([historyRecord]) });
    expect(await screen.findByText("Tomato Early Blight")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Open result/ }));
    expect(await screen.findByText("Saved description.")).toBeInTheDocument();
    expect(screen.getAllByText("field-v1")).toHaveLength(2);
  });

  it("shows Grape predictions in history table correctly", async () => {
    const grapeRow = { id: "g-1", predicted_class_id: "grape_black_rot", confidence: 0.99, created_at: "2026-11-17T10:00:00Z" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse([grapeRow])));
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    expect(await screen.findByText("Grape Black Rot")).toBeInTheDocument();
  });

  it("shows Potato predictions in history table correctly", async () => {
    const potatoRow = { id: "p-1", predicted_class_id: "potato_late_blight", confidence: 0.88, created_at: "2026-11-17T11:00:00Z" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse([potatoRow])));
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    expect(await screen.findByText("Potato Late Blight")).toBeInTheDocument();
  });

  it("shows an empty state when the API has no saved predictions", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse([])));
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    expect(await screen.findByText("No predictions yet")).toBeInTheDocument();
  });

  it("shows a history error state and allows retry", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    expect(await screen.findByText("History could not be loaded")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("paginates newest-first backend results and disables boundary navigation", async () => {
    const records = Array.from({ length: 21 }, (_, index) => ({ id: "h-" + index, predicted_class_id: "tomato_early_blight", confidence: 0.8, created_at: "2026-09-30T10:00:00Z" }));
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(records))
      .mockResolvedValueOnce(jsonResponse(records.slice(20)))
      .mockResolvedValueOnce(jsonResponse(records.slice(0, 20)));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    expect(await screen.findByText("Page 1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Page 2")).toBeInTheDocument();
    expect(fetchMock.mock.calls[1][0]).toContain("offset=20");
    expect(screen.getByRole("button", { name: "Previous" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Previous" }));
    expect(await screen.findByText("Page 1")).toBeInTheDocument();
    expect(fetchMock.mock.calls[2][0]).toContain("offset=0");
  });

  it("sends the selected class filter through the existing API query", async () => {
    const filtered = { id: "h-filter", predicted_class_id: "tomato_early_blight", confidence: 0.75 };
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse([])).mockResolvedValueOnce(jsonResponse([filtered]));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    await screen.findByText("No predictions yet");
    fireEvent.change(screen.getByLabelText("Filter by class ID"), { target: { value: "tomato_early_blight" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(await screen.findByText("Tomato Early Blight")).toBeInTheDocument();
    expect(fetchMock.mock.calls[1][0]).toContain("class_id=tomato_early_blight");
  });

  it("handles malformed list responses without exposing internal errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ records: [] })));
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("History could not be loaded");
    expect(screen.getByRole("alert")).toHaveTextContent("expected format");
  });

  it("shows a safe not-found message when a history detail record disappeared", async () => {
    const row = { id: "gone", predicted_class_id: "tomato_early_blight", confidence: 0.75 };
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse([row])).mockResolvedValueOnce(jsonResponse({ detail: "Prediction record not found" }, 404));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    await screen.findByText("Tomato Early Blight");
    fireEvent.click(screen.getByRole("button", { name: /Open result/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("saved prediction could not be found");
  });

  it("opens a historical record while safely omitting optional fields", async () => {
    const row = { id: "bare", predicted_class_id: "tomato_early_blight", confidence: 0.5 };
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse([row])).mockResolvedValueOnce(jsonResponse(row));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />); fireEvent.click(screen.getByRole("button", { name: /Prediction history/ }));
    await screen.findByText("Tomato Early Blight");
    fireEvent.click(screen.getByRole("button", { name: /Open result/ }));
    expect(await screen.findByText("Disease information was not stored for this record.")).toBeInTheDocument();
    expect(screen.getByText("No stored general guidance.")).toBeInTheDocument();
    expect(screen.getByText("No weather data was stored.")).toBeInTheDocument();
    expect(screen.getByText("No weather-specific guidance was stored.")).toBeInTheDocument();
  });
});

// ─── history analytics ────────────────────────────────────────────────────────
describe("history analytics", () => {
  it("calculates summaries and chart distributions only from returned records", () => {
    const summary = calculateHistoryAnalytics([
      { predicted_class_id: "tomato_early_blight", confidence: 0.8, severity: { category: "Moderate" } },
      { predicted_class_id: "tomato_early_blight", confidence: 0.6, severity: { category: "Moderate" } },
      { predicted_class_id: "potato_healthy", confidence: 1 },
    ]);
    expect(summary.total).toBe(3);
    expect(summary.uniqueClasses).toBe(2);
    expect(summary.averageConfidence).toBeCloseTo(0.8);
    expect(summary.classDistribution).toEqual({ tomato_early_blight: 2, potato_healthy: 1 });
    expect(summary.severityDistribution).toEqual({ Moderate: 2 });
  });
  it("does not fabricate analytics when there are no records", () => {
    expect(calculateHistoryAnalytics([])).toEqual({ total: 0, uniqueClasses: 0, averageConfidence: null, classDistribution: {}, severityDistribution: {} });
  });
});

// ─── backend error mapping ────────────────────────────────────────────────────
describe("backend error mapping", () => {
  it.each([
    ["database_unavailable", /history storage is unavailable/i],
    ["persistence_failed", /could not be saved/i],
    ["request_too_large", /JSON size limit/i],
    ["unsupported_image_type", /unsupported image type/i],
    ["upload_too_large", /exceeds the server/i],
    ["mask_dimensions_mismatch", /lesion mask must be a PNG/i],
    ["invalid_crop", /crop selector/i],
  ])("maps %s to human-readable guidance", (code, expected) => {
    expect(errorMessage({ code })).toMatch(expected);
  });
});
