/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk-inspired palette
        'void': {
          900: '#0a0a0f',
          800: '#12121a',
          700: '#1a1a25',
          600: '#252532',
        },
        'neon': {
          cyan: '#00f5d4',
          pink: '#f72585',
          purple: '#7b2cbf',
          yellow: '#fee440',
          orange: '#ff6b35',
        },
        'slate': {
          850: '#1e293b',
        }
      },
      fontFamily: {
        'display': ['Outfit', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': `linear-gradient(rgba(0, 245, 212, 0.03) 1px, transparent 1px),
                         linear-gradient(90deg, rgba(0, 245, 212, 0.03) 1px, transparent 1px)`,
        'gradient-radial': 'radial-gradient(ellipse at center, var(--tw-gradient-stops))',
      },
      backgroundSize: {
        'grid': '50px 50px',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(0, 245, 212, 0.3)' },
          '100%': { boxShadow: '0 0 30px rgba(0, 245, 212, 0.6)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      boxShadow: {
        'neon': '0 0 20px rgba(0, 245, 212, 0.3)',
        'neon-pink': '0 0 20px rgba(247, 37, 133, 0.3)',
        'neon-purple': '0 0 20px rgba(123, 44, 191, 0.3)',
      },
    },
  },
  plugins: [],
}
