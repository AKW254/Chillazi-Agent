import { StrictMode, createElement } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'


const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element #root was not found.')
}

createRoot(rootElement).render(createElement(StrictMode, null, createElement(App)))
