import React from "react";
import { Container, Box, Typography } from "@mui/material";
import { Line } from "react-chartjs-2";
import {
  Chart,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";
import useFetch from "../../hooks/useFetch"; // Adjust path if needed

// Register chart elements
Chart.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

function EntityVisuals(id) {
  const number = id.id;

  const url = `/entities/${number}/chart`;

  const { data, loading, error } = useFetch(url);

  if (loading) return <p>Loading stock data...</p>;
  if (error) return <p>Error: {error}</p>;
  if (!data || !data.data || !data.data.stock_chart)
    return <p>No data available</p>;

  const stockData = {
    labels: data.data.stock_chart.dates, // X-axis (dates)
    datasets: [
      {
        label: `${data.data.name} Stock Price`,
        data: data.data.stock_chart.prices, // Y-axis (prices)
        borderColor: "#8884d8",
        backgroundColor: "rgba(136, 132, 216, 0.2)",
        pointRadius: 3,
        borderWidth: 2,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { ticks: { font: { size: 12 } } },
      y: { ticks: { font: { size: 12 } }, beginAtZero: false },
    },
    plugins: {
      legend: { display: true, position: "top" },
      tooltip: { enabled: true },
    },
  };

  return (
    <Container sx={{ mt: 4 }}>
      <Box
        sx={{
          maxWidth: 900,
          width: "100%",
          mx: "auto",
          borderRadius: 4,
          border: "1px solid #e0e0e0", // subtle border
          boxShadow: "0 4px 12px rgba(0,0,0,0.08)", // soft shadow
          backgroundColor: "#fafafa", // light background
          p: { xs: 2, sm: 3 }, // responsive padding
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 1,
        }}
      >
        <Typography
          variant="h5"
          sx={{ fontWeight: 700, textAlign: "center" }}
        >
          {data?.data?.name || "N/A"} Stock Chart
        </Typography>

        <Box sx={{ width: "100%", height: { xs: 200, sm: 300 } }}>
          <Line data={stockData} options={options} />
        </Box>
      </Box>
    </Container>
  );
}

export default EntityVisuals;
