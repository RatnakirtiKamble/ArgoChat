import React, { useState, useEffect, useRef, type FormEvent } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet-draw';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import HeatmapLayer from './HeatmapLayer.tsx';

// Fix marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface Bounds {
  topLeft: { lat: number; lng: number };
  bottomRight: { lat: number; lng: number };
}

interface Message {
  sender: 'user' | 'bot' | 'system';
  text: string;
}

interface DrawControlProps {
  onAreaSelect: (bounds: Bounds | null) => void;
}

const DrawControl: React.FC<DrawControlProps> = ({ onAreaSelect }) => {
  const map = useMap();
  const drawnItemsRef = useRef<L.FeatureGroup>(new L.FeatureGroup());

  useEffect(() => {
    const drawnItems = drawnItemsRef.current;
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
      edit: { featureGroup: drawnItems, remove: true },
      draw: {
        rectangle: {
          shapeOptions: { color: '#007bff', weight: 3, fillColor: '#007bff', fillOpacity: 0.25 },
          repeatMode: true,
          showArea: false,
        },
        polygon: false,
        circle: false,
        circlemarker: false,
        marker: false,
        polyline: false,
      },
    });

    map.addControl(drawControl);

    const handleCreated = (e: any) => {
        if (e.layerType === 'rectangle') {
          const bounds = e.layer.getBounds();
          drawnItemsRef.current?.clearLayers();
          drawnItemsRef.current?.addLayer(e.layer);
          const sw = bounds.getSouthWest();
          const ne = bounds.getNorthEast();
          const topLeft = { lat: ne.lat, lng: sw.lng };
          const bottomRight = { lat: sw.lat, lng: ne.lng };
          onAreaSelect({ topLeft, bottomRight });
        }
      };
      
      const handleEdited = (e: any) => {
        e.layers.eachLayer((layer: any) => {
          const bounds = layer.getBounds();
          const sw = bounds.getSouthWest();
          const ne = bounds.getNorthEast();
          const topLeft = { lat: ne.lat, lng: sw.lng };
          const bottomRight = { lat: sw.lat, lng: ne.lng };
          onAreaSelect({ topLeft, bottomRight });
        });
      };
      

    const handleDeleted = () => onAreaSelect(null);

    map.on(L.Draw.Event.CREATED, handleCreated);
    map.on(L.Draw.Event.EDITED, handleEdited);
    map.on(L.Draw.Event.DELETED, handleDeleted);

    return () => {
      map.off(L.Draw.Event.CREATED, handleCreated);
      map.off(L.Draw.Event.EDITED, handleEdited);
      map.off(L.Draw.Event.DELETED, handleDeleted);
      if (map && map.removeControl) map.removeControl(drawControl);
    };
  }, [map, onAreaSelect]);

  return null;
};

