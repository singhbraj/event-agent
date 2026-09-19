import { NavLink, Outlet } from 'react-router-dom'

import styles from './App.module.css'

export default function App() {
  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1 className={styles.title}>Event Agent</h1>
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
      </header>

      <main className={styles.thread}>
        <Outlet />
      </main>
    </div>
  )
}
