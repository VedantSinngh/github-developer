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
        semantic: {
          success: "#16a34a",
          error: "#dc2626",
        },
      },
      fontFamily: {
        serif: ["var(--font-eb-garamond)", "'Times New Roman'", "serif"],
        sans: ["var(--font-inter)", "Inter", "sans-serif"],
      },
      fontSize: {
        "display-mega": ["64px", { lineHeight: "1.05", letterSpacing: "-1.92px", fontWeight: "300" }],
        "display-xl": ["48px", { lineHeight: "1.08", letterSpacing: "-0.96px", fontWeight: "300" }],
        "display-lg": ["36px", { lineHeight: "1.17", letterSpacing: "-0.36px", fontWeight: "300" }],
        "display-md": ["32px", { lineHeight: "1.13", letterSpacing: "-0.32px", fontWeight: "300" }],
        "display-sm": ["24px", { lineHeight: "1.2", letterSpacing: "0px", fontWeight: "300" }],
        "title-md": ["20px", { lineHeight: "1.35", letterSpacing: "0px", fontWeight: "500" }],
        "title-sm": ["18px", { lineHeight: "1.44", letterSpacing: "0.18px", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "1.5", letterSpacing: "0.16px", fontWeight: "400" }],
        "body-strong": ["16px", { lineHeight: "1.5", letterSpacing: "0.16px", fontWeight: "500" }],
        "body-sm": ["15px", { lineHeight: "1.47", letterSpacing: "0.15px", fontWeight: "400" }],
        caption: ["14px", { lineHeight: "1.5", letterSpacing: "0px", fontWeight: "400" }],
        "caption-uppercase": ["12px", { lineHeight: "1.4", letterSpacing: "0.96px", fontWeight: "600" }],
        "button": ["15px", { lineHeight: "1.0", letterSpacing: "0px", fontWeight: "500" }],
        "nav-link": ["15px", { lineHeight: "1.4", letterSpacing: "0px", fontWeight: "500" }],
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
