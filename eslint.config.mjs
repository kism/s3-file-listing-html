import js from "@eslint/js";
import globals from "globals";
import { defineConfig } from "eslint/config";

export default defineConfig([{ files: ["./s3_file_listing_html/**/*.js"], languageOptions: { ecmaVersion: 3, sourceType: "script" } }]);
