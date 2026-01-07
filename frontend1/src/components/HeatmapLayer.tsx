import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L, { TileLayer } from "leaflet";

interface HeatmapLayerProps {
  mode: string | null;
}

const HeatmapLayer: React.FC<HeatmapLayerProps> = ({ mode }) => {
  const map = useMap();
  const layerRef = useRef<TileLayer | null>(null);

  useEffect(() => {
    if (mode) {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }

      const tileUrl = `/tiles/${mode}/{z}/{x}/{y}.png`;

      const newLayer = L.tileLayer(tileUrl, {
        maxZoom: 5, // Adjust based on your tiles
        minZoom: 0,
        opacity: 0.7,
        attribution: `Ocean ${mode.charAt(0).toUpperCase() + mode.slice(1)} Data`,
        zIndex: 10,
      });

      newLayer.addTo(map);
      layerRef.current = newLayer;
    } else {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    }

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
    };
  }, [mode, map]);

  return null;
};

export default HeatmapLayer;
