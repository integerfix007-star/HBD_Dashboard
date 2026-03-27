import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { 
  ServerStackIcon, 
  StarIcon, 
  MapIcon, 
  TagIcon, 
  ChartBarIcon, 
  PhoneIcon 
} from "@heroicons/react/24/solid";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend 
} from "recharts";

const MasterDataDashboard = () => {
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get("task_id");
  const [dashboardData, setDashboardData] = useState(null);
  const [error, setError] = useState(null);
  const [cacheAge, setCacheAge] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [etag, setEtag] = useState(null);

  // Cache constants
  const CACHE_KEY = `dashboard_stats_${taskId || "all"}`;
  const CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

  // Get cached data if valid
  const getCachedData = () => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) return null;
      
      const { data, timestamp, etag: cachedEtag } = JSON.parse(cached);
      const age = Date.now() - timestamp;
      
      if (age < CACHE_TTL) {
        return { data, age, etag: cachedEtag };
      }
      return null; // Cache expired
    } catch (err) {
      console.warn("Cache read error:", err);
      return null;
    }
  };

  // Save data to cache
  const setCachedData = (data, etagValue) => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        data,
        timestamp: Date.now(),
        etag: etagValue
      }));
    } catch (err) {
      console.warn("Cache write error:", err);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;

    const fetchData = async () => {
      try {
        // 1. Try to get cached data first
        const cached = getCachedData();
        if (cached && cached.data) {
          if (isMounted) {
            setDashboardData(cached.data);
            setCacheAge(Math.floor(cached.age / 1000));
            setEtag(cached.etag);
            setError(null);
          }
        }

        const query = taskId ? `?task_id=${taskId}` : "";
        const url = `/api/master-dashboard-stats${query}`;

        const headers = {
          "Authorization": `Bearer ${localStorage.getItem("token") || ""}`,
          "Content-Type": "application/json",
          ...(cached?.etag && { "If-None-Match": cached.etag })
        };

        const response = await fetch(url, {
          headers,
          signal: controller.signal
        });

        // 2. Handle 304 Not Modified
        if (response.status === 304) {
          if (isMounted) {
            setCacheAge(Math.floor((Date.now() - (localStorage.getItem(CACHE_KEY) 
              ? JSON.parse(localStorage.getItem(CACHE_KEY)).timestamp 
              : Date.now())) / 1000));
          }
          return;
        }

        // 3. Check if response is JSON
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new Error("Server returned HTML instead of JSON. The API route might be incorrect.");
        }

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const result = await response.json();
        const newEtag = response.headers.get("etag");

        // 4. Extract stats and cache them
        if (result.stats) {
          if (isMounted) {
            setDashboardData(result.stats);
            setCacheAge(0); // Fresh data
            setCachedData(result.stats, newEtag);
            setEtag(newEtag);
            setError(null);
          }
        } else {
          throw new Error(result.message || "Unexpected response from server");
        }
      } catch (err) {
        if (err.name === "AbortError") return; // Request was cancelled
        console.error("Fetch error:", err);
        
        if (isMounted) {
          setError(err.message || "Failed to load dashboard data.");
          // Keep showing cached data even on error
          const cached = getCachedData();
          if (!cached) {
            setDashboardData(null);
          }
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchData();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [taskId, CACHE_KEY]);

  if (error) return (
    <div className="flex h-screen items-center justify-center bg-gray-50 flex-col px-4 text-center">
      <div className="text-red-600 font-bold text-xl mb-3">⚠️ Failed to load registry data</div>
      <div className="text-sm text-gray-600 max-w-md mb-4">{error}</div>
      {dashboardData && <div className="text-xs text-gray-500">Showing cached data</div>}
    </div>
  );

  if (!dashboardData) return (
    <div className="flex h-screen items-center justify-center bg-gray-50 flex-col">
      <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mb-6"></div>
      <h2 className="text-2xl font-bold text-gray-700">Loading Registry Data...</h2>
      <p className="text-sm text-gray-500 mt-2">Fetching from cache or server</p>
    </div>
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Cache Status Badge */}
      {cacheAge !== null && (
        <div className="mb-4 flex items-center justify-between bg-white px-4 py-2 rounded-lg text-xs text-gray-600 border border-gray-200">
          <div className="flex items-center gap-2">
            {cacheAge === 0 ? (
              <>
                <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                Fresh data (just now)
              </>
            ) : (
              <>
                <span className="inline-block w-2 h-2 bg-amber-500 rounded-full"></span>
                Cached {cacheAge}s ago (auto-refresh in {Math.ceil((CACHE_TTL - cacheAge * 1000) / 1000)}s)
              </>
            )}
          </div>
          <button
            onClick={() => {
              localStorage.removeItem(CACHE_KEY);
              setDashboardData(null);
              setCacheAge(null);
              setIsLoading(true);
              window.location.reload();
            }}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Refresh Now
          </button>
        </div>
      )}
      {/* 1. KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border-t-4 border-blue-500">
           <p className="text-gray-500 font-bold text-sm uppercase">Total Master Records</p>
           <h1 className="text-4xl font-black text-gray-800">{dashboardData.total_records.toLocaleString()}</h1>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border-t-4 border-teal-500">
           <p className="text-gray-500 font-bold text-sm uppercase">Average Rating</p>
           <h1 className="text-4xl font-black text-gray-800">{dashboardData.avg_system_rating} ★</h1>
        </div>
      </div>

      {/* 2. Top Section: State Table & Phone Chart */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <SummaryTable 
            title="State Distribution" 
            data={dashboardData.state_summary} 
            label="State" 
        />
        
        <ChartBox title="Phone Number Availability" icon={<PhoneIcon className="w-5 h-5 text-green-500"/>}>
          <PieChart>
            <Pie 
              data={dashboardData.phone_distribution || []} 
              innerRadius={60} 
              outerRadius={80} 
              paddingAngle={5}
              dataKey="value" 
              nameKey="name"
            >
              {(dashboardData.phone_distribution || []).map((entry, i) => (
                <Cell key={`cell-${i}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => value.toLocaleString()} />
            <Legend verticalAlign="bottom" />
          </PieChart>
        </ChartBox>
      </div>

      {/* 3. Bar Charts: Cities & Subcategories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChartBox title="Top 10 Cities" icon={<MapIcon className="w-5 h-5 text-red-400"/>}>
          <BarChart data={dashboardData.top_cities} layout="vertical" barCategoryGap="20%">
            <XAxis type="number" hide />
            <YAxis dataKey="name" type="category" width={100} tick={{fontSize: 11}} axisLine={false} tickLine={false} />
            <Tooltip cursor={{fill: 'transparent'}} />
            <Bar dataKey="count" fill="#f87171" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ChartBox>

        <ChartBox title="Top Subcategories" icon={<TagIcon className="w-5 h-5 text-indigo-400"/>}>
          <BarChart data={dashboardData.top_subcategories} layout="vertical" barCategoryGap="20%">
            <XAxis type="number" hide />
            <YAxis dataKey="name" type="category" width={150} tick={{fontSize: 10}} axisLine={false} tickLine={false} />
            <Tooltip cursor={{fill: 'transparent'}} />
            <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ChartBox>
      </div>

      {/* 4. Top Rated Businesses Table */}
      <div className="bg-white rounded-xl shadow-sm p-6 border transition hover:shadow-md">
        <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
          <ChartBarIcon className="w-5 h-5 text-indigo-500" /> Top Rated Businesses
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="p-3">Name</th>
                <th className="p-3">Listings Count</th>
                <th className="p-3">City</th>
                <th className="p-3">Rating</th>
              </tr>
            </thead>
            <tbody>
              {dashboardData.top_rated_businesses.map((biz, idx) => (
                <tr key={biz.id || idx} className="border-b hover:bg-gray-50">
                  <td className="p-3 font-bold text-gray-800">{biz.name}</td>
                  <td className="p-3 text-sm">
                    <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded font-bold">
                        {biz.count || biz.listings_count || 1}
                    </span>
                  </td>
                  <td className="p-3 text-gray-600">{biz.city}</td>
                  <td className="p-3 text-amber-500 font-bold">{biz.stars} ★</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// --- Helper Components ---

const SummaryTable = ({ title, data, label }) => (
  <div className="bg-white p-6 rounded-xl border shadow-sm h-96 overflow-hidden flex flex-col">
    <h3 className="font-bold text-gray-700 mb-4">{title}</h3>
    <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="text-gray-400 border-b sticky top-0 bg-white">
            <tr><th className="text-left pb-2">{label}</th><th className="text-right pb-2">Count</th></tr>
          </thead>
          <tbody>
            {(data || []).map((item, i) => (
              <tr key={i} className="border-b last:border-none">
                <td className="py-3 font-medium text-gray-700">{item.state || item.data_source || item.name}</td>
                <td className="py-3 text-right font-bold text-blue-600">{item.count?.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
    </div>
  </div>
);

const ChartBox = ({ title, icon, children }) => (
  <div className="bg-white rounded-xl shadow-sm p-6 border h-96 flex flex-col transition hover:shadow-md">
    <div className="flex justify-between items-center mb-4">
      <h3 className="font-bold text-gray-700">{title}</h3>
      {icon}
    </div>
    <div className="flex-1 min-h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  </div>
);

export default MasterDataDashboard;