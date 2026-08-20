import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

import { StartupError } from './components/ui/StartupError'

const root = document.getElementById('root')

if (!root) {
  throw new Error('Root element #root not found')
}

const requiredEnvVars = [
  { key: 'VITE_EXECUTOR_URL', value: import.meta.env.VITE_EXECUTOR_URL },
  { key: 'VITE_USERNAME', value: import.meta.env.VITE_USERNAME },
]

const missingVar = requiredEnvVars.find(v => !v.value)

if (missingVar) {
  createRoot(root).render(
    <StrictMode>
      <StartupError message={`Missing required environment variable: ${missingVar.key}. Please configure it in your environment settings.`} />
    </StrictMode>
  )
} else {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>
  )
}
