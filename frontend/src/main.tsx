import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import CommandShell from './pages/CommandShell'
import AgentBoard from './pages/AgentBoard'
import ModelBrowser from './pages/ModelBrowser'
import TokenCalculator from './pages/TokenCalculator'
import TumeloPage from './pages/TumeloPage'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<CommandShell />} />
          <Route path="agents" element={<AgentBoard />} />
          <Route path="models" element={<ModelBrowser />} />
          <Route path="tokens" element={<TokenCalculator />} />
        </Route>
        {/* Standalone tumeloramaphosa.com landing page */}
        <Route path="/tumelo" element={<TumeloPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
