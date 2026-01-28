import React, { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardHeader,
  Typography,
  CardBody,
  Spinner,
  Button,
} from "@material-tailwind/react";
import { ChevronUpDownIcon, ArrowPathIcon } from "@heroicons/react/24/solid";

const BusinessCategory = () => {
  const [data, setData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const limit = 10; // Standardized to 10 as per team requirements

  const fetchBusinessData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams({
        source: "business-category",
        page: currentPage,
        limit: limit,
      });

      // Updated to point to root endpoint as requested
      const response = await fetch(`http://localhost:5000/?${queryParams}`);
      
      if (!response.ok) throw new Error("Backend connection failed");

      const result = await response.json();
      
      setData(result.data || []);
      setTotalPages(result.total_pages || 1);
      setTotalRecords(result.total_count || 0);
    } catch (err) {
      console.error("Fetch Error:", err);
      setError("Failed to Fetch data from backend");
    } finally {
      setLoading(false);
    }
  }, [currentPage]);

  useEffect(() => {
    fetchBusinessData();
  }, [fetchBusinessData]);

  const tableHeaders = [
    "ID", "Category", "City", "Name", "Area", "Address", 
    "Phone 1", "Phone 2", "URL", "Ratings", "Sub Category", 
    "State", "Country", "Email", "Lat", "Long"
  ];

  return (
    <div className="mt-8 mb-8 px-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <Typography variant="h4" className="text-gray-800 font-bold">
            Business Category Data
          </Typography>
          <Typography variant="small" className="text-gray-600">
            {error ? <span className="text-red-500 font-bold">{error}</span> : `Total Records: ${totalRecords}`}
          </Typography>
        </div>
        <Button 
          variant="outlined" 
          size="sm" 
          className="flex items-center gap-2"
          onClick={fetchBusinessData}
        >
          <ArrowPathIcon className="h-4 w-4" /> Refresh
        </Button>
      </div>

      <Card className="border border-gray-200 rounded-xl shadow-sm bg-white overflow-hidden">
        <CardHeader
          floated={false}
          shadow={false}
          className="bg-gray-100 border-b border-gray-300 px-6 py-4 rounded-none"
        >
          <Typography variant="h6" className="text-gray-800 font-semibold">
            Master Registry: Business Categories
          </Typography>
        </CardHeader>

        <CardBody className="overflow-x-auto p-0">
          {loading ? (
            <div className="flex flex-col justify-center py-20 items-center gap-3">
              <Spinner className="h-10 w-10 text-blue-500" />
              <Typography color="gray" className="font-medium">Fetching Master Table...</Typography>
            </div>
          ) : (
            <table className="w-full min-w-[1500px] table-fixed text-left">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {tableHeaders.map((head) => (
                    <th key={head} className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Typography
                          variant="small"
                          className="text-[11px] font-bold uppercase text-gray-600 opacity-70"
                        >
                          {head}
                        </Typography>
                        <ChevronUpDownIcon className="h-3 w-3" />
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.length === 0 ? (
                  <tr>
                    <td colSpan={tableHeaders.length} className="text-center py-10 text-gray-500 italic">
                      No business categories found in master table
                    </td>
                  </tr>
                ) : (
                  data.map((item, idx) => (
                    <tr key={idx} className="hover:bg-blue-50/30 border-b border-gray-100 transition-colors">
                      <td className="px-4 py-3 text-sm">{item.id || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.category || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.city || "-"}</td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.name || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.area || "-"}</td>
                      <td className="px-4 py-3 text-sm truncate max-w-[200px]">{item.address || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.phone_no_1 || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.phone_no_2 || "-"}</td>
                      <td className="px-4 py-3 text-sm text-blue-600 truncate max-w-[150px]">{item.url || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.ratings || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.sub_category || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.state || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.country || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.email || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.latitude || "-"}</td>
                      <td className="px-4 py-3 text-sm">{item.longitude || "-"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>

      {/* Pagination UI */}
      <div className="flex items-center justify-between mt-6 px-2">
        <Typography variant="small" className="font-bold text-gray-700">
          Page {currentPage} of {totalPages}
        </Typography>
        <div className="flex gap-2">
          <Button
            variant="outlined"
            size="sm"
            disabled={currentPage === 1 || loading}
            onClick={() => setCurrentPage((p) => p - 1)}
          >
            Previous
          </Button>
          <Button
            variant="outlined"
            size="sm"
            disabled={currentPage === totalPages || loading}
            onClick={() => setCurrentPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
};

export default BusinessCategory;