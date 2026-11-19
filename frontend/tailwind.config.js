/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        limeAccent: '#DDFB5C',
        limeHover: '#D0F244',
        obsidian: '#0F172A',
        skyDeep: '#0B63B8',
        skyMid: '#1E88E5',
      },
      letterSpacing: {
        tightest: '-0.035em',
        micro: '0.08em',
      },
      boxShadow: {
        'clay-card':
          '10px 10px 24px -4px rgba(175, 192, 214, 0.48), -8px -8px 20px 0px rgba(255, 255, 255, 0.96), inset 1px 1px 2px 0px rgba(255, 255, 255, 0.85)',
        'clay-card-hover':
          '14px 14px 30px -4px rgba(165, 185, 210, 0.56), -8px -8px 22px 0px rgba(255, 255, 255, 0.98), inset 1px 1px 2px 0px rgba(255, 255, 255, 0.9)',
        'clay-input':
          'inset 3px 3px 6px rgba(160, 175, 198, 0.36), inset -3px -3px 6px rgba(255, 255, 255, 0.92)',
        'clay-btn-blue':
          '0 8px 20px -3px rgba(29, 78, 216, 0.45), inset 0 2px 3px rgba(255, 255, 255, 0.42), inset 0 -2px 3px rgba(0, 0, 0, 0.22)',
        'clay-btn-green':
          '0 8px 20px -3px rgba(16, 185, 129, 0.42), inset 0 2px 3px rgba(255, 255, 255, 0.42), inset 0 -2px 3px rgba(0, 0, 0, 0.18)',
        'clay-pill':
          '5px 5px 12px rgba(175, 192, 214, 0.38), -4px -4px 10px rgba(255, 255, 255, 0.95), inset 1px 1px 1px rgba(255, 255, 255, 0.8)',
      },
    },
  },
  plugins: [],
};
