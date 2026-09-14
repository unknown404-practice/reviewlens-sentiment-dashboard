/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080c14",
        surface: {
          DEFAULT: "#0f172a",
          secondary: "#162036",
          tertiary: "#1e293b",
        },
        border: {
          DEFAULT: "rgba(255, 255, 255, 0.08)",
          subtle: "rgba(255, 255, 255, 0.05)",
          focus: "rgba(56, 189, 248, 0.5)",
        },
        brand: {
          primary: "#38bdf8",
          hover: "#0284c7",
        },
        sentiment: {
          positive: "#10b981",
          positiveMuted: "rgba(16, 185, 129, 0.12)",
          neutral: "#f59e0b",
          neutralMuted: "rgba(245, 158, 11, 0.12)",
          negative: "#f43f5e",
          negativeMuted: "rgba(244, 63, 94, 0.12)",
        }
      },
    },
  },
  plugins: [],
};
