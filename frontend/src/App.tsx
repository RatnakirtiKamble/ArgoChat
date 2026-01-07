import { Route, Routes } from 'react-router-dom'
import LandingPage from './pages/LandingPage';
import ChatMap from './pages/ChatMap';

function App() {
  return (
      <Routes>

        <Route path="/" element={<LandingPage />} />

        <Route path="/chat" element={<ChatMap />} />
      </Routes>

  )
}

export default App;
