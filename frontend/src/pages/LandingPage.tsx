import React from 'react';
import { useNavigate } from 'react-router-dom';
import Typewriter from '../components/Typewriter';

interface FeatureIconProps {
  path: string;
}

const FeatureIcon: React.FC<FeatureIconProps> = ({ path }) => (
  <div className="bg-blue-100 p-3 rounded-full mb-4">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      className="h-8 w-8 text-blue-600"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d={path} />
    </svg>
  </div>
);


const LandingPage: React.FC = () => {

  const navigate = useNavigate();
  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 via-white to-cyan-50 text-slate-800 font-sans flex flex-col items-center justify-center p-4">
      <main className="z-10 text-center max-w-4xl mx-auto">
        <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-cyan-500 pb-2">
          <Typewriter />Vaani
        </h1>

        <p className="mt-4 text-lg md:text-xl text-slate-600 max-w-2xl mx-auto">
          Your conversational gateway to ocean data. Select regions on an
          interactive map and get instant insights on temperature, salinity, and
          more.
        </p>

        <button
          onClick={() => {navigate('/chat');}}
          className="mt-10 px-8 py-4 bg-blue-600 text-white font-semibold text-lg rounded-full shadow-lg hover:bg-blue-700 transform hover:scale-105 transition-all duration-300 ease-in-out"
        >
          Launch Conversation Interface with Interactive Map
        </button>

        {/* Features Section */}
        <div className="mt-20 grid md:grid-cols-3 gap-8 text-left">
          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-xl shadow-md border">
            <FeatureIcon path="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13V7m0 13a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2h2m11-3l-5.447 2.724A1 1 0 0115 5.618v10.764a1 1 0 01-1.447.894L9 14m11-3V7m4 4h-4" />
            <h3 className="font-bold text-xl mb-2">Interactive Map</h3>
            <p className="text-slate-600">
              Select any oceanic region with precision drawing tools to define
              your area of interest.
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-xl shadow-md border">
            <FeatureIcon path="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            <h3 className="font-bold text-xl mb-2">Conversational AI</h3>
            <p className="text-slate-600">
              Ask questions in natural language and receive immediate,
              data-driven answers from the backend.
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-xl shadow-md border">
            <FeatureIcon path="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2H5a2 2 0 00-2 2v2m14 0H5" />
            <h3 className="font-bold text-xl mb-2">Data Overlays</h3>
            <p className="text-slate-600">
              Visualize complex data with intuitive heatmap layers for
              temperature, salinity, and fish prediction.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
