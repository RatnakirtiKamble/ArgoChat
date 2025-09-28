import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

const HeatmapLayer = ({ mode }) => {
  const map = useMap();
  const layerRef = useRef(null);

  useEffect(() => {
    if (mode) {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }

      const tileUrl = `/tiles/${mode}/{z}/{x}/{y}.png`;

      const newLayer = L.tileLayer(tileUrl, {
        maxZoom: 5, // <-- FIX: Correctly set to your max tile level
        minZoom: 0,
        opacity: 0.7,
        attribution: `Ocean ${mode.charAt(0).toUpperCase() + mode.slice(1)} Data`,
        zIndex: 10 
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