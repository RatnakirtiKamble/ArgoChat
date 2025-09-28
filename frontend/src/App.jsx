// new changes rename of the file
import React, { useState } from 'react';
import LandingPage from './pages/LandingPage.jsx';
import ChatMap from './ChatMap.jsx';

export default function App() {
  const [showChatMap, setShowChatMap] = useState(false);

  // This function, when called, will hide the chat/map and show the front page.
  const handleGoHome = () => {
    setShowChatMap(false);
  };

  if (!showChatMap) {
    // This part shows the landing page.
    return <LandingPage onLaunch={() => setShowChatMap(true)} />;
  }

  // This part shows the main app and gives it the ability to go home.
  return <ChatMap onGoHome={handleGoHome} />;
}