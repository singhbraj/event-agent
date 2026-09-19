import { useState } from 'react'

import styles from './Composer.module.css'

export default function Composer({ onSend, disabled }) {
  const [value, setValue] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    if (!value.trim() || disabled) return

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
      />
      <button className={styles.button} type="submit" disabled={disabled}>
        Send
      </button>
    </form>
  )
}
