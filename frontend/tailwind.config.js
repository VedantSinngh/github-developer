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
        canvas: {
          DEFAULT: "#f5f5f5",
          soft: "#fafafa",
          deep: "#0c0a09",
        },
        ink: {
          DEFAULT: "#0c0a09",
          primary: "#292524",
          "primary-active": "#0c0a09",
        },
        body: {
          DEFAULT: "#4e4e4e",
          strong: "#292524",
        },
        muted: {
          DEFAULT: "#777169",
          soft: "#a8a29e",
        },
        surface: {
          card: "#ffffff",
          strong: "#f0efed",
          dark: "#0c0a09",
          "dark-elevated": "#1c1917",
        },
        hairline: {
          DEFAULT: "#e7e5e4",
          soft: "#f0efed",
          strong: "#d6d3d1",
        },
        orb: {
          mint: "#a7e5d3",
          peach: "#f4c5a8",
          lavender: "#c8b8e0",
          sky: "#a8c8e8",
          rose: "#e8b8c4",
        },
      },
      fontFamily: {
        serif: ["'EB Garamond'", "'Times New Roman'", "serif"],
        sans: ["Inter", "sans-serif"],
      },
      borderRadius: {
        pill: "9999px",
        xl: "16px",
        xxl: "24px",
      },
      boxShadow: {
        soft: "0 4px 16px rgba(0, 0, 0, 0.04)",
      },
      spacing: {
        section: "96px",
      },
    },
  },
  plugins: [],
};
