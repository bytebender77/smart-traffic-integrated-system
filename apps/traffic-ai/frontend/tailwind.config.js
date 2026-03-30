/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx}'
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace']
      },
      colors: {
        midnight: '#05070f',
        abyss: '#0a1222',
        neon: {
          // Renamed color-group still used across the UI, but tuned to a
          // more subdued "government prototype" palette.
          cyan: '#1d4ed8', // Blue
          magenta: '#f97316', // Saffron-ish accent
          lime: '#16a34a', // Green
          amber: '#f59e0b', // Amber
          red: '#dc2626' // Red
        }
      },
      boxShadow: {
        glow: '0 0 18px rgba(29, 78, 216, 0.22)',
        neon: '0 0 14px rgba(249, 115, 22, 0.18)'
      },
      backgroundImage: {
        grid: 'linear-gradient(rgba(29,78,216,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(22,163,74,0.06) 1px, transparent 1px)',
        aurora: 'radial-gradient(circle at top, rgba(29,78,216,0.14), transparent 55%), radial-gradient(circle at 80% 20%, rgba(22,163,74,0.10), transparent 45%)'
      },
      keyframes: {
        pulseSlow: {
          '0%, 100%': { opacity: 0.6 },
          '50%': { opacity: 1 }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' }
        },
        sweep: {
          '0%': { transform: 'translateX(-100%)', opacity: 0 },
          '50%': { opacity: 0.5 },
          '100%': { transform: 'translateX(100%)', opacity: 0 }
        }
      },
      animation: {
        pulseSlow: 'pulseSlow 3s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
        sweep: 'sweep 5s linear infinite'
      }
    }
  },
  plugins: []
};
