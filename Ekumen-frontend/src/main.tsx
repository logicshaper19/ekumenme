import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  // <React.StrictMode>  // Temporarily disabled to prevent double mounting during development
    <App />
  // </React.StrictMode>,
)
