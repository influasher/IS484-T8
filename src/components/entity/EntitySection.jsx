import React from "react";
import { useParams } from "react-router-dom";
import { Box, CircularProgress, Typography } from "@mui/material";
import EntityHeader from "./EntityHeader";
import EntityVisuals from "./Entityvisuals";
import EntityNews from "./Entitynews";
import useFetch from "../../hooks/useFetch";
import "../../styles/App.css";

const EntitySection = () => {
  const { ticker } = useParams();
  console.log(ticker);
  const url = `/entities/${ticker}`;
  const { data, loading, error } = useFetch(url);
  const EntityName = data ? data.data.name : "N/A";
  const stockID = data ? data.data.id : "N/A";

  if (loading)
    return (
      <Box sx={styles.loading}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading...
        </Typography>
      </Box>
    );

  if (error)
    return (
      <Box sx={styles.error}>
        <Typography variant="h6" color="error">
          Error fetching entity data.
        </Typography>
      </Box>
    );

  return (
    <>
      <EntityHeader data={data} />

      <EntityVisuals id={stockID} />

      <EntityNews EntityName={EntityName} />
    </>
  );
};

const styles = {
  loading: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    fontSize: "1.5rem",
  },

  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    fontSize: "1.5rem",
  },
};

export default EntitySection;
