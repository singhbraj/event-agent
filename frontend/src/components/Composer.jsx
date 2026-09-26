import { useState } from 'react'

import styles from './Composer.module.css'

export default function Composer({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const canSend = Boolean(value.trim()) && !disabled

  function handleSubmit(event) {
    event.preventDefault()
    if (!canSend) return

    onSend(value)
    setValue('')
  }

  return (
    <form className={styles.composer} onSubmit={handleSubmit}>
      <input
        className={styles.input}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Find concerts in London this weekend"
        aria-label="Message the event agent"
        disabled={disabled}
      />
      <button className={styles.button} type="submit" disabled={!canSend} aria-label="Send">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path
            d="M3 8h10M9 4l4 4-4 4"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </form>
  )
}
