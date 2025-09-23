/**
 * Chat landing page with optional region selection via Leaflet map.
 *
 * - Lets users send a natural language prompt to the backend `/api/query`.
 * - Optionally captures a rectangular region to append lat/lon bounds to
 *   the prompt for geo-filtered queries.
 * - Renders a simple chat transcript and a modal map for selection.
 */
import { useState, useRef } from "react";
import axios from "axios";
import { MapContainer, TileLayer, FeatureGroup } from "react-leaflet";
import { EditControl } from "react-leaflet-draw";
import { type LeafletEvent, FeatureGroup as LeafletFeatureGroup } from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";

type Region = {
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
};

type Message = {
  type: "user" | "bot";
  text: string;
  isLocation?: boolean;
};

export default function LandingPage() {
  const [showMap, setShowMap] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { type: "bot", text: "Hello! Ask me about Argo ocean data." },
  ]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);

  const featureGroupRef = useRef<LeafletFeatureGroup>(null);

  // Handle new region selection
  const handleCreated = (e: LeafletEvent & { layer: any }) => {
    if (featureGroupRef.current) featureGroupRef.current.clearLayers();
    if (featureGroupRef.current) featureGroupRef.current.addLayer(e.layer);

    const layer = e.layer;
    if (!layer.getBounds) return;

    const bounds = layer.getBounds();
    const region: Region = {
      lat_min: bounds.getSouthWest().lat,
      lat_max: bounds.getNorthEast().lat,
      lon_min: bounds.getSouthWest().lng,
      lon_max: bounds.getNorthEast().lng,
    };

    setSelectedRegion(region);

    setMessages((prev) => [
      ...prev,
      { type: "bot", text: `Region selected. You can now close the map.` },
    ]);
  };

  // Send user prompt
  const handleSend = async () => {
    if (!inputText.trim() && !selectedRegion) return;

    const displayText = selectedRegion ? "Location" : inputText;
    setMessages((prev) => [...prev, { type: "user", text: displayText, isLocation: !!selectedRegion }]);

    let backendPrompt = inputText;
    if (selectedRegion) {
      backendPrompt += `\nCoordinates: lat_min=${selectedRegion.lat_min}, lat_max=${selectedRegion.lat_max}, lon_min=${selectedRegion.lon_min}, lon_max=${selectedRegion.lon_max}`;
    }

    setInputText("");
    setSelectedRegion(null);
    setLoading(true);

    try {
      const payload = { user_prompt: backendPrompt };
      const response = await axios.post("http://127.0.0.1:8000/api/query", payload);
      const botText = response.data?.answer || response.data?.message || "No response.";

      setMessages((prev) => [...prev, { type: "bot", text: botText }]);
    } catch (error: any) {
      console.error(error);
      setMessages((prev) => [...prev, { type: "bot", text: "Error fetching response from backend." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#1e1e2f", color: "#fff", fontFamily: "Arial, sans-serif" }}>
      {/* Chat messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ textAlign: msg.type === "user" ? "right" : "left", marginBottom: "8px" }}>
            <span style={{ display: "inline-block", padding: "8px 12px", borderRadius: "12px", background: msg.type === "user" ? "#4ade80" : "#3b3b5c", color: msg.type === "user" ? "#000" : "#fff" }}>
              {msg.text}
            </span>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: "left", marginBottom: "8px" }}>
            <span style={{ display: "inline-block", padding: "8px 12px", borderRadius: "12px", background: "#3b3b5c" }}>
              Thinking...
            </span>
          </div>
        )}
      </div>

      {/* Input bar */}
      <div style={{ padding: "12px", borderTop: "1px solid #444", display: "flex", gap: "8px" }}>
        <button
          onClick={() => setShowMap(true)}
          style={{ padding: "8px 12px", background: "#3b82f6", color: "#fff", border: "none", borderRadius: "8px", cursor: "pointer" }}
        >
          Add Location
        </button>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          style={{ flex: 1, padding: "8px 12px", borderRadius: "8px", border: "1px solid #444", background: "#2a2a3b", color: "#fff" }}
          placeholder="Type your message..."
        />
        <button
          onClick={handleSend}
          style={{ padding: "8px 12px", background: "#10b981", color: "#fff", border: "none", borderRadius: "8px", cursor: "pointer" }}
        >
          Send
        </button>
      </div>

      {/* Map modal */}
      {showMap && (
        <div
          // FIX: Removed the onMouseDown handler from this overlay to prevent it from interfering with map clicks.
          style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.7)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000 }}
        >
          <div style={{ width: "80%", height: "70%", background: "#2a2a3b", borderRadius: "12px", overflow: "hidden", position: "relative" }}>
            <button
              // FIX: Simplified to a standard onClick handler.
              onClick={() => setShowMap(false)}
              style={{ position: "absolute", top: "8px", right: "8px", zIndex: 2000, background: "#ef4444", color: "#fff", border: "none", borderRadius: "6px", padding: "4px 8px", cursor: "pointer" }}
            >
              Close
            </button>
            {/* The stopPropagation here is still good practice to prevent any other potential bubbling. */}
            <div style={{ width: "100%", height: "100%" }} onMouseDown={(e) => e.stopPropagation()}>
              <MapContainer center={[15, 80]} zoom={4} style={{ width: "100%", height: "100%" }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <FeatureGroup ref={featureGroupRef}>
                  <EditControl
                    position="topleft"
                    onCreated={handleCreated}
                    draw={{ rectangle: true, polyline: false, polygon: false, circle: false, marker: false, circlemarker: false }}
                    edit={{ featureGroup: featureGroupRef.current!, remove: true }}
                  />
                </FeatureGroup>
              </MapContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}