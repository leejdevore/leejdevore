"use client";

import { MapView } from "@/components/map/MapView";
import { FilterPanel } from "@/components/panels/FilterPanel";
import { LotDetailPanel } from "@/components/panels/LotDetailPanel";
import { AIChat } from "@/components/chat/AIChat";
import { Header } from "@/components/layout/Header";
import { useAppStore } from "@/store/appStore";

export default function Home() {
  const selectedBbl = useAppStore((state) => state.selectedBbl);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <Header />

      <div className="flex-1 flex relative">
        {/* Left Panel - Filters */}
        <FilterPanel />

        {/* Map */}
        <div className="flex-1 relative">
          <MapView />
        </div>

        {/* Right Panel - Lot Details */}
        {selectedBbl && <LotDetailPanel bbl={selectedBbl} />}

        {/* AI Chat */}
        <AIChat />
      </div>
    </div>
  );
}
