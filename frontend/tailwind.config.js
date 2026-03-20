/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Clean, neutral base
        background: "hsl(0 0% 98%)",
        foreground: "hsl(220 13% 18%)",

        // Card colors — pure white
        card: {
          DEFAULT: "hsl(0 0% 100%)",
          foreground: "hsl(220 13% 18%)",
        },

        // Primary — emerald green (used sparingly)
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

        // Secondary — light gray
        secondary: {
          DEFAULT: "hsl(220 14% 96%)",
          foreground: "hsl(220 13% 32%)",
        },

        // Muted — medium gray
        muted: {
          DEFAULT: "hsl(220 14% 93%)",
          foreground: "hsl(220 9% 46%)",
        },

        // Accent — warm amber
        accent: {
          DEFAULT: "hsl(42 95% 50%)",
          foreground: "hsl(220 13% 18%)",
        },

        // Destructive — red
        destructive: {
          DEFAULT: "hsl(0 72% 55%)",
          foreground: "hsl(0 0% 100%)",
        },

        // Popover — white
        popover: {
          DEFAULT: "hsl(0 0% 100%)",
          foreground: "hsl(220 13% 18%)",
        },

        // Border — neutral gray
        border: "hsl(220 13% 91%)",
        input: "hsl(220 13% 91%)",
        ring: "hsl(152 76% 36%)",

        // Status colors
        success: "hsl(145 80% 38%)",
        warning: "hsl(40 96% 50%)",
        info: "hsl(200 95% 50%)",

        // Emerald palette (accent use)
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

        // Forest palette (accent use)
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
            color: "hsl(220 13% 18%)",
            maxWidth: "none",
            h1: { color: "hsl(220 13% 18%)" },
            h2: { color: "hsl(220 13% 18%)", marginTop: "1.5em", marginBottom: "0.5em" },
            h3: { color: "hsl(220 13% 18%)", marginTop: "1.25em", marginBottom: "0.5em" },
            h4: { color: "hsl(220 13% 18%)" },
            strong: { color: "hsl(153 80% 30%)" },
            p: { marginTop: "0.75em", marginBottom: "0.75em" },
            li: { marginTop: "0.25em", marginBottom: "0.25em" },
            "ul > li::marker": { color: "hsl(153 80% 30%)" },
            "ol > li::marker": { color: "hsl(153 80% 30%)" },
            a: { color: "hsl(153 80% 30%)" },
            code: { color: "hsl(220 13% 32%)", backgroundColor: "hsl(220 14% 96%)", padding: "0.2em 0.4em", borderRadius: "0.25em" },
            hr: { borderColor: "hsl(220 13% 91%)" },
            blockquote: { borderLeftColor: "hsl(153 80% 30%)", color: "hsl(220 9% 46%)" },
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
