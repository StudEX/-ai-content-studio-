/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        cyan: { DEFAULT: '#00C9C8', 50: '#E0FFFE', 400: '#00C9C8', 500: '#00B3B2', 600: '#009A99' },
        obsidian: { DEFAULT: '#0A0A0B', 50: '#1A1A1D', 100: '#141416', 900: '#0A0A0B' },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
    },
  },
  plugins: [],
}
