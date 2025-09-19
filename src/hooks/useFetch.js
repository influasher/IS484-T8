import { useState, useEffect } from "react";
import { getData } from "../services/api"; // ✅ Use api.js

const useFetch = (endpoint) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!endpoint) return; // skip fetch if endpoint is null
    
    const fetchData = async () => {
      try {
        const result = await getData(endpoint);
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint]);

  return { data, loading, error };
};

export default useFetch;
