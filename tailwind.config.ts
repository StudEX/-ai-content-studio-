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
        background: "var(--background)",
        foreground: "var(--foreground)",
        obsidian: { DEFAULT: '#0A0A0B', 50: '#1A1A1D', 100: '#141416', 900: '#0A0A0B' },
        ember: { DEFAULT: '#FF4500', 300: '#FF8A65', 400: '#FF6B3D', 500: '#FF4500', 600: '#CC3700' },
        signal: { DEFAULT: '#FF8C00', 400: '#FFB347' },
        terminal: { DEFAULT: '#00FF41' },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};
export default config;
