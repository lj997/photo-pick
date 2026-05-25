/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#faf9f7',
          raised: '#ffffff',
        },
        surface: {
          DEFAULT: '#f0ebe4',
          light: '#fefefe',
          lighter: '#e8e2da',
          hover: '#e8e2da',
        },
        border: {
          DEFAULT: '#d6d3d1',
          light: '#e7e5e4',
        },
        accent: {
          DEFAULT: '#b45309',
          hover: '#92400e',
          muted: '#fef3c7',
        },
        text: {
          DEFAULT: '#1c1917',
          secondary: '#57534e',
          muted: '#78716c',
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
