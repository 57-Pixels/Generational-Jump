import { defineConfig } from "vite";

// Pages: https://57-pixels.github.io/FantasyMilitaryProject/
// Local `npm run dev` uses "/" so you open http://localhost:5173/
const pagesBase = "/FantasyMilitaryProject/";

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? pagesBase : "/",
  root: ".",
  publicDir: "public",
  server: {
    port: 5173,
    open: false,
  },
});
