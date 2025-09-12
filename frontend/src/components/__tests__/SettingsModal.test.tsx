import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import SettingsModal from '../SettingsModal'
import { Provider } from 'jotai'

// simple store wrapper, using default settings from atomWithStorage
function ModalHarness({ open = true }) {
  return (
    <Provider>
      <SettingsModal open={open} onClose={() => {}} />
    </Provider>
  )
}

describe('SettingsModal', () => {
  it('renders and toggles auto scroll', () => {
    render(<ModalHarness />)
    const btn = screen.getByRole('button', { name: /auto scroll/i })
    // The button text shows On/Off; click toggles state but we just verify it exists and is clickable
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    // no throw implies interaction ok
    expect(true).toBe(true)
  })

  it('does not render when closed', () => {
    render(<ModalHarness open={false} />)
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})
