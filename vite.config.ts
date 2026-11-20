import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Every folder in projects/ with an index.html becomes its own page,
// so adding a project doesn't require editing this file.
const projects = readdirSync("projects", { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);

export default defineConfig({
  // GitHub Pages serves this repo at msmith126.github.io/homepage/
  base: "/homepage/",
  plugins: [react()],
  build: {
    rolldownOptions: {
      input: {
        main: resolve("index.html"),
        ...Object.fromEntries(
          projects.map((name) => [
            name,
            resolve("projects", name, "index.html"),
          ]),
        ),
      },
    },
  },
});
