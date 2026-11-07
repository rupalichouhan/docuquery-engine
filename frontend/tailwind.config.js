/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#FDFBF7",
        parchment: "#FDFBF7",
        surface: "#FFFFFF",
        primary: {
          DEFAULT: "#2C4C3B",
          hover: "#8FA998",
          light: "#F0F4F1",
          subtle: "#E4EDE6",
        },
        "text-main": "#292524",
        "text-muted": "#78716C",
        "verified-bg": "#D1FAE5",
        "verified-text": "#065F46",
        "warm-border": "#E7E2D9",
        "warm-card": "#FFFFFF",
        "warm-bg": "#FDFBF7",
      },
      fontFamily: {
        serif: ["Lora", "Georgia", "Cambria", "serif"],
        sans: ["Figtree", "Nunito", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        warm: "0 1px 3px 0 rgba(41, 37, 36, 0.05), 0 1px 2px -1px rgba(41, 37, 36, 0.05)",
        "warm-md": "0 4px 6px -1px rgba(41, 37, 36, 0.07), 0 2px 4px -2px rgba(41, 37, 36, 0.05)",
        "warm-lg": "0 10px 15px -3px rgba(41, 37, 36, 0.08), 0 4px 6px -4px rgba(41, 37, 36, 0.04)",
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};
