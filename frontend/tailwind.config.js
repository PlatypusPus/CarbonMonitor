/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#FFFFFF",
        canvas: "#F4F7F5",
        leaf: "#2E9E6B",
        sky: "#4A9ECC",
        peach: "#F5A66D",
        rose: "#E8606A",
        sidebar: "#EBF5EF",
      },
    },
  },
  plugins: [],
};
