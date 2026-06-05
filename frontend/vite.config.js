import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      recharts: "recharts/es6",  // ← force Vite to use the ES module build
    },
  },
});