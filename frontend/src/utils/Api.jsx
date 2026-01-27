import axios from "axios";

const api = axios.create({
  // Use localhost instead of 127.0.0.1 to ensure better compatibility with CORS
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000", 
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;