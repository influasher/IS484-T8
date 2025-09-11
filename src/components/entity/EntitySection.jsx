import React from "react";
import { useParams } from "react-router-dom";
import { Box, CircularProgress, Typography, Link as MuiLink } from "@mui/material";
import EntityHeader from "./EntityHeader";
import EntityVisuals from "./Entityvisuals";
import EntityNews from "./Entitynews";
import EntityProfile from "./EntityProfile";
import useFetch from "../../hooks/useFetch";
import "../../styles/App.css";
import { Link } from "react-router-dom";

const EntitySection = () => {
  const { ticker } = useParams();
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
    <Box sx={{ display: "flex" }}>
      <Box sx={{ flex: 1, padding: 2 }}>
        <EntityHeader data={data} />
        <EntityVisuals id={stockID} />
        <div style={{ textAlign: "center" }}>
          <Typography variant="h6" sx={{ mt: 2 }}>
            <MuiLink 
              component={Link}
              to="/NewsPage">
                Search for more news
            </MuiLink>
          </Typography>
          <EntityNews EntityName={EntityName} />
        </div>
      </Box>
      <Box sx={{ width: "25%", borderLeft: "1px solid #ddd", padding: 2 }}>
        <EntityProfile data={data} />
      </Box>
    </Box>
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
