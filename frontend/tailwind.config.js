/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './components/**/*.{vue,js,ts}',
    './pages/**/*.{vue,js,ts}',
    './app/**/*.{vue,js,ts}',
    './composables/**/*.{js,ts}'
  ],
  theme: {
    extend: {
      colors: {
        // 主背景
        bg: {
          DEFAULT: '#0f172a',
          light: '#1e293b',
          card: 'rgba(30, 41, 59, 0.6)',
          soft: 'rgba(15, 23, 42, 0.85)'
        },
        // 文字色
        text: {
          primary: '#e2e8f0',
          secondary: '#94a3b8',
          muted: '#64748b'
        },
        // 点缀三色
        accent: {
          purple: '#a78bfa',
          blue: '#60a5fa',
          green: '#34d399',
          gold: '#fbbf24',
          pink: '#f472b6'
        },
        // 主题色（与 topics 表对应）
        topic: {
          llm: '#a78bfa',
          rag: '#34d399',
          agent: '#60a5fa',
          transformer: '#fbbf24',
          diffusion: '#f472b6',
          mlops: '#c084fc'
        }
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          '"PingFang SC"',
          '"Hiragino Sans GB"',
          '"Microsoft YaHei"',
          '"Helvetica Neue"',
          'Helvetica',
          'Arial',
          'sans-serif'
        ],
        mono: ['"JetBrains Mono"', 'Menlo', 'Monaco', '"Courier New"', 'monospace']
      },
      borderRadius: {
        card: '14px',
        chip: '20px'
      },
      boxShadow: {
        glow: '0 0 40px rgba(167, 139, 250, 0.15)',
        glowBlue: '0 0 40px rgba(96, 165, 250, 0.15)',
        glowGreen: '0 0 40px rgba(52, 211, 153, 0.15)'
      },
      backgroundImage: {
        'gradient-text': 'linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%)',
        'gradient-card': 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(52, 211, 153, 0.05) 100%)',
        'gradient-hero': 'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.15) 0%, rgba(52, 211, 153, 0.05) 40%, transparent 70%)'
      }
    }
  },
  plugins: []
}
