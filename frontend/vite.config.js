import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// In dev, proxy /api to the FastAPI backend so the frontend can use
// same-origin relative URLs (which also work unchanged inside Tauri).
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
            },
        },
    },
});
