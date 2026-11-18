import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/predict": "http://127.0.0.1:8000",
      "/predictions": "http://127.0.0.1:8000",
      "/weather": "http://127.0.0.1:8000",
      "/recommendations": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/testSetup.js",
    css: true,
  },
});
