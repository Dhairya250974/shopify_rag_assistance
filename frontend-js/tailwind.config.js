import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        shopify: {
          50: "#f5faed",
          100: "#e6f2d2",
          500: "#95bf47",
          600: "#769b35",
          700: "#5b7a2b"
        },
        ink: {
          950: "#101315",
          900: "#171b1f",
          800: "#22282d"
        }
      },
      boxShadow: {
        soft: "0 18px 60px rgba(16, 24, 40, 0.10)",
        glow: "0 24px 80px rgba(149, 191, 71, 0.25)"
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" }
        }
      },
      animation: {
        shimmer: "shimmer 1.8s ease-in-out infinite"
      }
    }
  },
  plugins: [typography]
};
