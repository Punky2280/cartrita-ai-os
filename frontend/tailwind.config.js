/** @type {import('tailwindcss').Config} */

// Design tokens for Cartrita AI OS v2
const cartritaTokens = {
  colors: {
    primary: {
      'copilot-blue': '#6e81ff',
      'copilot-pink': '#e568ac',
      'anthropic-orange': '#d97e21',
      50: '#f0f4ff',
      100: '#e0e9ff',
      200: '#c7d7ff',
      300: '#a5bcff',
      400: '#8295ff',
      500: '#6e81ff',
      600: '#5b6aff',
      700: '#4c5aed',
      800: '#3d47c2',
      900: '#363d99',
      950: '#242759',
    },
    semantic: {
      success: {
        50: '#f0fdf4',
        500: '#22c55e',
        600: '#16a34a',
        700: '#15803d',
      },
      warning: {
        50: '#fffbeb',
        500: '#f97316',
        600: '#ea580c',
        700: '#c2410c',
      },
      error: {
        50: '#fef2f2',
        500: '#ef4444',
        600: '#dc2626',
        700: '#b91c1c',
      },
    },
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
      950: '#030712',
    },
  },
};

const config = {
  darkMode: ["class"],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
                // Cartrita v2 Brand Colors
        'copilot-blue': cartritaTokens.colors.primary['copilot-blue'],
        'copilot-pink': cartritaTokens.colors.primary['copilot-pink'],
        'anthropic-orange': cartritaTokens.colors.primary['anthropic-orange'],

        // Primary palette
        primary: cartritaTokens.colors.primary,

        // Semantic colors
        success: cartritaTokens.colors.semantic.success,
        warning: cartritaTokens.colors.semantic.warning,
        error: cartritaTokens.colors.semantic.error,

        // Enhanced grayscale
        gray: cartritaTokens.colors.gray,
      },
      borderRadius: {
        sm: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
        full: '9999px',
        // Keep shadcn/ui radius variables for compatibility
        DEFAULT: "var(--radius)",
      },
      keyframes: {
        "fade-in-up": {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        "slide-in": {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        "bounce-dots": {
          '0%, 80%, 100%': { transform: 'scale(0.8)', opacity: '0.5' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.3s ease-out",
        "slide-in": "slide-in 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        "bounce-dots": "bounce-dots 1.4s infinite ease-in-out",
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [
  "tailwindcss-animate"
  ],
};

export default config;
