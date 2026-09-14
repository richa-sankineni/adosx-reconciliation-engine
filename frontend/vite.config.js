import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: the frontend calls /api/... and Vite forwards it to Django on
// :8000. Keeps the frontend code free of hardcoded hosts.
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
