import { NavLink, Outlet } from 'react-router-dom'

import styles from './App.module.css'

export default function App() {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.inner}>
          <div className={styles.brand}>
            <span className={styles.mark} aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path
                  d="M3.2 4.2h11.6v2.7a1.7 1.7 0 0 0 0 3.4v2.7H3.2V10.3a1.7 1.7 0 0 0 0-3.4V4.2Z"
                  stroke="currentColor"
                  strokeWidth="1.4"
                />
              </svg>
            </span>
            <div>
              <p className={styles.kicker}>Live events</p>
              <h1 className={styles.title}>Event Agent</h1>
            </div>
          </div>
          <nav className={styles.nav} aria-label="Primary navigation">
            <NavLink
              className={({ isActive }) => (isActive ? styles.active : undefined)}
              end
              to="/"
            >
              Chat
            </NavLink>
            <NavLink
              className={({ isActive }) => (isActive ? styles.active : undefined)}
              to="/tickets"
            >
              Tickets
            </NavLink>
          </nav>
        </div>
      </header>

      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
