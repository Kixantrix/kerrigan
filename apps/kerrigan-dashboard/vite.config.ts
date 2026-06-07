import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

const host = process.env.TAURI_DEV_HOST;
const appVersion = process.env.npm_package_version ?? "0.1.0";

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      fs: fileURLToPath(new URL("./src/lib/shims/fs.ts", import.meta.url)),
      os: fileURLToPath(new URL("./src/lib/shims/os.ts", import.meta.url)),
      path: fileURLToPath(new URL("./src/lib/shims/path.ts", import.meta.url)),
      "node:fs/promises": fileURLToPath(
        new URL("./src/lib/shims/fs-promises.ts", import.meta.url),
      ),
    },
  },

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent Vite from obscuring rust errors
  clearScreen: false,
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      // 3. tell Vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
}));
