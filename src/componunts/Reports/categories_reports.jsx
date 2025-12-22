import React, { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  Typography,
  Input,
  Spinner,
  Select,
  Option,
} from "@material-tailwind/react";
import {
  MagnifyingGlassIcon,
  ChevronUpDownIcon,
  RectangleGroupIcon,
  ChevronDownIcon, // Added missing import
} from "@heroicons/react/24/solid";
import { listingData } from "@/data/listingJSON"; 
import * as XLSX from "xlsx/dist/xlsx.full.min.js";

const defaultColumns = [
  { key: "name", label: "Name", width: 220 },
  { key: "category", label: "Category", width: 160 },
  { key: "subcategory", label: "Sub-Category", width: 160 },
  { key: "address", label: "Address", width: 300 },
  { key: "phone_number", label: "Contact", width: 140 },
  { key: "city", label: "City", width: 140 },
  { key: "source", label: "Source", width: 140 },
];

export function CategoriesReports() {
  const [loading, setLoading] = useState(true);
  const [fullData, setFullData] = useState([]);
  const [pageData, setPageData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const limit = 10;

  // --- FILTERS STATE ---
  const [selectedCategory, setSelectedCategory] = useState(""); 
  const [selectedSource, setSelectedSource] = useState(""); // <--- NEW STATE
  const [citySearch, setCitySearch] = useState("");
  
  const [sortField, setSortField] = useState(null);
  const [sortOrder, setSortOrder] = useState("asc");

  useEffect(() => {
    setLoading(true);
    setTimeout(() => {
      setFullData(listingData);
      setLoading(false);
    }, 300);
  }, []);

  // 1. GET UNIQUE CATEGORIES
  const uniqueCategories = useMemo(() => {
    if (!fullData.length) return [];
    const categories = [
      ...new Set(
        fullData.map((item) => String(item.category || "").trim()).filter(Boolean)
      ),
    ];
    return categories.sort();
  }, [fullData]);

  // 2. GET UNIQUE SOURCES (NEW LOGIC)
  const uniqueSources = useMemo(() => {
    if (!fullData.length) return [];
    const sources = [
      ...new Set(
        // Ensure your JSON has a 'source' key
        fullData.map((item) => String(item.source || "").trim()).filter(Boolean)
      ),
    ];
    return sources.sort();
  }, [fullData]);

  // 3. FILTER LOGIC
  const filteredData = useMemo(() => {
    let data = [...fullData];
    
    const normalize = (val) => String(val || "").toLowerCase().trim();
    const targetCategory = normalize(selectedCategory);
    const targetSource = normalize(selectedSource); // <--- NEW NORMALIZATION

    // Filter by Category
    if (targetCategory) {
      data = data.filter((x) => normalize(x.category) === targetCategory);
    }

    // Filter by Source (NEW)
    if (targetSource) {
      data = data.filter((x) => normalize(x.source) === targetSource);
    }
    
    // Filter by City Search
    if (citySearch) {
      const s = normalize(citySearch);
      data = data.filter((x) => normalize(x.city).includes(s));
    }
    
    return data;
  }, [fullData, selectedCategory, selectedSource, citySearch]);

  const sortedData = useMemo(() => {
    if (!sortField) return filteredData;
    return [...filteredData].sort((a, b) => {
      const A = String(a[sortField] ?? "").toLowerCase();
      const B = String(b[sortField] ?? "").toLowerCase();
      if (A === B) return 0;
      return sortOrder === "asc" ? (A > B ? 1 : -1) : (A < B ? 1 : -1);
    });
  }, [filteredData, sortField, sortOrder]);

  // Reset page when any filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedCategory, selectedSource, citySearch]);

  useEffect(() => {
    const start = (currentPage - 1) * limit;
    setPageData(sortedData.slice(start, start + limit));
  }, [sortedData, currentPage]);

  const totalPages = Math.max(1, Math.ceil(filteredData.length / limit));

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  return (
    <div className="min-h-screen mt-8 mb-12 px-4 rounded bg-[#F8FAFC]">
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white shadow-sm rounded-xl border border-gray-200">
            <RectangleGroupIcon className="h-6 w-6 text-gray-600" />
          </div>
          <div>
            <Typography variant="h4" color="blue-gray" className="font-bold tracking-tight">
              Categories Report
            </Typography>
            <Typography variant="small" className="font-medium text-gray-500">
              Analyzing records by industry classification
            </Typography>
          </div>
        </div>
      </div>

      <Card className="h-full w-full border border-gray-200 shadow-sm bg-white overflow-visible">
        <CardHeader 
          floated={false} 
          shadow={false} 
          className="rounded-none p-6 bg-white border-b border-gray-100 overflow-visible"
        >
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between overflow-visible">
            <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto relative z-50">
              
              {/* --- 1. CATEGORY SELECT --- */}
              <div className="w-full sm:w-64"> 
                {!loading && uniqueCategories.length > 0 ? (
                    <Select 
                      key={`cat-select-${selectedCategory || 'empty'}`}
                      label="Filter by Category" 
                      value={selectedCategory} 
                      onChange={(val) => setSelectedCategory(val)} 
                      className="bg-white" 
                      containerProps={{ className: "min-w-[100px]" }}
                      menuProps={{ className: "z-[9999]" }}
                    >
                      {uniqueCategories.map((cat) => (
                        <Option key={cat} value={cat}>{cat}</Option>
                      ))}
                    </Select>
                ) : (
                    <div className="w-full h-10 border border-gray-200 rounded-lg bg-gray-50 flex items-center px-3 text-gray-400 text-sm">
                        Loading...
                    </div>
                )}
                {selectedCategory && (
                   <div className="text-xs text-blue-600 font-bold cursor-pointer mt-1 text-right select-none" onClick={() => setSelectedCategory("")}>
                     Clear
                   </div>
                )}
              </div>

              {/* --- 2. SOURCE SELECT (NEW TAB IN BETWEEN) --- */}
              <div className="w-full sm:w-64"> 
                {!loading ? (
                    <Select 
                      key={`source-select-${selectedSource || 'empty'}`}
                      label="Filter by Source" 
                      value={selectedSource} 
                      onChange={(val) => setSelectedSource(val)} 
                      className="bg-white" 
                      containerProps={{ className: "min-w-[100px]" }}
                      menuProps={{ className: "z-[9999]" }}
                      // Disable if no sources found in data
                      disabled={uniqueSources.length === 0} 
                    >
                      {uniqueSources.length > 0 ? (
                        uniqueSources.map((src) => (
                          <Option key={src} value={src}>{src}</Option>
                        ))
                      ) : (
                        <Option value="" disabled>No Sources Found</Option>
                      )}
                    </Select>
                ) : (
                    <div className="w-full h-10 border border-gray-200 rounded-lg bg-gray-50 flex items-center px-3 text-gray-400 text-sm">
                        Loading...
                    </div>
                )}
                {selectedSource && (
                   <div className="text-xs text-blue-600 font-bold cursor-pointer mt-1 text-right select-none" onClick={() => setSelectedSource("")}>
                     Clear
                   </div>
                )}
              </div>

              {/* --- 3. CITY SEARCH --- */}
              <div className="w-full sm:w-64">
                <Input 
                  label="Search by City..." 
                  value={citySearch} 
                  onChange={(e) => setCitySearch(e.target.value)} 
                  icon={<MagnifyingGlassIcon className="h-5 w-5" />} 
                  className="bg-white" 
                />
              </div>

            </div>
            
            <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
                <Typography className="text-xs font-bold text-gray-500 uppercase">
                  Found: <span className="text-gray-900 ml-1">{filteredData.length}</span>
                </Typography>
            </div>
          </div>
        </CardHeader>
        
        <CardBody className="p-0 overflow-x-auto relative z-10">
          {loading ? (
            <div className="flex justify-center py-24">
              <Spinner className="h-10 w-10 text-gray-400" />
            </div>
          ) : (
            <table className="w-full table-fixed border-collapse min-w-[1000px] text-left">
              <thead className="border-b border-gray-100 bg-gray-50/50">
                <tr>
                  {defaultColumns.map((col) => (
                    <th 
                      key={col.key} 
                      style={{ width: col.width }} 
                      className="px-6 py-4 cursor-pointer hover:bg-gray-100/50 transition-colors" 
                      onClick={() => toggleSort(col.key)}
                    >
                      <div className="flex items-center justify-between text-[11px] font-bold uppercase text-gray-500 tracking-wider">
                        <span>{col.label}</span>
                        <ChevronUpDownIcon className={`h-4 w-4 ${sortField === col.key ? 'text-gray-900' : 'text-gray-300'}`} />
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="text-sm text-gray-700">
                {pageData.length === 0 ? (
                  <tr><td colSpan={6} className="text-center py-20 text-gray-400 italic">No records found.</td></tr>
                ) : (
                  pageData.map((row, idx) => (
                    <tr key={idx} className="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
                      {defaultColumns.map((col) => (
                        <td key={col.key} className="px-6 py-4 break-words align-top text-gray-600">
                          {col.key === "name" ? <span className="font-bold text-gray-900">{row[col.key]}</span> : row[col.key] || "-"}
                        </td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>

      <div className="mt-8 flex justify-center items-center gap-2">
        <Button
          variant="text"
          className="normal-case font-bold text-gray-600"
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
        >
          Previous
        </Button>
        <Typography variant="small" className="font-bold text-gray-500 px-4">
          Page {currentPage} of {totalPages}
        </Typography>
        <Button
          variant="text"
          className="normal-case font-bold text-gray-600"
          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          disabled={currentPage === totalPages}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

export default CategoriesReports;