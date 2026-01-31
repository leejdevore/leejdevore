"use client";

import { useCallback, useRef, useEffect, useState } from "react";
import Map, { NavigationControl, Source, Layer, MapRef } from "react-map-gl/maplibre";
import type { MapLayerMouseEvent } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useAppStore } from "@/store/appStore";

const TILES_URL = process.env.NEXT_PUBLIC_TILES_URL || "http://localhost:3001";

// MapLibre style with OpenStreetMap base and vector tiles from Martin
const mapStyle = {
  version: 8 as const,
  name: "DevSight",
  sources: {
    osm: {
      type: "raster" as const,
      tiles: [
        "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [
    {
      id: "osm-tiles",
      type: "raster" as const,
      source: "osm",
      minzoom: 0,
      maxzoom: 22,
    },
  ],
};

// Lot fill layer - colored by opportunity score
const lotsFillLayer = {
  id: "lots-fill",
  type: "fill" as const,
  source: "lots",
  "source-layer": "lots_enriched",
  paint: {
    "fill-color": [
      "case",
      // High opportunity (green)
      [">=", ["coalesce", ["get", "opportunity_score"], 0], 70],
      "#22c55e",
      // Medium opportunity (yellow)
      [">=", ["coalesce", ["get", "opportunity_score"], 0], 40],
      "#f59e0b",
      // Low opportunity (red/orange)
      [">=", ["coalesce", ["get", "opportunity_score"], 0], 1],
      "#ef4444",
      // Default (gray for no score)
      "#9ca3af",
    ],
    "fill-opacity": [
      "case",
      ["boolean", ["feature-state", "hover"], false],
      0.8,
      0.5,
    ],
  },
};

// Lot outline layer
const lotsOutlineLayer = {
  id: "lots-outline",
  type: "line" as const,
  source: "lots",
  "source-layer": "lots_enriched",
  paint: {
    "line-color": [
      "case",
      ["boolean", ["feature-state", "selected"], false],
      "#0ea5e9",
      "#374151",
    ],
    "line-width": [
      "case",
      ["boolean", ["feature-state", "selected"], false],
      3,
      ["boolean", ["feature-state", "hover"], false],
      2,
      1,
    ],
  },
};

export function MapView() {
  const mapRef = useRef<MapRef>(null);
  const [isMapLoaded, setIsMapLoaded] = useState(false);

  const viewport = useAppStore((state) => state.viewport);
  const setViewport = useAppStore((state) => state.setViewport);
  const selectedBbl = useAppStore((state) => state.selectedBbl);
  const setSelectedBbl = useAppStore((state) => state.setSelectedBbl);
  const hoveredBbl = useAppStore((state) => state.hoveredBbl);
  const setHoveredBbl = useAppStore((state) => state.setHoveredBbl);

  // Handle viewport changes
  const onMove = useCallback(
    (evt: { viewState: { longitude: number; latitude: number; zoom: number; bearing: number; pitch: number } }) => {
      setViewport({
        center: [evt.viewState.longitude, evt.viewState.latitude],
        zoom: evt.viewState.zoom,
        bearing: evt.viewState.bearing,
        pitch: evt.viewState.pitch,
      });
    },
    [setViewport]
  );

  // Handle lot click
  const onClick = useCallback(
    (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature && feature.properties?.bbl) {
        setSelectedBbl(feature.properties.bbl);
      } else {
        setSelectedBbl(null);
      }
    },
    [setSelectedBbl]
  );

  // Handle lot hover
  const onMouseMove = useCallback(
    (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature && feature.properties?.bbl) {
        setHoveredBbl(feature.properties.bbl);
        if (mapRef.current) {
          mapRef.current.getCanvas().style.cursor = "pointer";
        }
      } else {
        setHoveredBbl(null);
        if (mapRef.current) {
          mapRef.current.getCanvas().style.cursor = "";
        }
      }
    },
    [setHoveredBbl]
  );

  const onMouseLeave = useCallback(() => {
    setHoveredBbl(null);
    if (mapRef.current) {
      mapRef.current.getCanvas().style.cursor = "";
    }
  }, [setHoveredBbl]);

  const onLoad = useCallback(() => {
    setIsMapLoaded(true);
  }, []);

  // Update feature states for hover/selection
  useEffect(() => {
    if (!isMapLoaded) return;
    const map = mapRef.current?.getMap();
    if (!map) return;

    // Clear previous states
    try {
      map.removeFeatureState({ source: "lots", sourceLayer: "lots_enriched" });
    } catch {
      // Source may not exist yet
    }

    // Set hover state
    if (hoveredBbl) {
      try {
        map.setFeatureState(
          { source: "lots", sourceLayer: "lots_enriched", id: hoveredBbl },
          { hover: true }
        );
      } catch {
        // Ignore if source doesn't exist
      }
    }

    // Set selected state
    if (selectedBbl) {
      try {
        map.setFeatureState(
          { source: "lots", sourceLayer: "lots_enriched", id: selectedBbl },
          { selected: true }
        );
      } catch {
        // Ignore if source doesn't exist
      }
    }
  }, [hoveredBbl, selectedBbl, isMapLoaded]);

  return (
    <Map
      ref={mapRef}
      mapStyle={mapStyle}
      longitude={viewport.center[0]}
      latitude={viewport.center[1]}
      zoom={viewport.zoom}
      bearing={viewport.bearing}
      pitch={viewport.pitch}
      onMove={onMove}
      onClick={onClick}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      onLoad={onLoad}
      interactiveLayerIds={["lots-fill"]}
      style={{ width: "100%", height: "100%" }}
    >
      <NavigationControl position="top-right" />

      {/* Lot tiles from Martin vector tile server */}
      <Source
        id="lots"
        type="vector"
        tiles={[`${TILES_URL}/lots_enriched/{z}/{x}/{y}.pbf`]}
        minzoom={10}
        maxzoom={22}
      >
        <Layer {...lotsFillLayer} />
        <Layer {...lotsOutlineLayer} />
      </Source>
    </Map>
  );
}
