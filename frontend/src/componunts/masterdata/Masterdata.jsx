import React, { useState, useEffect, useCallback } from "react";
import ReusableTable from "../Table/ReusableTable"; 
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

const MasterData = () => {
  const [data, setData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState(null);

  const limit = 10;

  const columns = [
    { header: "ID", accessor: "id" },
    { header: "Category", accessor: "category" },
    { header: "City", accessor: "city" },
    { header: "Name", accessor: "name" },
    { header: "Area", accessor: "area" },
    { header: "Address", accessor: "address" },
    { header: "Phone 1", accessor: "phone_no_1" },
    { header: "Phone 2", accessor: "phone_no_2" },
    { header: "URL", accessor: "url" },
    { header: "Ratings", accessor: "ratings" },
    { header: "Sub Category", accessor: "sub_category" },
    { header: "State", accessor: "state" },
    { header: "Country", accessor: "country" },
    { header: "Email", accessor: "email" },
    { header: "Lat", accessor: "latitude" },
    { header: "Long", accessor: "longitude" },
    { header: "Reviews", accessor: "reviews" },
    { header: "Facebook", accessor: "facebook_url" },
    { header: "LinkedIn", accessor: "linkedin_url" },
    { header: "Twitter", accessor: "twitter_url" },
    { header: "Description", accessor: "description" },
    { header: "Pincode", accessor: "pincode" },
    { header: "Virtual Phone", accessor: "virtual_phone" },
    { header: "WhatsApp", accessor: "whatsapp_no" },
    { header: "Phone 3", accessor: "phone_no_3" },
    { header: "Avg Spent", accessor: "avg_spent" },
    { header: "Cost for Two", accessor: "cost_for_two" },
  ];

  const fetchMasterData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams({
        source: "master-registry", 
        page: currentPage,
        limit: limit,
        search: search,
      });

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
    fetchMasterData();
  }, [fetchMasterData]);

  useEffect(() => {
    setCurrentPage(1);
  }, [search]);

  return (
    <div className="mt-8 mb-8 px-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Typography variant="h4" className="text-gray-800 font-bold">
            Master Registry Data
          </Typography>
          <Typography variant="small" className="font-medium text-gray-500">
            {error ? (
              <span className="text-red-500 font-bold">{error}</span>
            ) : (
              `Total Records found: ${totalRecords.toLocaleString()}`
            )}
          </Typography>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-72">
            <Input
              label="Global Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button 
            variant="outlined" 
            size="sm" 
            className="flex items-center gap-2"
            onClick={fetchMasterData}
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
            Central Data Repository
          </Typography>
        </CardHeader>

        <CardBody className="overflow-x-auto p-0">
          {loading ? (
            <div className="flex flex-col justify-center py-20 items-center gap-3">
              <Spinner className="h-10 w-10 text-blue-500" />
              <Typography className="animate-pulse text-gray-600 font-medium">
                Retrieving Records...
              </Typography>
            </div>
          ) : (
            <ReusableTable columns={columns} data={data} />
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

export default MasterData;