import React, { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardHeader,
  Typography,
  CardBody,
  Input,
  Button,
  Spinner,
} from "@material-tailwind/react";
import { ChevronUpDownIcon, ArrowPathIcon } from "@heroicons/react/24/solid";

const DuplicateData = () => {
  const [data, setData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState(null);

  const limit = 10; // Standardized limit for consistency

  const fetchDuplicateData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams({
        source: "duplicate", // Specifically requesting duplicate records from master table
        page: currentPage,
        limit: limit,
        search: search,
      });

      // Updated to point to root endpoint
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
  }, [currentPage, search]);

  useEffect(() => {
    fetchDuplicateData();
  }, [fetchDuplicateData]);

  // Reset to page 1 when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [search]);

  const tableHeaders = [
    { key: "id", label: "ID" },
    { key: "category", label: "Category" },
    { key: "city", label: "City" },
    { key: "name", label: "Name" },
    { key: "area", label: "Area" },
    { key: "address", label: "Address" },
    { key: "phone_no_1", label: "Phone 1" },
    { key: "phone_no_2", label: "Phone 2" },
    { key: "url", label: "URL" },
    { key: "ratings", label: "Ratings" },
    { key: "sub_category", label: "Sub Category" },
    { key: "state", label: "State" },
    { key: "country", label: "Country" },
    { key: "email", label: "Email" },
    { key: "pincode", label: "Pincode" },
    { key: "whatsapp_no", label: "WhatsApp" }
  ];

  return (
    <div className="mt-8 mb-8 px-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Typography variant="h4" className="text-gray-800 font-bold">
            Duplicate Data Master
          </Typography>
          <Typography variant="small" className="font-medium text-gray-500">
            {error ? (
              <span className="text-red-500 font-bold">{error}</span>
            ) : (
              `Displaying verified duplicate records (${totalRecords} total)`
            )}
          </Typography>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-72">
            <Input
              label="Search duplicates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button 
            variant="outlined" 
            size="sm" 
            className="flex items-center gap-2"
            onClick={fetchDuplicateData}
          >
            <ArrowPathIcon className="h-4 w-4" /> Refresh
          </Button>
        </div>
      </div>

      <Card className="border border-gray-200 rounded-xl shadow-sm bg-white overflow-hidden">
        <CardHeader
          floated={false}
          shadow={false}
          className="bg-gray-100 border-b border-gray-300 px-6 py-4 rounded-none"
        >
          <Typography variant="h6" className="text-gray-800 font-semibold">
            Duplicate Records Registry
          </Typography>
        </CardHeader>

        <CardBody className="overflow-x-auto p-0">
          {loading ? (
            <div className="flex flex-col justify-center py-20 items-center gap-3">
              <Spinner className="h-10 w-10 text-blue-500" />
              <Typography className="animate-pulse text-gray-600 font-medium">Synchronizing Master Table...</Typography>
            </div>
          ) : (
            <table className="w-full min-w-[1500px] table-fixed text-left">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {tableHeaders.map((head) => (
                    <th key={head.key} className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Typography
                          variant="small"
                          className="text-[11px] font-bold uppercase text-gray-600 opacity-70"
                        >
                          {head.label}
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
                    <td colSpan={tableHeaders.length} className="text-center py-10 text-gray-500 italic font-medium">
                      No duplicate entries found in master table
                    </td>
                  </tr>
                ) : (
                  data.map((item, idx) => (
                    <tr key={idx} className="hover:bg-blue-50/30 border-b border-gray-100 transition-colors">
                      {tableHeaders.map((header) => (
                        <td key={header.key} className="px-4 py-3 text-sm text-gray-700 truncate max-w-[200px]">
                          {item[header.key] || "-"}
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

export default DuplicateData;