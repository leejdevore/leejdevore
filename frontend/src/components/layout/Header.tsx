"use client";

import { MapPin, Menu, Search, Settings } from "lucide-react";
import { useAppStore } from "@/store/appStore";

export function Header() {
  const toggleFilterPanel = useAppStore((state) => state.toggleFilterPanel);

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 z-50">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleFilterPanel}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label="Toggle filters"
        >
          <Menu className="w-5 h-5 text-gray-600" />
        </button>

        <div className="flex items-center gap-2">
          <MapPin className="w-6 h-6 text-primary-600" />
          <span className="font-semibold text-lg text-gray-900">DevSight</span>
          <span className="text-sm text-gray-500 font-medium">NYC</span>
        </div>
      </div>

      <div className="flex-1 max-w-xl mx-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search address, BBL, or neighborhood..."
            className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label="Settings"
        >
          <Settings className="w-5 h-5 text-gray-600" />
        </button>

        <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-medium">
          U
        </div>
      </div>
    </header>
  );
}
