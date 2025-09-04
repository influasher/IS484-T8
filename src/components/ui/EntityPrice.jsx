import React from "react";
import useFetch from "../../hooks/useFetch";
import { Typography } from '@mui/material';

function EntityPrice(id) {
  const number = id.id;

  const url = `/entities/${number}/stock`;

  const { data, loading, error } = useFetch(url);

  const price = data ? data.data.stock_price : "N/A";

  return (
    <div style={styles.container}>
      <Typography
        sx={{
          color: "black",
          fontWeight: 700,
          fontSize: "clamp(1.5rem, 4vw, 3rem)", // dynamic font size
          textAlign: "center",
          m: "0 auto", // shorthand for margin
          maxWidth: "90vw",
          wordWrap: "break-word",
        }}
      >
        {loading ? "Loading..." : error ? "Error" : `$${price}`}
      </Typography>
    </div>
  );
}
const styles = {
  container: {
    position: "relative", // Use relative positioning for better flexibility
    display: "flex",
    justifyContent: "center", // Center horizontally
    alignItems: "center", // Center vertically
    height: "auto", // Dynamic height based on content
    padding: "5px", // Add padding for spacing
    boxSizing: "border-box",
    maxWidth: "1200px", // Limit maximum width for larger screens
    margin: "0 auto", // Center the container horizontally
  },
  price: {
    backgroundColor: "grey",
    borderRadius: "15px",
    color: "black",
    fontSize: "calc(1px + 1vw)", // Adjust font size dynamically based on viewport width
    fontWeight: "bold",
    padding: "8px 16px", // Adjusted padding for better spacing
    margin: "0 10px", // Reduced margin for better responsiveness
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "auto", // Dynamic height based on content
    minWidth: "150px", // Prevent excessive shrinking on small screens
    boxSizing: "border-box",
  },
};
export default EntityPrice;
