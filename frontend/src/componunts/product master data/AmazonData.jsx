import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Typography,
  Button,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
} from "@material-tailwind/react";
import { ArrowPathIcon, ArrowTopRightOnSquareIcon, MagnifyingGlassIcon } from "@heroicons/react/24/solid";
import ReusableTable from '../Table/ReusableTable'; 
import api from "../../utils/Api";

const AmazonData = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const amazonColumns = [
    {
      header: "Product Detail",
      accessor: "Product_name",
      render: (row) => {
        // Fallback for broken image URLs
        const imageList = row.Image_URLs ? row.Image_URLs.split(' | ') : [];
        const mainImage = imageList[0] || 'https://www.aaronfaber.com/wp-content/uploads/2017/03/product-placeholder.jpg';
        
        return (
          <div className="flex items-center gap-4">
            <Avatar
              src={mainImage}
              alt={row.Product_name}
              size="md"
              variant="rounded"
              className="border border-blue-gray-50 bg-white object-contain p-1 shadow-sm"
              onError={(e) => { e.target.src = 'https://via.placeholder.com/150?text=No+Image'; }}
            />
            <div className="flex flex-col">
              <Typography variant="small" color="blue-gray" className="font-bold leading-tight max-w-[300px]">
                {row.Product_name?.substring(0, 50)}...
              </Typography>
              <Typography className="text-[11px] font-medium text-gray-500 mt-1">
                ASIN: <span className="text-blue-600 font-bold">{row.ASIN}</span>
              </Typography>
            </div>
          </div>
        );
      }
    },
    {
      header: "Brand",
      accessor: "Brand",
      render: (row) => (
        <Chip
          variant="ghost"
          size="sm"
          value={row.Brand || "Generic"}
          className="rounded-full normal-case bg-gray-100 text-gray-700 border-none"
        />
      )
    },
    {
      header: "Price",
      accessor: "price",
      render: (row) => (
        <Typography variant="small" className="font-black text-blue-gray-900 bg-gray-100/50 px-2 py-1 rounded-lg w-fit">
           {row.price || "N/A"}
        </Typography>
      )
    },
    {
      header: "Ratings",
      accessor: "rating",
      render: (row) => (
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1">
            <Typography variant="small" className="font-bold text-orange-800">{row.rating || "0"}</Typography>
            <span className="text-orange-400 text-xs">★</span>
          </div>
          <Typography className="text-[10px] text-gray-400 font-medium">
            ({row.Number_of_ratings?.toLocaleString() || 0} reviews)
          </Typography>
        </div>
      )
    },
    {
      header: "Source",
      accessor: "link",
      render: (row) => (
        <Tooltip content="Open Amazon Page">
          <IconButton 
            variant="text" 
            color="blue-gray" 
            className="hover:bg-blue-50 hover:text-blue-600 transition-colors"
            onClick={() => window.open(row.link, '_blank')}
          >
            <ArrowTopRightOnSquareIcon className="h-5 w-5" />
          </IconButton>
        </Tooltip>
      )
    }
  ];

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/amazon_products');
      setProducts(response.data);
    } catch (error) {
      console.error("Fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  return (
    <div className="mt-10 mb-8 flex flex-col gap-6 px-4 bg-slate-50/50 min-h-screen">
      <Card className="overflow-hidden border border-gray-200 bg-gradient-to-br from-white to-gray-500/10 shadow-sm">
        <CardHeader 
          floated={false} 
          shadow={false} 
          className="m-0 p-6 flex justify-between items-center bg-white/60 border-b border-gray-100"
        >
          <div>
            <Typography variant="h5" color="blue-gray" className="font-black tracking-tight uppercase">
               Amazon Inventory Explorer
            </Typography>
            <Typography className="font-normal text-gray-500 text-sm">
              Live data from your recent scraping tasks
            </Typography>
          </div>
          <Button
            variant="outlined"
            size="sm"
            className="flex items-center gap-2 border-gray-300 normal-case font-bold"
            onClick={loadData}
            disabled={loading}
          >
            <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Inventory
          </Button>
        </CardHeader>

        <CardBody className="px-0 pt-0 pb-2">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 animate-pulse">
               <MagnifyingGlassIcon className="h-12 w-12 text-gray-200 mb-4" />
               <Typography color="gray" className="font-bold text-gray-400">Loading your catalog...</Typography>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-24 border-2 border-dashed border-gray-100 m-6 rounded-3xl">
               <Typography color="gray" className="font-medium italic">Your inventory is empty. Start a scraper task!</Typography>
            </div>
          ) : (
            <div className="p-4">
               <ReusableTable columns={amazonColumns} data={products} />
            </div>
          )}
        </CardBody>
      </Card>

      <footer className="mt-auto py-6 text-center">
        <Typography variant="small" className="font-bold text-gray-300 uppercase tracking-widest">
           Found {products.length} active listings
        </Typography>
      </footer>
    </div>
  );
};

export default AmazonData;