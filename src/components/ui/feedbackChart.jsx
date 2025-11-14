import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { useLocation } from "react-router-dom";
import useFetch from "../../hooks/useFetch";
import { Box, Typography, CircularProgress } from "@mui/material";
import { PieChart } from "@mui/x-charts/PieChart";

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

function VoteChart({ fetchKey }) {
  const location = useLocation();
  const { id } = location.state || { id: null };

  // Use the news ID directly - the backend will handle UUID string format
  const { data, loading, error } = useFetch(`labeling/votes/news/${id}`, {
    key: fetchKey,
  });

  // Fetch the agreement rate from news endpoint
  const { data: agreementData } = useFetch(`/news/id/${id}`);
  const agreementScore = agreementData?.data?.agreement_rate;

  // Handle loading state
  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Handle error or no data state
  if (error || !data || !data.data) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
      >
        <Typography color="textSecondary">
          No feedback data available
        </Typography>
      </Box>
    );
  }

  const voteData = data.data;
  let bearishCount = 0,
    neutralCount = 0,
    bullishCount = 0;

  voteData.forEach((item) => {
    switch (item.vote) {
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

  // Calculate the total number of votes
  const totalCount = bearishCount + neutralCount + bullishCount;
  const chartData = [
    { id: 0, value: bullishCount, label: "Bullish" },
    { id: 1, value: neutralCount, label: "Neutral" },
    { id: 2, value: bearishCount, label: "Bearish" },
  ];

  console.log("Chart Data:", chartData);

  // Show message if no votes yet
  if (totalCount === 0) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
      >
        <Typography color="textSecondary" fontStyle="italic">
          No user feedback submitted yet
        </Typography>
      </Box>
    );
  }

  // Calculate percentages
  const bearishPercentage = (bearishCount / totalCount) * 100;
  const neutralPercentage = (neutralCount / totalCount) * 100;
  const bullishPercentage = (bullishCount / totalCount) * 100;

  // // Pie chart data
  // const chartData = {
  //   labels: ["Bearish", "Neutral", "Bullish"],
  //   datasets: [
  //     {
  //       data: [bearishPercentage, neutralPercentage, bullishPercentage],
  //       backgroundColor: ["#dc3545", "#6c757d", "#28a745"],
  //       borderColor: "black",
  //       borderWidth: 3,
  //     },
  //   ],
  // };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "bottom",
        labels: { font: { size: 15 } },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || "";
            const value = context.raw || 0;
            const count = Math.round((value / 100) * totalCount);
            // REMOVED: confidence display from tooltip
            return `${label}: ${value.toFixed(1)}% (${count} votes)`;
          },
        },
      },
    },
  };

  // Disable the pie if agreementScore is 1
  if (!agreementData || agreementScore === 1) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
      >
        <Typography color="textSecondary" fontStyle="italic">
          No feedback required
        </Typography>
      </Box>
    );
  }

  return (
    <Box
    >
      <PieChart
        series={[
          {
            data: chartData,
          },
        ]}
        height={250}
        width={300}
        margin={{ right: 5 }}
      />
    </Box>
  );
}

export default VoteChart;
