import React from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { Button } from '@/components/ui'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const next = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'

  return (
    <Button
      variant="ghost"
      size="sm"
      aria-label={`Switch theme (current: ${theme})`}
      title={`Switch theme (current: ${theme})`}
      onClick={() => setTheme(next)}
    >
      {theme === 'dark' ? 'Dark' : theme === 'light' ? 'Light' : 'System'}
    </Button>
  )
}
