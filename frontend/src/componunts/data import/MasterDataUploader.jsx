import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../utils/Api"; 

const MasterDataUploader = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault(); // Prevents page reload
    if (!file) return alert("Select a file first!");

    const formData = new FormData();
    formData.append("file", file);

    console.log("Starting upload..."); // Debug Log 1

    try {
      setLoading(true);
      
      const response = await api.post("/upload/master", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("Upload Response:", response.data); // Debug Log 2

      // Check specifically for task_id
      const task_id = response.data.task_id;

      if (task_id) {
        console.log("Redirecting to task:", task_id); // Debug Log 3
        
        // --- FIX: Added '/dashboard' prefix based on your routes.js layout ---
        // Try navigating to the full path. 
        // If your URL bar usually shows /dashboard/home, this needs to be /dashboard/masterdata/dashboard
        navigate(`/dashboard/masterdata/dashboard?task_id=${task_id}`);
        
      } else {
        console.error("No task_id in response");
        alert("Upload finished, but no Task ID was returned by the server.");
      }

    } catch (error) {
      console.error("Master Upload Error:", error);
      alert("Upload failed. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md border-t-4 border-gray-900">
      <h2 className="text-xl font-bold mb-4 text-gray-900">Upload Master Data CSV</h2>
      <p className="text-sm text-gray-500 mb-4">
        This file will populate the central database. You will be redirected automatically.
      </p>
      
      <form onSubmit={handleUpload} className="flex flex-col gap-4">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-white hover:file:bg-gray-900"
        />
        
        <button
          type="submit"
          disabled={loading || !file}
          className={`py-2 px-4 rounded font-bold text-white transition-all ${
            loading ? "bg-gray-400" : "bg-gray-700 hover:bg-gray-900"
          }`}
        >
          {loading ? "Processing..." : "Upload Master CSV"}
        </button>
      </form>
    </div>
  );
};

export default MasterDataUploader;