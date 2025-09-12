import React, { useEffect, useRef } from 'react'
import { useAtom } from 'jotai'
import { settingsAtom } from '@/stores'

type Props = {
  open: boolean
  onClose: () => void
}

export default function SettingsModal({ open, onClose }: Props) {
  const [settings, setSettings] = useAtom(settingsAtom)
  const firstFieldRef = useRef<HTMLButtonElement | null>(null)

  useEffect(() => {
    if (open) {
      // focus first control for accessibility
      const t = setTimeout(() => firstFieldRef.current?.focus(), 0)
      return () => clearTimeout(t)
    }
  }, [open])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-title"
    >
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative z-10 w-full max-w-lg rounded-xl border border-gray-700 bg-gray-900 p-5 text-white shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 id="settings-title" className="text-lg font-semibold">Settings</h2>
          <button
            onClick={onClose}
            aria-label="Close settings"
            className="rounded bg-gray-800 hover:bg-gray-700 px-2 py-1"
          >
            Close
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Auto scroll</div>
              <div className="text-sm text-gray-400">Scroll to latest message automatically</div>
            </div>
            <button
              ref={firstFieldRef}
              onClick={() => setSettings((s) => ({ ...s, autoScroll: !s.autoScroll }))}
              className={`px-3 py-1 rounded border ${settings.autoScroll ? 'bg-emerald-600 border-emerald-500' : 'bg-gray-800 border-gray-700'}`}
              aria-pressed={settings.autoScroll}
              aria-label="Toggle auto scroll"
            >
              {settings.autoScroll ? 'On' : 'Off'}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Reduced motion</div>
              <div className="text-sm text-gray-400">Disable heavy animations for performance</div>
            </div>
            <button
              onClick={() => setSettings((s) => ({ ...s, reducedMotion: !s.reducedMotion }))}
              className={`px-3 py-1 rounded border ${settings.reducedMotion ? 'bg-emerald-600 border-emerald-500' : 'bg-gray-800 border-gray-700'}`}
              aria-pressed={settings.reducedMotion}
              aria-label="Toggle reduced motion"
            >
              {settings.reducedMotion ? 'On' : 'Off'}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <label htmlFor="font-size" className="font-medium">Font size</label>
            <select
              id="font-size"
              value={settings.fontSize || 'md'}
              onChange={(e) => setSettings((s) => ({ ...s, fontSize: e.target.value as 'sm' | 'md' | 'lg' }))}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1"
            >
              <option value="sm">Small</option>
              <option value="md">Medium</option>
              <option value="lg">Large</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}