const App: React.FC = () => {
  const [selectedBounds, setSelectedBounds] = useState<Bounds | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'bot', text: "Hello! Click the layers icon to toggle heatmaps, then select an area to begin." },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const [heatmapMode, setHeatmapMode] = useState<string | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const handleSetMode = (mode: string) => setHeatmapMode(mode);
  const handleClear = () => { setHeatmapMode(null); setIsPanelOpen(false); };

  const formatBounds = (bounds: Bounds | null) => {
    if (!bounds) return "No region selected";
    const { topLeft, bottomRight } = bounds;
    return `TopLeft:(${topLeft.lat.toFixed(4)}, ${topLeft.lng.toFixed(4)}), BottomRight:(${bottomRight.lat.toFixed(4)}, ${bottomRight.lng.toFixed(4)})`;
  };

  const handleAreaSelect = (bounds: Bounds | null) => {
    setSelectedBounds(bounds);
    setMessages(prev => [
      ...prev,
      { sender: 'system', text: bounds ? `New region selected. ${formatBounds(bounds)}` : 'Region selection cleared.' }
    ]);
  };

  const scrollToBottom = () => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage: Message = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1200));
    const botMessage: Message = {
      sender: 'bot',
      text: selectedBounds
        ? `For the region ${formatBounds(selectedBounds)}, the current mock salinity is 35 PSU and temperature is 28°C.`
        : "Please select a region on the map first to get data about water conditions.",
    };
    setMessages(prev => [...prev, botMessage]);
    setIsLoading(false);
  };

  const handleUseCoords = () => {
    if (!selectedBounds) {
      setMessages(prev => [...prev, { sender: 'system', text: "Please select a region on the map first." }]);
      return;
    }
    setInput(`In the region ${formatBounds(selectedBounds)}, what is the ` + input);
  };

  return (
    <div className="flex flex-col md:flex-row h-screen bg-white shadow-lg font-sans">
      <div className="md:w-3/5 h-full w-full relative">
        <MapContainer
          center={[20.5937, 78.9629]}
          zoom={5}
          minZoom={0}
          maxZoom={5}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap contributors' />
          <DrawControl onAreaSelect={handleAreaSelect} />
          <HeatmapLayer mode={heatmapMode} />
        </MapContainer>
        {/* Heatmap toggle panel */}
        <div className="absolute top-3 right-3 z-[1000] flex flex-col items-end">
          <button
            onClick={() => setIsPanelOpen(!isPanelOpen)}
            className="bg-white p-2 rounded-lg shadow-xl border border-gray-200 hover:bg-gray-100 transition-colors"
            aria-label="Toggle heatmap layers"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2H5a2 2 0 00-2 2v2m14 0H5" />
            </svg>
          </button>
          {isPanelOpen && (
            <div className="mt-2 bg-white p-2 rounded-lg shadow-xl flex flex-col space-y-2 border border-gray-200 w-40">
              {['temperature', 'salinity', 'pressure', 'fish_prediction'].map((mode) => (
                <button
                  key={mode}
                  onClick={() => handleSetMode(mode)}
                  className={`text-sm text-left px-3 py-2 rounded-md font-semibold transition-colors w-full ${
                    heatmapMode === mode
                      ? mode === 'temperature'
                        ? 'bg-red-500 text-white'
                        : mode === 'salinity'
                        ? 'bg-green-500 text-white'
                        : mode === 'pressure'
                        ? 'bg-blue-500 text-white'
                        : 'bg-yellow-500 text-white'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                  }`}
                >
                  {mode === 'fish_prediction' ? 'Fish Prediction 🐟' : mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
              {heatmapMode && <button onClick={handleClear} className="text-sm text-center text-gray-500 hover:text-red-600 pt-1 font-medium">Clear</button>}
            </div>
          )}
        </div>
      </div>

      {/* Chat panel */}
      <div className="md:w-2/5 w-full h-full flex flex-col border-l border-gray-200">
        <header className="p-4 border-b border-gray-200 bg-gray-50">
          <h1 className="text-xl font-bold text-blue-800">SamudraVaani</h1>
          <p className="text-sm text-gray-700">Ocean Data Assistant</p>
        </header>
        <div className="flex-1 p-4 overflow-y-auto custom-scrollbar bg-gray-100">
          {messages.map((msg, i) => (
            <div key={i} className={`flex my-2 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.sender === 'system' ? (
                <div className="text-center w-full my-2">
                  <span className="text-xs text-gray-500 bg-gray-200 rounded-full px-3 py-1">{msg.text}</span>
                </div>
              ) : (
                <div className={`rounded-xl p-3 max-w-xs lg:max-w-md shadow-sm ${msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800'}`}>
                  <p className="text-sm">{msg.text}</p>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-xl p-3 max-w-xs bg-white text-gray-800 shadow-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="mb-2">
            <button onClick={handleUseCoords} disabled={!selectedBounds} className="text-xs font-semibold text-blue-600 bg-blue-100 hover:bg-blue-200 rounded-full px-4 py-1.5 transition-colors disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed">
              Use Selected Coordinates
            </button>
            {selectedBounds && <span className="text-xs text-gray-500 ml-3 hidden sm:inline">{formatBounds(selectedBounds)}</span>}
          </div>
          <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 w-full px-4 py-2 text-sm bg-gray-100 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button type="submit" className="bg-blue-500 text-white p-2 rounded-full hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default App;
