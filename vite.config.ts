import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  server: {
    port: 3000, // Ensure correct port for debugging
    open: true, // Opens browser automatically
    strictPort: true, // Prevents fallback to another port
    host: "localhost", // Ensures debugging works with VS Code
    hmr: {
      overlay: false, // Prevents annoying overlay errors
    },
  },
  build: {
    sourcemap: true, // Enables source maps for debugging
    target: "esnext", // Ensures modern JavaScript output
    outDir: "dist",
  },
  resolve: {
    alias: {
      "~": "/app", // Ensures TypeScript paths work
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      target: "esnext",
    },
  },
});
