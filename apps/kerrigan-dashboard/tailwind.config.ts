import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "neutral-bg": "#0D1117",
        "neutral-fg": "#E8EAED",
        brand: "#5965F2",
        accent: "#F59E0B",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      spacing: {
        "0.5": "2px",
        "1": "4px",
        "1.5": "6px",
        "2": "8px",
        "2.5": "10px",
        "3": "12px",
        "3.5": "14px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "8": "32px",
        "13": "52px",
      },
      fontSize: {
        display: ["28px", { lineHeight: "1.2" }],
        heading: ["18px", { lineHeight: "1.2" }],
        body: ["14px", { lineHeight: "1.5" }],
        micro: ["12px", { lineHeight: "1.4" }],
        nano: ["10px", { lineHeight: "1.4" }],
      },
    },
  },
} satisfies Config;
