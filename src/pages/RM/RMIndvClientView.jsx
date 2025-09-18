import React from "react";
import ClientRecc from "../../components/clients/ClientRecc";
import StockWatchlist from "../../components/ui/Watchlist";
import { Box, Paper } from "@mui/material";

const RMIndvClientView = () => {
  return (
    <div>
      <ClientRecc />
      <Box
        sx={{
          minHeight: "100vh",
          bgcolor: (t) => t.palette.grey[100],
          p: { xs: 1.5, sm: 2.5, md: 3 },
        }}
      >
        <Paper
          elevation={1}
          sx={{ borderRadius: 3, p: { xs: 2, sm: 3 }, bgcolor: "white" }}
        >
          <StockWatchlist />
        </Paper>
      </Box>
    </div>
  );
};

export default RMIndvClientView;
