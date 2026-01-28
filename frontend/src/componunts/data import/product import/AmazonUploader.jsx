import React, { useState, useEffect } from "react";
import api from "../../../utils/Api";

const MAX_FILE_SIZE = 30 * 1024 * 1024; // 30MB

const AmazonUploader = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false); // For upload state
  
  // New state for fetching data
  const [products, setProducts] = useState([]);
  const [isFetching, setIsFetching] = useState(false);

  // --- 1. Fetch Data Function ---
  const fetchProducts = async () => {
    try {
      setIsFetching(true);
      // Endpoint from app.py: @app.route('/api/amazon_products', methods=['GET'])
      const response = await api.get("/api/amazon_products");
      setProducts(response.data);
    } catch (error) {
      console.error("Error fetching amazon products:", error);
    } finally {
      setIsFetching(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchProducts();
  }, []);

  // --- 2. File Selection Logic (Existing) ---
  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = [];
    for (let file of selectedFiles) {
      if (!file.name.endsWith(".csv")) {
        alert(`${file.name} is not a CSV file`);
        continue;
      }
      if (file.size > MAX_FILE_SIZE) {
        alert(`${file.name} exceeds 30MB limit`);
        continue;
      }
      validFiles.push(file);
    }
    setFiles(validFiles);
  };

  // --- 3. Upload Logic (Updated Endpoint) ---
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (files.length === 0) {
      alert("Please select at least one CSV file!");
      return;
    }

    const formData = new FormData();
    files.forEach((file) => {
      // Key must be "files" to match: request.files.getlist("files") in flask blueprint
      formData.append("files", file); 
    });

    try {
      setLoading(true);

      // Endpoint from blueprint: @amazon_bp.route("/upload/amazon-data")
      // Prefix defined in app.py: app.register_blueprint(amazon_bp,url_prefix="/amazon")
      const response = await api.post(
        "/amazon/upload/amazon-data",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log("Upload successful:", response.data);
      alert(`Files uploaded! Task ID: ${response.data.task_id}. Processing in background...`);
      setFiles([]);
      
      // Refresh table after a short delay to allow Celery to start processing
      setTimeout(() => {
        fetchProducts();
      }, 2000);

    } catch (error) {
      console.error("Error uploading files:", error);
      alert("File upload failed!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* --- UPLOAD SECTION --- */}
      <div className="p-6 max-w-xlg bg-white rounded-lg shadow mt-6">
        <h2 className="text-xl font-bold mb-4">Upload Amazon CSV Files</h2>

        <form onSubmit={handleSubmit}>
          <input
            type="file"
            accept=".csv"
            multiple
            onChange={handleFileChange}
            disabled={loading}
            className="mb-4 block w-full border border-gray-300 rounded-lg p-2"
          />

          {files.length > 0 && (
            <ul className="mb-4 text-sm text-gray-700">
              {files.map((file, index) => (
                <li key={index}>
                  {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </li>
              ))}
            </ul>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`px-4 py-2 rounded-lg text-white flex items-center justify-center ${
              loading
                ? "bg-gray-500 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin h-5 w-5 mr-2 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  ></path>
                </svg>
                Uploading...
              </span>
            ) : (
              "Upload"
            )}
          </button>
        </form>
      </div>

      {/* --- DATA TABLE SECTION --- */}
      <div className="p-6 max-w-xlg bg-white rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Uploaded Products</h2>
          <button 
            onClick={fetchProducts}
            className="text-sm text-blue-600 hover:underline"
          >
            Refresh List
          </button>
        </div>

        {isFetching ? (
          <p className="text-gray-500">Loading data...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm whitespace-nowrap">
              <thead className="uppercase tracking-wider border-b-2 border-gray-200 bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3">ID</th>
                  <th scope="col" className="px-6 py-3">ASIN</th>
                  <th scope="col" className="px-6 py-3">Product Name</th>
                  <th scope="col" className="px-6 py-3">Price</th>
                  <th scope="col" className="px-6 py-3">Rating</th>
                  <th scope="col" className="px-6 py-3">Brand</th>
                </tr>
              </thead>
              <tbody>
                {products.length > 0 ? (
                  products.map((item) => (
                    <tr key={item.id || item.ASIN} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">{item.id}</td>
                      <td className="px-6 py-4">{item.ASIN}</td>
                      {/* Truncate long names */}
                      <td className="px-6 py-4" title={item.Product_name}>
                        {item.Product_name?.substring(0, 40)}{item.Product_name?.length > 40 ? "..." : ""}
                      </td>
                      <td className="px-6 py-4">{item.price}</td>
                      <td className="px-6 py-4">{item.rating}</td>
                      <td className="px-6 py-4">{item.Brand}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                      No products found. Upload a CSV to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AmazonUploader;