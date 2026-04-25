/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-cream': '#FAF7F2',
        'bg-white': '#FFFFFF',
        'border-soft': '#E8E0D4',
        'slot-empty': '#F0EAE0',
        'box-resting': '#D4C4A8',
        'box-active': '#8B6F47',
        shuttle: '#5C4A38',
        'pallet-fill': '#B8A082',
        'pallet-empty': '#F5F0E8',
        'text-primary': '#2A2520',
        'text-secondary': '#888073',
        accent: '#8B6F47',
        'status-green': '#5CB874',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      letterSpacing: {
        ui: '0.08em',
      },
    },
  },
  plugins: [],
}

