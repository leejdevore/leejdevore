import { create } from "zustand";

interface FilterState {
  builtFarPctMax: number | null;
  minUnbuiltSf: number | null;
  zoningDistricts: string[];
  boroughs: string[];
  minLotArea: number | null;
  maxLotArea: number | null;
  excludeLandmarks: boolean;
}

interface ViewportState {
  center: [number, number];
  zoom: number;
  bearing: number;
  pitch: number;
}

interface AppState {
  // Filters
  filters: FilterState;
  setFilters: (filters: Partial<FilterState>) => void;
  resetFilters: () => void;

  // Viewport
  viewport: ViewportState;
  setViewport: (viewport: Partial<ViewportState>) => void;

  // Selection
  selectedBbl: number | null;
  setSelectedBbl: (bbl: number | null) => void;
  hoveredBbl: number | null;
  setHoveredBbl: (bbl: number | null) => void;

  // Panels
  isFilterPanelOpen: boolean;
  toggleFilterPanel: () => void;
  isChatOpen: boolean;
  toggleChat: () => void;

  // Site lists
  siteLists: { name: string; bbls: number[] }[];
  addToSiteList: (listName: string, bbl: number) => void;
  removeFromSiteList: (listName: string, bbl: number) => void;
  createSiteList: (name: string) => void;
}

const defaultFilters: FilterState = {
  builtFarPctMax: null,
  minUnbuiltSf: null,
  zoningDistricts: [],
  boroughs: [],
  minLotArea: null,
  maxLotArea: null,
  excludeLandmarks: true,
};

const defaultViewport: ViewportState = {
  center: [-73.985, 40.748], // NYC center
  zoom: 12,
  bearing: 0,
  pitch: 0,
};

export const useAppStore = create<AppState>((set) => ({
  // Filters
  filters: defaultFilters,
  setFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    })),
  resetFilters: () => set({ filters: defaultFilters }),

  // Viewport
  viewport: defaultViewport,
  setViewport: (newViewport) =>
    set((state) => ({
      viewport: { ...state.viewport, ...newViewport },
    })),

  // Selection
  selectedBbl: null,
  setSelectedBbl: (bbl) => set({ selectedBbl: bbl }),
  hoveredBbl: null,
  setHoveredBbl: (bbl) => set({ hoveredBbl: bbl }),

  // Panels
  isFilterPanelOpen: true,
  toggleFilterPanel: () =>
    set((state) => ({ isFilterPanelOpen: !state.isFilterPanelOpen })),
  isChatOpen: false,
  toggleChat: () => set((state) => ({ isChatOpen: !state.isChatOpen })),

  // Site lists
  siteLists: [],
  addToSiteList: (listName, bbl) =>
    set((state) => ({
      siteLists: state.siteLists.map((list) =>
        list.name === listName && !list.bbls.includes(bbl)
          ? { ...list, bbls: [...list.bbls, bbl] }
          : list
      ),
    })),
  removeFromSiteList: (listName, bbl) =>
    set((state) => ({
      siteLists: state.siteLists.map((list) =>
        list.name === listName
          ? { ...list, bbls: list.bbls.filter((b) => b !== bbl) }
          : list
      ),
    })),
  createSiteList: (name) =>
    set((state) => ({
      siteLists: [...state.siteLists, { name, bbls: [] }],
    })),
}));
