import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // The FastAPI server serves the built app at /app, so every file path starts there.
  base: "/app/",
  plugins: [react()],
  // During `npm run dev`, send /api calls to the FastAPI server running on port 8000.
  server: { proxy: { "/api": "http://localhost:8000" } },
});
