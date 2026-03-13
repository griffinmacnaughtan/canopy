/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Vibrant forest green theme
        background: "hsl(145 30% 96%)",
        foreground: "hsl(152 40% 10%)",

        // Card colors - Clean white with green tint
        card: {
          DEFAULT: "hsl(150 30% 99%)",
          foreground: "hsl(152 40% 10%)",
        },

        // Primary - Vibrant emerald green
        primary: {
          DEFAULT: "hsl(152 76% 36%)",
          foreground: "hsl(0 0% 100%)",
          50: "hsl(149 80% 96%)",
          100: "hsl(149 75% 90%)",
          200: "hsl(150 70% 80%)",
          300: "hsl(151 65% 65%)",
          400: "hsl(152 70% 50%)",
          500: "hsl(152 76% 36%)",
          600: "hsl(153 80% 30%)",
          700: "hsl(154 82% 24%)",
          800: "hsl(155 80% 18%)",
          900: "hsl(156 78% 12%)",
        },

        // Secondary - Soft mint
        secondary: {
          DEFAULT: "hsl(145 35% 93%)",
          foreground: "hsl(152 30% 20%)",
        },

        // Muted - Sage
        muted: {
          DEFAULT: "hsl(145 20% 90%)",
          foreground: "hsl(150 15% 40%)",
        },

        // Accent - Forest gold
        accent: {
          DEFAULT: "hsl(42 95% 50%)",
          foreground: "hsl(152 40% 10%)",
        },

        // Destructive - Coral
        destructive: {
          DEFAULT: "hsl(0 72% 55%)",
          foreground: "hsl(0 0% 100%)",
        },

        // Popover - White
        popover: {
          DEFAULT: "hsl(150 30% 99%)",
          foreground: "hsl(152 40% 10%)",
        },

        // Border - Green-tinted gray
        border: "hsl(145 25% 86%)",
        input: "hsl(145 25% 86%)",
        ring: "hsl(152 76% 36%)",

        // Status colors - Vivid nature palette
        success: "hsl(145 80% 38%)",
        warning: "hsl(40 96% 50%)",
        info: "hsl(200 95% 50%)",

        // Emerald palette
        emerald: {
          50: "hsl(149 80% 96%)",
          100: "hsl(149 75% 90%)",
          200: "hsl(150 70% 80%)",
          300: "hsl(151 65% 65%)",
          400: "hsl(152 70% 50%)",
          500: "hsl(152 76% 36%)",
          600: "hsl(153 80% 30%)",
          700: "hsl(154 82% 24%)",
          800: "hsl(155 80% 18%)",
          900: "hsl(156 78% 12%)",
          950: "hsl(157 80% 6%)",
        },

        // Forest palette
        forest: {
          50: "hsl(140 60% 96%)",
          100: "hsl(141 55% 90%)",
          200: "hsl(142 50% 80%)",
          300: "hsl(143 48% 65%)",
          400: "hsl(144 55% 48%)",
          500: "hsl(145 70% 35%)",
          600: "hsl(146 75% 28%)",
          700: "hsl(147 78% 22%)",
          800: "hsl(148 76% 16%)",
          900: "hsl(149 74% 10%)",
          950: "hsl(150 80% 5%)",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Sora", "system-ui", "sans-serif"],
        serif: ["Playfair Display", "Georgia", "serif"],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        shimmer: "shimmer 2s infinite",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      typography: {
        DEFAULT: {
          css: {
            color: "hsl(152 40% 10%)",
            maxWidth: "none",
            h1: { color: "hsl(152 40% 10%)" },
            h2: { color: "hsl(152 40% 10%)", marginTop: "1.5em", marginBottom: "0.5em" },
            h3: { color: "hsl(152 40% 10%)", marginTop: "1.25em", marginBottom: "0.5em" },
            h4: { color: "hsl(152 40% 10%)" },
            strong: { color: "hsl(152 76% 36%)" },
            p: { marginTop: "0.75em", marginBottom: "0.75em" },
            li: { marginTop: "0.25em", marginBottom: "0.25em" },
            "ul > li::marker": { color: "hsl(152 76% 36%)" },
            "ol > li::marker": { color: "hsl(152 76% 36%)" },
            a: { color: "hsl(152 76% 36%)" },
            code: { color: "hsl(152 30% 20%)", backgroundColor: "hsl(145 35% 93%)", padding: "0.2em 0.4em", borderRadius: "0.25em" },
            hr: { borderColor: "hsl(145 25% 86%)" },
            blockquote: { borderLeftColor: "hsl(152 76% 36%)", color: "hsl(150 15% 40%)" },
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
