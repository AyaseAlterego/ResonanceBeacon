/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          50: '#f0f0f5',
          100: '#e0e0eb',
          200: '#c1c1d7',
          300: '#a2a2c3',
          400: '#8383af',
          500: '#64649b',
          600: '#4d4d7a',
          700: '#363659',
          800: '#1f1f38',
          900: '#0a0a1a',
          950: '#050510',
        },
        accent: {
          50: '#eef2ff',
          100: '#dbe4ff',
          200: '#bac8ff',
          300: '#91a7ff',
          400: '#748ffc',
          500: '#5c7cfa',
          600: '#4c6ef5',
          700: '#4263eb',
          800: '#3b5bdb',
          900: '#364fc7',
        },
        cyber: {
          blue: '#00d4ff',
          green: '#00ff88',
          red: '#ff4466',
          yellow: '#ffcc00',
          purple: '#b44aff',
        },
        background: '#0a0a0f',
        foreground: '#e0e0eb',
        primary: {
          DEFAULT: '#a29bfe',
          foreground: '#0a0a0f',
        },
        muted: {
          DEFAULT: '#1f1f38',
          foreground: '#8383af',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
