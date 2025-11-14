import React, { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  CircularProgress,
  Typography,
  Link as MuiLink,
  Chip,
  Tooltip,
  Grid,
  Divider,
  Container,
  ToggleButtonGroup,
  ToggleButton,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  Stack,
} from "@mui/material";
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import useFetch from "../../hooks/useFetch";
import { Link } from "react-router-dom";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import "../../styles/App.css";
import EntityPrice from "../ui/EntityPrice";
import ReportButton from "../ui/export";
import SendPDF from "../ui/SendReport";
import CustomChip from "../ui/CustomChip";
import { ROUTES } from "../../routes";

const IndvEntity = () => {
  const { ticker } = useParams();
  const url = `/entities/${ticker}`;
  const { data, loading, error } = useFetch(url);
  const stockID = data?.data?.id ?? null;
  const EntityName = data?.data?.name ?? null;
  const EntityTicker = data?.data?.ticker ?? null;

  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const newsPerPage = 4; // Matches backend
  const [selectedNews, setSelectedNews] = useState(null); // State to track selected news

  // Construct API URL with pagination parameters
  const newsUrl = `/news/entity/${ticker}?page=${currentPage}&per_page=${newsPerPage}`;
  const {
    data: newsRawData,
    loading: newsLoading,
    error: newsError,
  } = useFetch(newsUrl);

  // Extract news data
  const newsData = newsRawData?.data.news ?? [];
  const totalPages = newsRawData?.data.pages ?? 1; // Ensure valid number
  const currentNews = newsData; // Directly use API response

  console.log("News Data:", newsData);

  const [timeRange, setTimeRange] = useState("1Y"); // Default to 1 year

  const timeRanges = [
    { value: "1D", label: "1D" },
    { value: "1W", label: "1W" },
    { value: "1M", label: "1M" },
    { value: "3M", label: "3M" },
    { value: "6M", label: "6M" },
    { value: "1Y", label: "1Y" },
    { value: "YTD", label: "YTD" },
    { value: "5Y", label: "5Y" },
  ];

  const entityUrl = stockID
    ? `/entities/${stockID}/chart?period=${timeRange}`
    : null;
  const irxUrl = `/entities/ticker=^IRX/chart?period=${timeRange}`;

  // Fetch entity data
  const {
    data: entityData,
    loading: entityLoading,
    error: entityError,
  } = useFetch(entityUrl);

  // Fetch IRX data
  const {
    data: irxData,
    loading: irxLoading,
    error: irxError,
  } = useFetch(irxUrl);

  const getColor = (sentimentType) => {
    if (sentimentType > 0) return "success";
    if (sentimentType < 0) return "error";
    return "default";
  };

  const handleTimeRangeChange = (event, newTimeRange) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
    }
  };

  // Function to calculate cumulative returns
  const calculateCumulativeReturns = (prices) => {
    if (!prices || prices.length === 0) return [];

    const basePrice = prices[0];
    return prices.map((price) => ((price - basePrice) / basePrice) * 100);
  };

  if (entityLoading || irxLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading chart data...</Typography>
      </Box>
    );
  }

  if (entityError) {
    return (
      <Typography color="error" sx={{ py: 4, textAlign: "center" }}>
        Entity Error: {entityError}
      </Typography>
    );
  }

  if (irxError) {
    return (
      <Typography color="error" sx={{ py: 4, textAlign: "center" }}>
        IRX Error: {irxError}
      </Typography>
    );
  }

  // Only check for empty data **after loading finishes and no error**
  if (
    !entityData?.data?.stock_chart ||
    entityData.data.stock_chart.prices.length === 0
  ) {
    return (
      <Typography sx={{ py: 4, textAlign: "center" }}>
        No entity data available
      </Typography>
    );
  }

  const performanceChange = entityData.data.stock_chart.performance;
  console.log("Performance Change:", performanceChange);

  // Process entity data
  const entityDates = entityData.data.stock_chart.dates.filter(
    (date) => date !== undefined && date !== null
  );
  const entityPrices = entityData.data.stock_chart.prices.filter(
    (price) => price !== undefined && price !== null
  );

  // Calculate cumulative returns for entity
  const entityReturns = calculateCumulativeReturns(entityPrices);

  // Ensure entity dates and prices lengths match
  if (entityDates.length !== entityPrices.length) {
    return <p>Entity data mismatch: dates and prices lengths do not match</p>;
  }

  // Handle empty entity data
  if (!entityDates.length || !entityPrices.length) {
    return <p>No valid entity data available for the chart</p>;
  }

  // Convert entity dates to proper format
  const processedEntityDates = entityDates.map((date) => {
    if (typeof date === "string") {
      return new Date(date);
    }
    return date;
  });

  // Process IRX data if available
  let irxReturns = [];
  let processedIrxDates = [];

  if (irxData && irxData.data && irxData.data.stock_chart) {
    const irxDatesRaw = irxData.data.stock_chart.dates.filter(
      (date) => date !== undefined && date !== null
    );
    const irxPricesRaw = irxData.data.stock_chart.prices.filter(
      (price) => price !== undefined && price !== null
    );

    if (irxDatesRaw.length === irxPricesRaw.length && irxDatesRaw.length > 0) {
      processedIrxDates = irxDatesRaw.map((date) => {
        if (typeof date === "string") {
          return new Date(date);
        }
        return date;
      });

      // Calculate cumulative returns for IRX
      irxReturns = calculateCumulativeReturns(irxPricesRaw);

      // Align IRX data with entity data dates if needed
      const minLength = Math.min(
        processedEntityDates.length,
        processedIrxDates.length
      );
      if (irxReturns.length > minLength) {
        irxReturns = irxReturns.slice(0, minLength);
      }
    }
  }

  // Prepare series data
  const seriesData = [
    {
      data: entityReturns,
      label: `${entityData.data.name} Cumulative Return (%)`,
      color: "#8884d8",
      showMark: false,
    },
  ];

  // Add IRX data if available
  if (irxReturns.length > 0) {
    seriesData.push({
      data: irxReturns,
      label: "13 Week Treasury Bill Cumulative Return (%)",
      color: "#82ca9d",
      showMark: false,
    });
  }

  // Filter news based on search term
  const filteredNews = newsData.filter(
    (news) =>
      news.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      news.summary.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle search term change
  const handleSearchChange = (term) => {
    console.log("Search Term:", term); // Check the updated search term
    setSearchTerm(term); // Update search term in the parent component
  };

  // Handle pagination
  const handlePageChange = (event, pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  const profiles = [
    { label: "Symbol", value: data.data.ticker },
    { label: "Name", value: data.data.name },
    { label: "Asset Type", value: data.data["asset_type"] ?? "-" },
    { label: "Description", value: data.data.summary ?? "-" },
    { label: "Sector", value: data.data.sector ?? "-" },
  ];

  const sentimentTypes = {
    AvgSentiment: data ? parseFloat(data.data.sentiment_score).toFixed(1) : 0,
    simpleAverage: data ? parseFloat(data.data.simple_average).toFixed(1) : 0,
    TimeDecay: data ? parseFloat(data.data.time_decay).toFixed(1) : 0,
  };

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
    <Box sx={{ display: "flex", px: 4 }}>
      <Box sx={{ flex: 1, p: 2 }}>
        {/* Header spanning full width */}
        <Box sx={{ width: "100%", my: 1 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              px: 3,
              bgcolor: "white",
            }}
          >
            {/* Entity & Price */}
            <Stack>
              <Typography variant="h5">{EntityTicker ?? "N/A"}</Typography>
              <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
                <EntityPrice id={stockID} />
                <CustomChip value={performanceChange} showArrow={true} />
              </Stack>
            </Stack>

          </Box>
          <Divider sx={{ mt: 2, mb: 3 }} />
        </Box>

        {/* Main Content + News vs Sidebar */}
        <Stack direction="row" sx={{ width: "100%" }}>
          {/* LEFT: Chart + News */}
          <Stack direction="column" sx={{ flex: 3 }} spacing={4}>
            {/* Chart Section */}
            <Container>
              <Box
                sx={{
                  maxWidth: 900,
                  mx: "auto",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "start",
                  gap: 2,
                }}
              >
                <Stack
                  direction="row"
                  alignItems="center"
                  justifyContent="space-between"
                  sx={{ mt: 2, width: "100%" }}
                >
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    Cumulative Returns
                  </Typography>

                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "flex-end",
                    }}
                  >
                    <ToggleButtonGroup
                      value={timeRange}
                      exclusive
                      onChange={handleTimeRangeChange}
                      aria-label="time range selection"
                      size="small"
                      sx={{
                        "& .MuiToggleButton-root": {
                          px: 2,
                          py: 0.5,
                          fontSize: "0.875rem",
                          fontWeight: 600,
                          color: "#666",
                          "&.Mui-selected": {
                            bgcolor: "#8884d8",
                            color: "white",
                            "&:hover": { bgcolor: "#7c7bd8" },
                          },
                          "&:hover": { bgcolor: "#f5f5f5" },
                        },
                      }}
                    >
                      {timeRanges.map((range) => (
                        <ToggleButton key={range.value} value={range.value}>
                          {range.label}
                        </ToggleButton>
                      ))}
                    </ToggleButtonGroup>
                  </Box>
                </Stack>

                {/* Line Chart */}
                <Stack
                  direction="row"
                  alignItems="start"
                  sx={{ mt: 1, width: "100%" }}
                >
                  <Stack direction="column" spacing={3} sx={{ width: "100%" }}>
                    <LineChart
                      height={400}
                      xAxis={[
                        {
                          data: processedEntityDates,
                          label: "Date",
                          scaleType: "time",
                        },
                      ]}
                      series={seriesData}
                    >
                      {/* Add horizontal origin line */}
                      <ChartsReferenceLine y={0} />
                    </LineChart>
                  </Stack>
                </Stack>
              </Box>
            </Container>

            {/* News Section */}

            <Container>
              <Stack
                direction="row"
                alignItems="center"
                justifyContent="space-between"
                sx={{ mt: 2 }}
              >
                <Typography variant="h6">In the news</Typography>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  <MuiLink
                    component={Link}
                    to={ROUTES.NEWS}
                    underline="hover"
                    sx={{
                      color: "text.primary", // uses theme's default text color (black/dark gray)
                      "&:hover": { color: "text.secondary" }, // subtle hover effect
                      gap: 10,
                    }}
                  >
                    View More
                    <ArrowForwardIcon />
                  </MuiLink>
                </Typography>
              </Stack>
              <Divider sx={{ mt: 1, mb: 1 }} />
              <TableContainer component={Paper} elevation={0}>
                <Table size="small">
                  <TableBody>
                    {currentNews.map((news, i) => (
                      <TableRow key={i} hover>
                        <TableCell
                          sx={{
                            height: "100px", // 🔹 fixed width
                            maxHeight: "100px",
                            whiteSpace: "normal", // allow wrapping
                            wordWrap: "break-word",
                          }}
                        >
                          <MuiLink
                            component={Link}
                            to={ROUTES.INDIVIDUAL_NEWS}
                            state={{ id: news.id, title: news.title }}
                            sx={{
                              display: "block",
                              textDecoration: "none",
                              color: "inherit",
                              "&:hover": { textDecoration: "none" },
                            }}
                            onClick={() => {
                              setSelectedNews(news);
                              console.log("Selected News:", news);
                            }}
                          >
                            <Stack direction="column" spacing={0.5}>
                              <Typography
                                variant="body2"
                                sx={{
                                  fontWeight: "bold",
                                  color: "text.secondary",
                                }}
                              >
                                {news.publisher} |{" "}
                                {new Date(
                                  news.published_date
                                ).toLocaleDateString("en-US", {
                                  year: "numeric",
                                  month: "short",
                                  day: "numeric",
                                })}
                              </Typography>
                              <Typography
                                variant="subtitle1"
                                sx={{ color: "text.primary" }}
                              >
                                {news.title}
                              </Typography>
                            </Stack>
                          </MuiLink>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Pagination */}
              {totalPages > 1 && (
                <Grid container justifyContent="center" sx={{ mt: 4, mb: 4 }}>
                  <Grid size={{ xs: 12, md: 8, lg: 6 }}>
                    <Pagination
                      count={totalPages}
                      page={currentPage}
                      onChange={handlePageChange}
                      shape="rounded"
                      showFirstButton
                      showLastButton
                      siblingCount={2}
                      boundaryCount={1}
                      sx={{
                        display: "flex",
                        justifyContent: "center",
                        "& .MuiPagination-ul": {
                          justifyContent: "center",
                          flexWrap: "nowrap",
                        },
                        "& .MuiPaginationItem-root.Mui-selected": {
                          backgroundColor: "#212121",
                          color: "#fff",
                        },
                      }}
                    />
                  </Grid>
                </Grid>
              )}
            </Container>
          </Stack>

          {/* Divider between Left & Right */}
          <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />

          {/* RIGHT: Sidebar */}
          <Stack direction="column" sx={{ flex: 1.2, maxWidth: 400 }}>
            <Box sx={{ p: 2, mb: 3 }}>
              {/* Sentiment Scores */}
              <Typography variant="h5" sx={{ mb: 2 }}>
                Sentiment Scores
              </Typography>
              <Grid container spacing={1} alignItems="center" sx={{ mb: 4 }}>
                {[
                  {
                    label: `Weighted Sentiment: ${sentimentTypes.AvgSentiment}`,
                    tooltip:
                      "Weighted combination of multiple NLP models' sentiment predictions with confidence factored in.",
                    value: sentimentTypes.AvgSentiment,
                  },
                  {
                    label: `Simple Average: ${sentimentTypes.simpleAverage}`,
                    tooltip:
                      "Direct average of all article sentiment scores without weighting or adjustments.",
                    value: sentimentTypes.simpleAverage,
                  },
                  {
                    label: `Time Decay: ${sentimentTypes.TimeDecay}`,
                    tooltip:
                      "Recent articles weighted more heavily than older ones to reflect current market sentiment.",
                    value: sentimentTypes.TimeDecay,
                  },
                ].map((chip, i) => (
                  <Grid item key={i}>
                    <Tooltip title={chip.tooltip} arrow>
                      <Chip
                        label={chip.label}
                        variant="outlined"
                        sx={{
                          fontSize: "0.8rem",
                          fontWeight: 500,
                          borderRadius: "8px",
                          borderColor: getColor(chip.value),
                          color: getColor(chip.value),
                          backgroundColor: "transparent",
                        }}
                      />
                    </Tooltip>
                  </Grid>
                ))}
              </Grid>

              {/* Company Profile */}
              <Typography variant="h5" sx={{ mt: 2 }}>
                About
              </Typography>
              <Divider sx={{ my: 1 }} />
              <TableContainer component={Paper} elevation={0}>
                <Table size="small">
                  <TableBody>
                    {profiles.map((profile, i) => (
                      <TableRow key={i}>
                        <TableCell sx={{ fontWeight: "bold", width: "40%" }}>
                          {profile.label}
                        </TableCell>
                        <TableCell>{profile.value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          </Stack>
        </Stack>
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

export default IndvEntity;
