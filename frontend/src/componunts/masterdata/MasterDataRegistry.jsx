import React, { useState, useEffect } from 'react';
import ReusableTable from '../Table/ReusableTable'; 

const MasterDataRegistry = () => {
  const [allData, setAllData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Pagination States
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);

  const columns = [
    { header: "Global ID", accessor: "global_business_id" },
    { header: "Business Name", accessor: "business_name" },
    { header: "Category", accessor: "business_category" },
    { header: "City", accessor: "city" },
    { header: "State", accessor: "state" },
    { header: "Phone", accessor: "primary_phone" },
    { header: "Data Source", accessor: "data_source" },
  ];

  useEffect(() => {
    fetchData(currentPage);
  }, [currentPage]);

  const fetchData = (page) => {
    setLoading(true);
    // BACKEND INSTRUCTION: Endpoint must support 'page' and 'limit' query params
    fetch(`http://localhost:5000/master_table/list?page=${page}&limit=10`) 
      .then(res => res.json())
      .then(result => {
        // BACKEND INSTRUCTION: Expected response format: { data: [], total_pages: X, total_count: Y }
        setAllData(result.data || []);
        setTotalPages(result.total_pages || 1);
        setTotalRecords(result.total_count || 0);
        setLoading(false);
      })
      .catch(err => {
        console.error("Fetch Error:", err);
        setLoading(false);
      });
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Complete Master Registry</h2>
        <span style={{ fontSize: '14px', color: '#666' }}>Total Records: {totalRecords}</span>
      </div>

      {loading ? (
        <p>Loading Page {currentPage}...</p>
      ) : (
        <>
          <ReusableTable columns={columns} data={allData} />
          
          {/* PAGINATION CONTROLS */}
          <div style={{ 
            marginTop: '20px', 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '15px' 
          }}>
            <button 
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
              style={{ padding: '5px 15px', cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}
            >
              Previous
            </button>

            <span style={{ fontWeight: 'bold' }}>
              Page {currentPage} of {totalPages}
            </span>

            <button 
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(prev => prev + 1)}
              style={{ padding: '5px 15px', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer' }}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default MasterDataRegistry;