import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Locally (running `npm run dev` on your host machine): defaults to localhost:8000.
// Inside Docker/Podman compose: the frontend container can't reach the backend
// via "localhost" — that refers to the frontend container itself. Compose sets
// BACKEND_URL=http://backend:8000 (the service name) to fix this — see
// docker-compose.yml's frontend service environment block.
const backendTarget = process.env.BACKEND_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
});
