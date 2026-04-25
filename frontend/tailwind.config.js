/** @type {import('tailwindcss').Config} */
// Color keys are written verbatim from BRIEF.md F2 (e.g. "bg-cream", "text-primary"),
// which means usage looks like `bg-bg-cream` / `text-text-primary`. Awkward but
// keeps the design tokens 1:1 with the spec.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "bg-cream": "#FAF7F2",
        "border-soft": "#E8E0D4",
        "slot-empty": "#F0EAE0",
        "box-resting": "#D4C4A8",
        "box-active": "#8B6F47",
        shuttle: "#5C4A38",
        "pallet-fill": "#B8A082",
        "pallet-empty": "#F5F0E8",
        "text-primary": "#2A2520",
        "text-secondary": "#888073",
        accent: "#8B6F47",
        "status-green": "#5CB874",
      },
      fontFamily: {
        sans: ["Georgia", "serif"],
        mono: ["Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
