"use client";

import { X, Building2, MapPin, Ruler, TrendingUp, AlertTriangle, ArrowRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAppStore } from "@/store/appStore";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface LotDetail {
  id: string;
  bbl: number;
  address: string | null;
  borough: string;
  block: number;
  lot: number;
  zoning_dist_1: string | null;
  special_district_1: string | null;
  lot_area_sf: number | null;
  bldg_area_sf: number | null;
  built_far: number | null;
  max_far: number | null;
  built_far_pct: number | null;
  unbuilt_sf: number | null;
  num_floors: number | null;
  year_built: number | null;
  owner_name: string | null;
  landmark_status: string | null;
  opportunity_score: number | null;
  distress_score: number | null;
}

interface LotDetailPanelProps {
  bbl: number;
}

export function LotDetailPanel({ bbl }: LotDetailPanelProps) {
  const setSelectedBbl = useAppStore((state) => state.setSelectedBbl);

  const { data: lot, isLoading, error } = useQuery<LotDetail>({
    queryKey: ["lot", bbl],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/lots/${bbl}`);
      if (!response.ok) throw new Error("Failed to fetch lot");
      return response.json();
    },
    enabled: !!bbl,
  });

  const boroughName = (code: string) => {
    const names: Record<string, string> = {
      MN: "Manhattan",
      BK: "Brooklyn",
      QN: "Queens",
      BX: "Bronx",
      SI: "Staten Island",
    };
    return names[code] || code;
  };

  const formatNumber = (num: number | null | undefined) => {
    if (num == null) return "N/A";
    return num.toLocaleString();
  };

  const getScoreColor = (score: number | null | undefined) => {
    if (score == null) return "text-gray-500";
    if (score >= 70) return "text-green-600";
    if (score >= 40) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (score: number | null | undefined) => {
    if (score == null) return "bg-gray-100";
    if (score >= 70) return "bg-green-100";
    if (score >= 40) return "bg-yellow-100";
    return "bg-red-100";
  };

  return (
    <div className="w-96 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Building2 className="w-5 h-5 text-gray-600" />
          <span className="font-semibold text-gray-900">Lot Details</span>
        </div>
        <button
          onClick={() => setSelectedBbl(null)}
          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
        >
          <X className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {isLoading && (
          <div className="p-4 space-y-4">
            <div className="skeleton h-6 w-3/4" />
            <div className="skeleton h-4 w-1/2" />
            <div className="skeleton h-24 w-full" />
            <div className="skeleton h-24 w-full" />
          </div>
        )}

        {error && (
          <div className="p-4 text-center text-red-600">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
            <p>Failed to load lot details</p>
          </div>
        )}

        {lot && (
          <div className="p-4 space-y-6">
            {/* Address & Location */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {lot.address || `BBL ${lot.bbl}`}
              </h3>
              <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                <MapPin className="w-4 h-4" />
                <span>
                  {boroughName(lot.borough)} Block {lot.block}, Lot {lot.lot}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">BBL: {lot.bbl}</p>
            </div>

            {/* Opportunity Score */}
            {lot.opportunity_score != null && (
              <div
                className={`p-4 rounded-lg ${getScoreBg(lot.opportunity_score)}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Opportunity Score
                  </span>
                  <span
                    className={`text-2xl font-bold ${getScoreColor(
                      lot.opportunity_score
                    )}`}
                  >
                    {lot.opportunity_score}
                  </span>
                </div>
                <div className="mt-2 h-2 bg-white/50 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      lot.opportunity_score >= 70
                        ? "bg-green-500"
                        : lot.opportunity_score >= 40
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                    style={{ width: `${lot.opportunity_score}%` }}
                  />
                </div>
              </div>
            )}

            {/* FAR Analysis */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                FAR Analysis
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Built FAR</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {lot.built_far?.toFixed(2) || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Max FAR</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {lot.max_far?.toFixed(2) || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Utilization</p>
                  <p
                    className={`text-lg font-semibold ${
                      (lot.built_far_pct ?? 0) < 50
                        ? "text-green-600"
                        : "text-gray-900"
                    }`}
                  >
                    {lot.built_far_pct?.toFixed(1) || "N/A"}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Unbuilt SF</p>
                  <p className="text-lg font-semibold text-primary-600">
                    {formatNumber(lot.unbuilt_sf)}
                  </p>
                </div>
              </div>
            </div>

            {/* Property Details */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <Ruler className="w-4 h-4" />
                Property Details
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Lot Area</span>
                  <span className="font-medium">
                    {formatNumber(lot.lot_area_sf)} SF
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Building Area</span>
                  <span className="font-medium">
                    {formatNumber(lot.bldg_area_sf)} SF
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Floors</span>
                  <span className="font-medium">{lot.num_floors || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Year Built</span>
                  <span className="font-medium">{lot.year_built || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Zoning</span>
                  <span className="font-medium">
                    {lot.zoning_dist_1 || "N/A"}
                  </span>
                </div>
                {lot.special_district_1 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Special District</span>
                    <span className="font-medium">{lot.special_district_1}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Owner</span>
                  <span className="font-medium truncate max-w-[180px]">
                    {lot.owner_name || "N/A"}
                  </span>
                </div>
              </div>
            </div>

            {/* Landmark Status */}
            {lot.landmark_status && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">
                      Landmark Protected
                    </p>
                    <p className="text-xs text-amber-600">
                      {lot.landmark_status}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* LL97 Distress */}
            {lot.distress_score != null && lot.distress_score > 0.5 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <div>
                    <p className="text-sm font-medium text-red-800">
                      LL97 Distress Signal
                    </p>
                    <p className="text-xs text-red-600">
                      Score: {(lot.distress_score * 100).toFixed(0)}% - Potential
                      acquisition opportunity
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      {lot && (
        <div className="p-4 border-t border-gray-200 space-y-2">
          <button className="w-full flex items-center justify-center gap-2 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
            Run TDR Analysis
            <ArrowRight className="w-4 h-4" />
          </button>
          <button className="w-full py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors">
            Add to Site List
          </button>
        </div>
      )}
    </div>
  );
}
