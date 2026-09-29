/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#FFFFFF",
        canvas: "#F4F7F5",
        sidebar: "#F2F7F3",
        leaf: {
          DEFAULT: "#2E9E6B",
          hover: "#268057",
          deep: "#23895A",
          action: "#236F4B",
          "action-hover": "#195A3C",
        },
        sky: "#4A9ECC",
        mint: "#A8DBBF",
        peach: "#F5A66D",
        rose: "#E8606A",
        ink: "#20372C",
        body: "#52675B",
        muted: "#65766B",
        line: "#DCE5DF",
      },
      fontFamily: {
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
        mono: ['"Roboto Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "14px",
        pill: "20px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.08)",
        pin: "0 2px 5px rgba(0,0,0,0.15)",
      },
      keyframes: {
        pulseDot: {
          "0%,100%": { transform: "scale(1)", opacity: "1" },
          "50%": { transform: "scale(1.7)", opacity: "0.35" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "pulse-dot": "pulseDot 1.6s ease-in-out infinite",
        shimmer: "shimmer 1.4s linear infinite",
      },
    },
  },
  plugins: [],
};
