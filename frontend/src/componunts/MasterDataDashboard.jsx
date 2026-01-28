import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../utils/Api"; 
import {
  MapPinIcon,
  TagIcon,
  CheckBadgeIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ServerStackIcon,
  QueueListIcon,
  CheckCircleIcon,
  XCircleIcon,
  GlobeAltIcon,
  ArrowPathIcon 
} from "@heroicons/react/24/solid";

const MasterDataDashboard = () => {
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get("task_id");

  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState("LOADING"); // LOADING, PROCESSING, COMPLETED, FAILED
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!taskId) {
      setError("No Task ID found. Please upload a file.");
      setStatus("FAILED");
      return;
    }

    let isMounted = true;
    let pollTimer = null;

    const fetchReport = async () => {
      try {
        const res = await api.get(`/upload/report/${taskId}`);
        
        if (!isMounted) return;

        const reportStatus = res.data.status;
        setStatus(reportStatus);

        // Parse Stats if available
        if (res.data.stats) {
            const parsedStats = typeof res.data.stats === 'string' 
              ? JSON.parse(res.data.stats) 
              : res.data.stats;
            setStats(parsedStats);
        }

        // --- AUTO-POLL LOGIC ---
        // If the worker is still running, check again in 2 seconds
        if (reportStatus === "PROCESSING" || reportStatus === "PENDING") {
            pollTimer = setTimeout(fetchReport, 2000);
        } 

      } catch (err) {
        console.error("Fetch error:", err);
        if (isMounted) setError("Failed to connect to backend.");
      }
    };

    fetchReport();

    // Cleanup to prevent memory leaks if user leaves page
    return () => {
        isMounted = false;
        if (pollTimer) clearTimeout(pollTimer);
    };
  }, [taskId]);

  // --- LOADER STATE (If Processing) ---
  if (status === "LOADING" || status === "PROCESSING" || status === "PENDING") {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 flex-col">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mb-6"></div>
        <h2 className="text-2xl font-bold text-gray-700 animate-pulse">Processing Master Data...</h2>
        <p className="text-gray-500 mt-2">Please wait, this updates automatically.</p>
        <p className="text-xs text-gray-400 mt-4 font-mono">Task ID: {taskId}</p>
      </div>
    );
  }

  if (!taskId) {
      return (
        <div className="p-10 text-center">
            <h3 className="text-xl font-bold text-gray-700 mb-2">No Report Selected</h3>
            <p className="text-gray-500">Please upload a file to generate a dashboard report.</p>
        </div>
      );
  }

  // DEFAULT DATA STRUCTURE 
  const data = stats || {
    total_listings: 0,
    total_products: 0,
    listing_status: { complete: 0, incomplete: 0 },
    scrape_status: { pending_city: 0, pending_city_category: 0 },
    source_stats: [], 
    city_counts: [], 
    category_counts: [], 
    
    total_cities: 0,
    total_areas: 0,
    total_categories: 0,
    city_match_status: { matched: 0, unmatched: 0 },
    missing_values: { missing_phone: 0, missing_email: 0, missing_address: 0 },
    top_city_categories: [] 
  };

  const displayField = (value) => {
    if (error && !stats) return "-";
    return (value !== undefined && value !== null) ? value.toLocaleString() : "0";
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      
      {/* 1. HERO SECTION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-2xl shadow-sm p-8 text-center relative overflow-hidden border border-gray-100 transition hover:shadow-md">
           <div className="absolute top-0 left-0 w-full h-1 bg-blue-500"></div>
           <div className="flex justify-center mb-4">
             <div className="p-3 rounded-full bg-blue-50"><ServerStackIcon className="w-8 h-8 text-blue-600" /></div>
           </div>
           <h1 className="text-4xl font-extrabold text-gray-800 mb-1">{displayField(data.total_records || data.total_listings)}</h1>
           <p className="text-gray-500 uppercase tracking-widest text-xs font-bold">Total Listing Data</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm p-8 text-center relative overflow-hidden border border-gray-100 transition hover:shadow-md">
           <div className="absolute top-0 left-0 w-full h-1 bg-purple-500"></div>
           <div className="flex justify-center mb-4">
             <div className="p-3 rounded-full bg-purple-50"><TagIcon className="w-8 h-8 text-purple-600" /></div>
           </div>
           <h1 className="text-4xl font-extrabold text-gray-800 mb-1">{displayField(data.total_categories)}</h1>
           <p className="text-gray-500 uppercase tracking-widest text-xs font-bold">Unique Categories</p>
        </div>
      </div>

      {/* 2. COMPLETENESS & SCRAPE QUEUE */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <MetricCard 
          title="Matched Cities" 
          value={displayField(data.city_match_status?.matched)} 
          icon={<CheckCircleIcon className="w-6 h-6 text-white" />} 
          color="bg-teal-500"
        />
        <MetricCard 
          title="Unmatched Cities" 
          value={displayField(data.city_match_status?.unmatched)} 
          icon={<XCircleIcon className="w-6 h-6 text-white" />} 
          color="bg-red-400"
        />
        <MetricCard 
          title="Total Cities" 
          value={displayField(data.total_cities)} 
          icon={<MapPinIcon className="w-6 h-6 text-white" />} 
          color="bg-amber-500"
        />
        <MetricCard 
          title="Total Areas" 
          value={displayField(data.total_areas)} 
          icon={<QueueListIcon className="w-6 h-6 text-white" />} 
          color="bg-amber-600"
        />
      </div>

      {/* 3. SOURCE WISE DATA */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-700">Source Wise Breakdown</h3>
          <GlobeAltIcon className="w-6 h-6 text-blue-400" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {(data.source_stats || []).map((source, idx) => (
             <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-xs font-bold text-gray-500 uppercase mb-1">{source.source || 'Unknown'}</p>
                <p className="text-xl font-bold text-gray-800">{source.count?.toLocaleString()}</p>
             </div>
          ))}
          {(data.source_stats || []).length === 0 && <p className="text-sm text-gray-400">No source data available.</p>}
        </div>
      </div>

      {/* 4. DETAILED DATA TABLES (3 COLUMNS) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <SimpleTableCard 
           title="Citywise Data Count" 
           icon={<MapPinIcon className="w-5 h-5 text-green-500"/>}
           data={data.city_counts || []} 
           col1="City"
           col2="Count"
        />

        <SimpleTableCard 
           title="Categorywise Data Count" 
           icon={<TagIcon className="w-5 h-5 text-purple-500"/>}
           data={data.category_counts || []}
           col1="Category"
           col2="Count"
        />

        {/* City + Category Data */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 h-96 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-700">City + Category</h3>
              <ChartBarIcon className="w-5 h-5 text-indigo-500" />
            </div>
            <div className="overflow-y-auto flex-1">
              <table className="w-full text-left">
                <thead className="bg-gray-50 sticky top-0">
                  <tr className="text-xs text-gray-500 uppercase">
                    <th className="py-2 px-2">City</th>
                    <th className="py-2 px-2">Cat</th>
                    <th className="py-2 px-2 text-right">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.top_city_categories || []).map((item, index) => {
                    const city = item.city;
                    if (item.category) {
                       return (
                        <tr key={index} className="border-b border-gray-100 last:border-none hover:bg-gray-50 transition">
                          <td className="py-2 px-2 text-sm text-gray-700">{city}</td>
                          <td className="py-2 px-2 text-xs font-bold text-indigo-600 uppercase">{item.category}</td>
                          <td className="py-2 px-2 text-sm font-bold text-right">{item.count}</td>
                        </tr>
                       );
                    }
                    if (item.categories) {
                        return Object.entries(item.categories).map(([cat, count], i) => (
                            <tr key={`${index}-${i}`} className="border-b border-gray-100 last:border-none hover:bg-gray-50 transition">
                              <td className="py-2 px-2 text-sm text-gray-700">{city}</td>
                              <td className="py-2 px-2 text-xs font-bold text-indigo-600 uppercase">{cat}</td>
                              <td className="py-2 px-2 text-sm font-bold text-right">{count}</td>
                            </tr>
                        ));
                    }
                    return null;
                  })}
                </tbody>
              </table>
            </div>
        </div>
      </div>

      {/* 5. QUALITY & ISSUES ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
         <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
           <div className="flex items-center justify-between mb-6">
             <h3 className="text-lg font-bold text-gray-700">City Match Status</h3>
             <CheckBadgeIcon className="w-6 h-6 text-teal-500" />
           </div>
           <div className="flex justify-around items-center">
             <div className="text-center">
               <p className="text-3xl font-bold text-teal-600">{displayField(data.city_match_status?.matched)}</p>
               <p className="text-sm text-gray-500 mt-1">Matched Cities</p>
             </div>
             <div className="h-12 w-px bg-gray-200"></div>
             <div className="text-center">
               <p className="text-3xl font-bold text-red-500">{displayField(data.city_match_status?.unmatched)}</p>
               <p className="text-sm text-gray-500 mt-1">Unmatched Cities</p>
             </div>
           </div>
         </div>

         <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
           <div className="flex items-center justify-between mb-6">
             <h3 className="text-lg font-bold text-gray-700">Missing Data Points</h3>
             <ExclamationTriangleIcon className="w-6 h-6 text-amber-500" />
           </div>
           <div className="space-y-4">
             <QualityRow label="Records Missing Phone" count={data.missing_values?.missing_phone} total={data.total_records} error={error} />
             <QualityRow label="Records Missing Email" count={data.missing_values?.missing_email} total={data.total_records} error={error} />
             <QualityRow label="Records Missing Address" count={data.missing_values?.missing_address} total={data.total_records} error={error} />
           </div>
         </div>
      </div>
    </div>
  );
};

// --- Helper Components ---

const MetricCard = ({ title, value, icon, color }) => (
  <div className="bg-white rounded-xl shadow-sm p-5 flex items-center justify-between border border-gray-100 transition hover:shadow-md">
    <div>
      <p className="text-gray-500 text-xs font-bold uppercase mb-1">{title}</p>
      <h4 className="text-2xl font-bold text-gray-800">{value}</h4>
    </div>
    <div className={`p-3 rounded-lg ${color} shadow-sm`}>
      {icon}
    </div>
  </div>
);

const SimpleTableCard = ({ title, icon, data, col1, col2 }) => (
  <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 h-96 flex flex-col transition hover:shadow-md">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-bold text-gray-700">{title}</h3>
      {icon}
    </div>
    <div className="overflow-y-auto flex-1">
      <table className="w-full text-left">
        <thead className="bg-gray-50 sticky top-0">
          <tr className="text-xs text-gray-500 uppercase">
            <th className="py-2 px-2">{col1}</th>
            <th className="py-2 px-2 text-right">{col2}</th>
          </tr>
        </thead>
        <tbody>
          {(data || []).map((item, index) => (
            <tr key={index} className="border-b border-gray-100 last:border-none hover:bg-gray-50 transition">
              <td className="py-2 px-2 text-sm text-gray-700 font-medium">
                {item.city || item.category || 'N/A'}
              </td>
              <td className="py-2 px-2 text-sm font-bold text-gray-800 text-right">
                {(item.count ?? 0).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const QualityRow = ({ label, count, total, error }) => {
  const percentage = error ? 0 : (Math.round(((count ?? 0) / (total || 1)) * 100) || 0);
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-semibold text-gray-800">
          {error ? <span className="text-red-500 text-xs italic">{error}</span> : `${count ?? 0} (${percentage}%)`}
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${error ? 'bg-gray-300' : 'bg-amber-400'}`} style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
};

export default MasterDataDashboard;