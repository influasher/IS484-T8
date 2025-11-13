import React from "react";
import ClientCards from "../../components/clients/ClientCards";
import StockWatchlist from "../../components/ui/Watchlist";
import { Box, Paper } from "@mui/material";
import News from "../../components/news/News";

const RMHomePage = () => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        p: 2,
        gap: 2,
      }}
    >
      {/* ClientCards takes one full row */}
      <Box sx={{ width: "100%" }}>
        <ClientCards sx={{ pt: "84px" }} />
      </Box>

      {/* StockWatchlist and News share one row as two columns */}
      <Box
        sx={{ display: "flex", flexDirection: "row", width: "100%", gap: 2 }}
      >
        {/* Left column */}
        <Box
          sx={{
            flex: 1,
            p: 2,
          }}
        >
          <Paper sx={{ width: "100%", backgroundColor: "white", p:2}}>
            <StockWatchlist />
          </Paper>
        </Box>

        {/* Right column */}
        <Box
          sx={{
            flex: 1,
            p: 2,
          }}
        >
          <Paper sx={{ width: "100%", backgroundColor: "white" }}>
            <News />
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default RMHomePage;
