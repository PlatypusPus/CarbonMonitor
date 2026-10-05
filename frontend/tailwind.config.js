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
        mint: "#A8DBBF",
        peach: "#F5A66D",
        rose: "#E8606A",
        ink: "#20372C",
        body: "#52675B",
        muted: "#65766B",
        line: "#DCE5DF",
      },
      fontFamily: {
        sans: ['"Public Sans"', "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      borderRadius: {
        card: "14px",
        pill: "20px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.08)",
      },
    },
  },
  plugins: [],
};
