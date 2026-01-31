"use client";

import { ChevronLeft, Filter, RotateCcw } from "lucide-react";
import { useAppStore } from "@/store/appStore";

const BOROUGHS = [
  { code: "MN", name: "Manhattan" },
  { code: "BK", name: "Brooklyn" },
  { code: "QN", name: "Queens" },
  { code: "BX", name: "Bronx" },
  { code: "SI", name: "Staten Island" },
];

const ZONING_CATEGORIES = [
  { prefix: "R", name: "Residential" },
  { prefix: "C", name: "Commercial" },
  { prefix: "M", name: "Manufacturing" },
];

export function FilterPanel() {
  const isOpen = useAppStore((state) => state.isFilterPanelOpen);
  const toggleFilterPanel = useAppStore((state) => state.toggleFilterPanel);
  const filters = useAppStore((state) => state.filters);
  const setFilters = useAppStore((state) => state.setFilters);
  const resetFilters = useAppStore((state) => state.resetFilters);

  if (!isOpen) {
    return null;
  }

  const handleBoroughToggle = (code: string) => {
    const current = filters.boroughs;
    const updated = current.includes(code)
      ? current.filter((b) => b !== code)
      : [...current, code];
    setFilters({ boroughs: updated });
  };

  const handleZoningToggle = (prefix: string) => {
    const current = filters.zoningDistricts;
    const updated = current.includes(prefix)
      ? current.filter((z) => z !== prefix)
      : [...current, prefix];
    setFilters({ zoningDistricts: updated });
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full panel-slide-in">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <span className="font-semibold text-gray-900">Filters</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={resetFilters}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
            title="Reset filters"
          >
            <RotateCcw className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={toggleFilterPanel}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
          >
            <ChevronLeft className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Filter Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
        {/* FAR Utilization */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Built FAR % (max)
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={filters.builtFarPctMax ?? 100}
            onChange={(e) =>
              setFilters({ builtFarPctMax: parseInt(e.target.value) })
            }
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0%</span>
            <span className="font-medium text-gray-700">
              {filters.builtFarPctMax ?? 100}%
            </span>
            <span>100%</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Find underbuilt lots with development potential
          </p>
        </div>

        {/* Minimum Unbuilt SF */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Unbuilt SF
          </label>
          <input
            type="number"
            placeholder="e.g., 10000"
            value={filters.minUnbuiltSf ?? ""}
            onChange={(e) =>
              setFilters({
                minUnbuiltSf: e.target.value ? parseInt(e.target.value) : null,
              })
            }
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Filter by minimum development potential
          </p>
        </div>

        {/* Borough Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Borough
          </label>
          <div className="flex flex-wrap gap-2">
            {BOROUGHS.map((borough) => (
              <button
                key={borough.code}
                onClick={() => handleBoroughToggle(borough.code)}
                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                  filters.boroughs.includes(borough.code)
                    ? "bg-primary-100 text-primary-700 border border-primary-300"
                    : "bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200"
                }`}
              >
                {borough.name}
              </button>
            ))}
          </div>
        </div>

        {/* Zoning Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Zoning Category
          </label>
          <div className="flex flex-wrap gap-2">
            {ZONING_CATEGORIES.map((zone) => (
              <button
                key={zone.prefix}
                onClick={() => handleZoningToggle(zone.prefix)}
                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                  filters.zoningDistricts.includes(zone.prefix)
                    ? "bg-primary-100 text-primary-700 border border-primary-300"
                    : "bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200"
                }`}
              >
                {zone.name}
              </button>
            ))}
          </div>
        </div>

        {/* Lot Area Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Lot Area (SF)
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.minLotArea ?? ""}
              onChange={(e) =>
                setFilters({
                  minLotArea: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <span className="text-gray-400 self-center">-</span>
            <input
              type="number"
              placeholder="Max"
              value={filters.maxLotArea ?? ""}
              onChange={(e) =>
                setFilters({
                  maxLotArea: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Exclude Landmarks */}
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-medium text-gray-700">
              Exclude Landmarks
            </label>
            <p className="text-xs text-gray-500">
              Hide protected landmark sites
            </p>
          </div>
          <button
            onClick={() =>
              setFilters({ excludeLandmarks: !filters.excludeLandmarks })
            }
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              filters.excludeLandmarks ? "bg-primary-600" : "bg-gray-200"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                filters.excludeLandmarks ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <button
          onClick={() => {
            // This would trigger a refetch with current filters
            console.log("Applying filters:", filters);
          }}
          className="w-full py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
        >
          Apply Filters
        </button>
      </div>
    </div>
  );
}
