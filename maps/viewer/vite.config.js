import { defineConfig } from "vite";

// Relative base so GitHub Pages keeps working after repo renames
// (avoids hardcoding /OldRepoName/).
export default defineConfig({
  base: "./",
  root: ".",
  publicDir: "public",
  server: {
    port: 5173,
    open: false,
  },
});
