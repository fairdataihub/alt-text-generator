// @ts-check
import withNuxt from ".nuxt/eslint.config.mjs";
import stylistic from "@stylistic/eslint-plugin";
import prettierPlugin from "eslint-plugin-prettier";
import perfectionist from "eslint-plugin-perfectionist";

export default withNuxt({
  languageOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    globals: {
      browser: true,
      node: true,
    },
  },
  plugins: {
    "unused-imports": (await import("eslint-plugin-unused-imports")).default,
    "@stylistic": stylistic,
    prettier: prettierPlugin,
    perfectionist,
  },
  rules: {
    "@typescript-eslint/no-unused-vars": "off",

    "@stylistic/arrow-parens": ["error", "always"],
    "@stylistic/semi": ["error", "always"],
    "@stylistic/comma-dangle": ["error", "always-multiline"],
    "@stylistic/padding-line-between-statements": [
      "error",
      {
        blankLine: "always",
        next: "return",
        prev: "*",
      },
    ],
    endOfLine: "off",
    "@stylistic/quotes": ["error", "double"],
    "no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "warn" : "off",
    "unused-imports/no-unused-imports": "error",
    "unused-imports/no-unused-vars": [
      "warn",
      {
        args: "after-used",
        argsIgnorePattern: "^_",
        vars: "all",
        varsIgnorePattern: "^_",
      },
    ],
    "prettier/prettier": [
      "error",
      {
        endOfLine: "auto",
      },
    ],
    "vue/padding-line-between-tags": [
      "error",
      [{ blankLine: "always", next: "*", prev: "*" }],
    ],
  },
});
