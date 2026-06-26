import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy /api calls to the Flask backend so the frontend code can just
    // fetch("/api/predict") without worrying about CORS or ports.
    proxy: {
      "/api": "http://localhost:5000",
    },
  },
});
