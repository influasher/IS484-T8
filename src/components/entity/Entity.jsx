import React from "react";
import useFetch from "../../hooks/useFetch";
import { Box, Typography } from "@mui/material";

function Entity({ EntityTicker }) {
  const url = `/entities/${EntityTicker}`;

  const { data, loading, error } = useFetch(url);

  const entity = data ? data.data : "N/A";

  return (
    <Box sx={styles.container}>
      <Typography sx={styles.entityname} variant="h1">
        {loading
          ? "Loading..."
          : error
          ? "Error fetching data"
          : (
              <>
                {entity.name}{" "}
                <Typography component="span" sx={{ color: "grey.400", fontWeight: "500" }} variant="h5">
                  ({EntityTicker})
                </Typography>
              </>
            ) || "N/A"}
      </Typography>
    </Box>
  );
}
const styles = {
  container: {
    display: "flex",
    flexDirection: "column", // Stack content vertically
    justifyContent: "center", // Center content vertically
    alignItems: "center", // Center content horizontally
    padding: "5px", // Add padding for spacing
    boxSizing: "border-box", // Include padding in width/height calculations
    maxWidth: "1200px", // Limit maximum width for larger screens
    margin: "0 auto", // Center the container horizontally
  },
  entityname: {
    color: "black",
    fontWeight: "700",
    fontSize: "clamp(1rem, 4vw, 2.5rem)", // Dynamic font size (min: 1.5rem, max: 3rem)
    textAlign: "center", // Center text alignment
    margin: "0 auto", // Center horizontally
    maxWidth: "90vw", // Ensure it doesn't overflow on small screens
    wordWrap: "break-word", // Handle long words
  },
};

export default Entity;
