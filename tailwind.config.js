/*
PURPOSE: Tailwind CSS configuration for styling

KEY COMPONENTS:
- Content paths for CSS purging
- Theme customization options
- Plugin configuration

WHY USED:
- Utility-first CSS framework
- Responsive design capabilities
- Professional styling with minimal custom CSS
*/

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
