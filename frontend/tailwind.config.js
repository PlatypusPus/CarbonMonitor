/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#FFFFFF",
        canvas: "#F4F7F5",
        sidebar: "#F2F7F3",
        leaf: { DEFAULT: "#2E9E6B", hover: "#268057", deep: "#23895A" },
        sky: "#4A9ECC",
        mint: "#A8DBBF",
        peach: "#F5A66D",
        rose: "#E8606A",
        ink: "#33332F",
        body: "#55554F",
        muted: "#A8A89F",
        line: "#E6E6E0",
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
