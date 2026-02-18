// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        transparent: 'transparent',
        current: 'currentColor',
        'white': '#ffffff',
        'bleu': '#053D5E',
        'bleu-ciel': '#8faadc',
        'vert': '#7FC241',
        'blanc': '#F4F3F2',
        'blanc2': '#e5e5e5 ',
        'blanc3': '#fafeff',
        
      }
    },
  },
  plugins: [],
}
