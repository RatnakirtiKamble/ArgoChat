import React, { useState, useEffect } from 'react';

const texts = [
  'Samudra',          // English
  'समुद्र',           // Sanskrit
  'சமுத்ரா',         // Tamil
  'সমুদ্র',           // Bengali
];

const Typewriter: React.FC = () => {
  const [textIndex, setTextIndex] = useState(0);
  const [displayText, setDisplayText] = useState('');
  const [typing, setTyping] = useState(true); // true = typing, false = deleting

  useEffect(() => {
    const currentText = texts[textIndex];
    let timeout: ReturnType<typeof setTimeout>;

    if (typing) {
      if (displayText.length < currentText.length) {
        timeout = setTimeout(() => {
          setDisplayText(currentText.slice(0, displayText.length + 1));
        }, 150);
      } else {
        timeout = setTimeout(() => setTyping(false), 1000); 
      }
    } else {
      if (displayText.length > 0) {
        timeout = setTimeout(() => {
          setDisplayText(displayText.slice(0, -1));
        }, 100);
      } else {
        setTyping(true);
        setTextIndex((prev) => (prev + 1) % texts.length);
      }
    }

    return () => clearTimeout(timeout);
  }, [displayText, typing, textIndex]);

  return (
    <span>
      {displayText}
      <span className="blinking-cursor">|</span>
      <style>{`
        .blinking-cursor {
          display: inline-block;
          width: 1ch;
          animation: blink 0.7s infinite;
        }
        @keyframes blink {
          0%, 50%, 100% { opacity: 1; }
          25%, 75% { opacity: 0; }
        }
      `}</style>
    </span>
  );
};

export default Typewriter;
