import { describe, expect, it, vi } from "vitest";

describe("frontend API configuration", () => {
  it("uses VITE_API_BASE_URL for centralized history requests", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test/root/");
    vi.resetModules();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    }));
    try {
      const api = await import("./api.js");
      expect(api.API_BASE_URL).toBe("https://api.example.test/root");
      await api.fetchHistory({ limit: 21, offset: 40, classId: "tomato_early_blight" });
      expect(fetch).toHaveBeenCalledWith(
        "https://api.example.test/root/predictions?limit=21&offset=40&class_id=tomato_early_blight",
        expect.objectContaining({ signal: undefined }),
      );
    } finally {
      vi.unstubAllEnvs();
      vi.resetModules();
    }
  });

  it("exports SUPPORTED_CROPS as [tomato, potato, grape]", async () => {
    vi.resetModules();
    const api = await import("./api.js");
    expect(api.SUPPORTED_CROPS).toEqual(["tomato", "potato", "grape"]);
    vi.resetModules();
  });

  it("includes crop field in FormData when submitPrediction is called", async () => {
    vi.resetModules();
    const capturedForms = [];
    vi.stubGlobal("fetch", vi.fn().mockImplementation((_url, opts) => {
      capturedForms.push(opts.body);
      return Promise.resolve({
        ok: true, status: 200,
        json: async () => ({
          status: "completed", prediction_status: "accepted", recommendation_status: "available",
          prediction: { class_id: "grape_black_rot", confidence: 0.99, probabilities: { grape_black_rot: 0.99 } },
          model: { version: "v1" },
          severity: { status: "not_requested" },
          disease_information: null,
          general_guidance: [],
          weather_context: { status: "not_requested" },
          weather_guidance: [],
          recommendation_message: null,
          explainability: { status: "unavailable" },
          history: { record_id: "r1", created_at: "2026-11-17T00:00:00Z" },
        }),
      });
    }));
    try {
      const api = await import("./api.js");
      const image = new File([new Uint8Array([1])], "leaf.png", { type: "image/png" });
      await api.submitPrediction({ image, crop: "grape", lesionMask: null, location: "" });
      expect(capturedForms.length).toBe(1);
      expect(capturedForms[0]).toBeInstanceOf(FormData);
      expect(capturedForms[0].get("crop")).toBe("grape");
      expect(capturedForms[0].get("image")).toBeTruthy();
    } finally {
      vi.resetModules();
    }
  });
});
