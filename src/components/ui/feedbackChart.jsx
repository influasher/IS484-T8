import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { useLocation } from 'react-router-dom';
import useFetch from '../../hooks/useFetch';
import { Box, Typography, CircularProgress } from '@mui/material';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

function PieChart({ key }) {
  const location = useLocation();
  const { id } = location.state || { id: null };
  const { data, loading, error } = useFetch(`feedback/news/${id}`, { key });

  // Fetch the agreement rate
  const { data: agreementData } = useFetch(`/news/id/${id}`);  // Assuming a different endpoint
  const agreementScore = agreementData?.data?.agreement_rate;

  // Handle loading state
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
      </Box>
    );
  }

  // Handle error state
  if (error || !data || !data.data) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <Typography color="error">Error fetching feedback data.</Typography>
      </Box>
    );
  }

  // Process feedbackData to count sentiments
  const feedbackData = data.data;
  let bearishCount = 0,
    neutralCount = 0,
    bullishCount = 0;

  feedbackData.forEach((item) => {
    switch (item.assessment) {
      case "bearish":
        bearishCount++;
        break;
      case "neutral":
        neutralCount++;
        break;
      case "bullish":
        bullishCount++;
        break;
      default:
        break;
    }
  });

  // Calculate the total number of feedback entries
  const totalCount = bearishCount + neutralCount + bullishCount;

  // Calculate percentages for each sentiment (out of 100)
  const bearishPercentage = totalCount > 0 ? (bearishCount / totalCount) * 100 : 0;
  const bullishPercentage = totalCount > 0 ? (bullishCount / totalCount) * 100 : 0;

  // Pie chart data
  const chartData = {
    labels: ["Bearish", "Bullish"],
    datasets: [
      {
        data: [bearishPercentage, bullishPercentage], // Percentages for each segment
        backgroundColor: ["red", "green"], // Colors for each segment
        borderColor: "black", // Border color for all segments
        borderWidth: 3, // Border width
      },
    ],
  };

  // Options for the pie chart
  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "bottom", // Move the legend to the bottom
        labels: {
          font: {
            size: 15, // Font size for legend labels
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || "";
            const value = context.raw || 0;
            return `${label}: ${value.toFixed(1)}%`; // Format tooltip to show percentage
          },
        },
      },
    },
  };

  // Disable the pie if agreementScore is 1
  if (!agreementData || agreementScore === 1) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <Typography color="textSecondary" fontStyle="italic">
          No feedback required
        </Typography>
      </Box>
    );
  }

  return (
    <Box width="55%" margin="0 auto" textAlign="center">
      <Typography variant="h5" gutterBottom>
        Feedback Based on Users
      </Typography>
      <Pie data={chartData} options={options} />
    </Box>
  );
}

export default PieChart;
