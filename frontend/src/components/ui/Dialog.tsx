import React, { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

interface DialogProps {
  open: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  initialFocusRef?: React.RefObject<HTMLElement>
}

export const Dialog: React.FC<DialogProps> = ({ open, onClose, title, children, initialFocusRef }) => {
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open && initialFocusRef?.current) {
      initialFocusRef.current.focus()
    }
    if (!open) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'Tab') {
        // Trap focus
        const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        if (!focusable || focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          last.focus(); e.preventDefault()
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus(); e.preventDefault()
        }
      }
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onClose, initialFocusRef])

  if (!open) return null
  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        className="bg-white dark:bg-chatgpt-grey-light rounded-lg shadow-xl max-w-lg w-full p-6 relative"
        tabIndex={-1}
        onClick={e => e.stopPropagation()}
      >
        {title && <h2 className="text-lg font-bold mb-4">{title}</h2>}
        {children}
        <button
          className="absolute top-2 right-2 text-muted-foreground hover:text-primary focus:outline-none"
          aria-label="Close dialog"
          onClick={onClose}
        >
          ×
        </button>
      </div>
    </div>,
    document.body
  )
}
