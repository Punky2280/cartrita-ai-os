/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          hover: "hsl(var(--primary-hover))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        'cartrita-blue': '#2563EB',
        'copilot-blue': '#1B2951',
        'copilot-blue-light': '#2A3F73',
        'copilot-blue-dark': '#141E3C',
        'chatgpt-grey': '#202123',
        'chatgpt-grey-light': '#2D2D2D',
        'chatgpt-grey-dark': '#1A1A1A',
        'fuschia-pink': '#E91E63',
        'fuschia-pink-light': '#F06292',
        'fuschia-pink-dark': '#AD1457',
        // Agent color mapping
        'supervisor': '#2563EB',
        'knowledge-agent': '#3B82F6',
        'code-agent': '#1B2951',
        'research-agent': '#2A3F73',
        'task-agent': '#141E3C',
        'computer-use': '#E91E63',
        'audio': '#F06292',
        'evaluation': '#10B981',
        'memory': '#F59E0B',
        'model-selector': '#EF4444',
        'safety': '#6B7280',
      },
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
        'jetbrains-mono': ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-fuschia': 'pulse 1.5s ease-in-out infinite',
        'bounce-voice': 'bounce 0.5s ease-in-out',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}