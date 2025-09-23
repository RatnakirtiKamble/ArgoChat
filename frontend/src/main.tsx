/**
 * Client bootstrap.
 *
 * Creates the React root and wires up `BrowserRouter` with the `App`.
 */
import { BrowserRouter } from 'react-router-dom';
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
)
