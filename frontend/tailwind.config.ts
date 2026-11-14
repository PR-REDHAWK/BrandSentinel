import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f4f9",
          100: "#d9e2ec",
          500: "#1e3a8a",
          600: "#1e40af",
          700: "#1d4ed8",
          800: "#172554",
          900: "#0b1528",
        },
      },
    },
  },
  plugins: [],
};

export default config;
