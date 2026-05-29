/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#f6f7f9',
          raised: '#ffffff',
        },
        surface: {
          DEFAULT: '#eef1f5',
          light: '#fefefe',
          lighter: '#e5e9f0',
          hover: '#e8edf5',
        },
        border: {
          DEFAULT: '#d8dee8',
          light: '#e7ebf1',
        },
        accent: {
          DEFAULT: '#2563eb',
          hover: '#1d4ed8',
          muted: '#dbeafe',
        },
        text: {
          DEFAULT: '#111827',
          secondary: '#4b5563',
          muted: '#7b8494',
        },
      },
      borderRadius: {
        DEFAULT: '8px',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.03)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04)',
        'elevated': '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [],
}
