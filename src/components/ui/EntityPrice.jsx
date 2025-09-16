import React from "react";
import useFetch from "../../hooks/useFetch";
import { Typography } from "@mui/material";

function EntityPrice(id) {
  const number = id.id;

  const url = `/entities/${number}/stock`;

  const { data, loading, error } = useFetch(url);

  const price = data ? data.data.stock_price : "N/A";

  return (
    <Typography
      variant="h4"
      sx={{
        mt: 1,
        maxWidth: "90vw",
        wordWrap: "break-word",
      }}
    >
      {loading ? "Loading..." : error ? "Error" : `$${price}`}
    </Typography>
  );
}

export default EntityPrice;
