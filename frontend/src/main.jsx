import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import App from './App.jsx'
import ChatPage from './pages/ChatPage.jsx'
import TicketDetailPage from './pages/TicketDetailPage.jsx'
import TicketsPage from './pages/TicketsPage.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          <Route index element={<ChatPage />} />
          <Route path="tickets" element={<TicketsPage />} />
          <Route path="tickets/:ticketId" element={<TicketDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
