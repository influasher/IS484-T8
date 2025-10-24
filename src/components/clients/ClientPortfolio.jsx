import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Stack,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Card,
  CardContent,
  Divider,
  CircularProgress,
} from '@mui/material';
import { LineChart } from '@mui/x-charts/LineChart';
import { ChartsReferenceLine } from '@mui/x-charts/ChartsReferenceLine';
import { PieChart } from '@mui/x-charts/PieChart';
import ClientTransactionTable from './ClientTransactionTable';

const PortfolioDashboard = ({ clientId }) => {
  // Portfolio-related state
  const [timeRange, setTimeRange] = useState('1Y');
  const [portfolioData, setPortfolioData] = useState(null);
  const [transactionData, setTransactionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [transactionLoading, setTransactionLoading] = useState(true);
  const [irxData, setIrxData] = useState([]);

  const timeRanges = [
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '6M', value: '6M' },
    { label: '1Y', value: '1Y' },
    { label: '2Y', value: '2Y' },
    { label: '5Y', value: '5Y' },
  ];


  // Function to calculate portfolio metrics from transaction data
  const calculatePortfolioMetrics = (transactions) => {
    let totalDeposits = 0;
    let totalWithdrawals = 0;
    let totalPurchases = 0;
    let totalSales = 0;
    let totalDividends = 0;
    let totalCapitalGains = 0;
    let totalInterest = 0;

    transactions.forEach(transaction => {
      const amount = transaction.amount;

      switch (transaction.type.toLowerCase()) {
        case 'deposit':
          totalDeposits += amount;
          break;
        case 'withdrawal':
          totalWithdrawals += Math.abs(amount);
          break;
        case 'purchase':
        case 'buy':
          totalPurchases += Math.abs(amount);
          break;
        case 'sale':
        case 'sell':
          totalSales += amount;
          break;
        case 'dividend':
          totalDividends += amount;
          break;
        case 'capital gains':
          totalCapitalGains += amount;
          break;
        case 'interest':
          totalInterest += amount;
          break;
      }
    });

    const netCashInvested = totalDeposits - totalWithdrawals;
    const currentCashPosition = totalDeposits - totalWithdrawals - totalPurchases + totalSales + totalDividends + totalCapitalGains + totalInterest;
    const netSecuritiesInvestment = totalPurchases - totalSales;
    const estimatedSecuritiesValue = netSecuritiesInvestment * 1.15; // 15% estimated growth
    const estimatedTotalPortfolioValue = currentCashPosition + estimatedSecuritiesValue;
    const unrealizedPL = estimatedTotalPortfolioValue - netCashInvested;
    const unrealizedPLPercent = netCashInvested > 0 ? (unrealizedPL / netCashInvested) * 100 : 0;

    return {
      totalInvestment: netCashInvested,
      totalPortfolioValue: estimatedTotalPortfolioValue,
      unrealizedPL: unrealizedPL,
      unrealizedPLPercent: unrealizedPLPercent,
      breakdown: {
        totalDeposits,
        totalWithdrawals,
        totalPurchases,
        totalSales,
        totalDividends,
        totalCapitalGains,
        totalInterest,
        currentCashPosition,
        netSecuritiesInvestment,
        estimatedSecuritiesValue
      }
    };
  };

  // Function to fetch IRX data from real API
  const fetchIRXData = async (timeRange) => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
      const irxUrl = `${API_BASE_URL}/api/entities/ticker=^IRX/chart?period=${timeRange}`;

      console.log(`Fetching IRX data from: ${irxUrl}`);
      const response = await fetch(irxUrl);

      if (!response.ok) {
        console.error('IRX API error - Status:', response.status);
        const errorText = await response.text();
        console.error('IRX API error - Response:', errorText);
        return [];
      }

      const result = await response.json();
      console.log("Raw IRX API response:", result);

      // Extract dates and prices from the API response
      const dates = result.data?.stock_chart?.dates || [];
      const prices = result.data?.stock_chart?.prices || [];

      if (dates.length === 0 || prices.length === 0) {
        console.warn("No IRX data available");
        return [];
      }

      // Convert to the format we need
      const irxData = dates.map((dateStr, index) => ({
        date: new Date(dateStr),
        value: prices[index] || 0
      }));

      console.log("Processed IRX data:", irxData);
      return irxData;

    } catch (error) {
      console.error('Error fetching IRX data:', error);
      return [];
    }
  };

  // Function to calculate percentage change from the first value
  const calculatePercentageChange = (performanceData) => {
    if (!performanceData || performanceData.length === 0) {
      return [];
    }

    // Sort data by date (ascending)
    const sortedData = [...performanceData].sort((a, b) => new Date(a.date) - new Date(b.date));

    if (sortedData.length === 0) {
      return [];
    }

    const baseValue = sortedData[0].value;

    return sortedData.map(item => ({
      date: item.date,
      value: baseValue === 0 ? 0 : ((item.value - baseValue) / baseValue) * 100
    }));
  };


  // Function to filter performance data based on time range
  const filterPerformanceByTimeRange = (performanceData, timeRange) => {
    if (!performanceData || performanceData.length === 0) {
      return [];
    }

    // Sort data by date to ensure we have the latest data first
    const sortedData = [...performanceData].sort((a, b) => new Date(b.date) - new Date(a.date));

    // Find the most recent date in the data
    const latestDate = new Date(sortedData[0].date);

    let monthsBack;
    switch (timeRange) {
      case '1M':
        monthsBack = 1;
        break;
      case '3M':
        monthsBack = 3;
        break;
      case '6M':
        monthsBack = 6;
        break;
      case '1Y':
        monthsBack = 12;
        break;
      case '2Y':
        monthsBack = 24;
        break;
      case '5Y':
        monthsBack = 60;
        break;
      default:
        return performanceData; // Return all data if unknown time range
    }

    // Calculate start date based on the latest data point
    const startDate = new Date(latestDate.getFullYear(), latestDate.getMonth() - monthsBack, latestDate.getDate());

    console.log(`Filtering for ${timeRange}: Latest data date=${latestDate}, Start date=${startDate}`);

    const filtered = performanceData.filter(item => {
      const itemDate = new Date(item.date);
      return itemDate >= startDate;
    });

    console.log(`Filtered ${performanceData.length} items to ${filtered.length} items`);
    return filtered;
  };

  const fetchPortfolioData = async (transactions, period = '1Y') => {
    setLoading(true);
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";

      // Fetch portfolio allocation
      const portfolioResponse = await fetch(`${API_BASE_URL}/api/portfolio/${clientId}`);
      const portfolioResult = portfolioResponse.ok ? await portfolioResponse.json() : null;

      // Fetch performance history
      console.log(`Fetching performance data from: ${API_BASE_URL}/api/performance/${clientId}`);
      const performanceResponse = await fetch(`${API_BASE_URL}/api/portfolio/performance/${clientId}`);
      console.log('Performance response status:', performanceResponse.status);
      console.log('Performance response ok:', performanceResponse.ok);

      let performanceResult = null;
      if (performanceResponse.ok) {
        performanceResult = await performanceResponse.json();
        console.log("Successfully fetched performance data:", performanceResult);
      } else {
        console.error('Performance API error - Status:', performanceResponse.status);
        const errorText = await performanceResponse.text();
        console.error('Performance API error - Response:', errorText);
      }


      const calculatedMetrics = calculatePortfolioMetrics(transactions);

      // Use only real API data
      console.log("Portfolio result:", portfolioResult);
      console.log("Performance result:", performanceResult);

      const allocation = portfolioResult?.allocation || [];
      console.log("Processed allocation:", allocation);

      // Check the structure of performance data
      console.log("Performance result structure:", performanceResult);
      console.log("Performance result.performance:", performanceResult?.performance);

      const rawPerformance = performanceResult?.performance?.map(p => ({
        date: new Date(p.date),
        value: p.value
      })) || [];
      console.log("Raw performance data after mapping:", rawPerformance);

      // Filter performance data based on selected time range
      const filteredPerformance = filterPerformanceByTimeRange(rawPerformance, period);
      console.log("Filtered performance data:", filteredPerformance);

      // Convert to percentage change
      const percentagePerformance = calculatePercentageChange(filteredPerformance);
      console.log("Percentage performance data:", percentagePerformance);

      // Fetch real IRX data for the same time period
      const rawIrxData = await fetchIRXData(period);

      // Filter IRX data to match the same time range
      const filteredIrxData = filterPerformanceByTimeRange(rawIrxData, period);

      // Convert IRX to percentage change (starting from 0)
      const irxPerformance = calculatePercentageChange(filteredIrxData);
      console.log("IRX performance data:", irxPerformance);

      const portfolioDataWithCalculatedMetrics = {
        metrics: calculatedMetrics,
        allocation: allocation,
        performance: percentagePerformance,
        irxPerformance: irxPerformance
      };
      console.log("Final portfolio data being set:", portfolioDataWithCalculatedMetrics)

      setPortfolioData(portfolioDataWithCalculatedMetrics);
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
      // Set empty data on error
      const calculatedMetrics = calculatePortfolioMetrics(transactions);
      setPortfolioData({
        allocation: [],
        performance: [],
        irxPerformance: [],
        metrics: calculatedMetrics
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactionData = async () => {
    setTransactionLoading(true);
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
      console.log(`Fetching transactions for client: ${clientId}`);
      const response = await fetch(`${API_BASE_URL}/api/transactions/client/${clientId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error('Failed to fetch transactions');
      }

      const result = await response.json();
      console.log('Fetched transactions:', result);

      // Transform the data to match the expected format
      const formattedTransactions = result.transactions.map(txn => ({
        id: txn.txn_uuid,
        dateTime: txn.datetime,
        source: txn.source,
        type: txn.type,
        currency: txn.currency,
        amount: txn.amount,
        price_per_share: txn.price_per_share,
        quantity: txn.quantity,
        description: txn.desc
      }));

      setTransactionData(formattedTransactions);

      // Update portfolio data with real transactions
      fetchPortfolioData(formattedTransactions, timeRange);
    } catch (error) {
      console.error('Error fetching transaction data:', error);
      setTransactionData([]);
      // Create portfolio with empty transactions
      fetchPortfolioData([], timeRange);
    } finally {
      setTransactionLoading(false);
    }
  };

  const handleTimeRangeChange = (_, newTimeRange) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
      fetchPortfolioData(transactionData, newTimeRange);
    }
  };

  useEffect(() => {
    if (clientId) {
      fetchTransactionData();
    }
  }, [clientId]);

  // Loading state check for portfolio data
  if (loading || !portfolioData) {
    return (
      <Box sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading Portfolio...
        </Typography>
      </Box>
    );
  }

  const { performance, metrics, allocation, irxPerformance } = portfolioData;
  const totalAllocation = allocation?.reduce((sum, item) => sum + item.value, 0) || 0;

  // Prepare data for LineChart - handle empty performance data
  const dates = performance?.map(item => item.date) || [];
  const portfolioValues = performance?.map(item => item.value) || [];
  let irxValues = irxPerformance?.map(item => item.value) || [];

  // Align IRX data with portfolio data length to avoid mismatched arrays
  if (irxValues.length > portfolioValues.length && portfolioValues.length > 0) {
    console.log(`Trimming IRX data from ${irxValues.length} to ${portfolioValues.length} items`);
    irxValues = irxValues.slice(0, portfolioValues.length);
  }

  console.log(`Data alignment check: Portfolio=${portfolioValues.length}, IRX=${irxValues.length}, Dates=${dates.length}`);

  // Calculate y-axis domain based on actual data range
  const calculateYAxisDomain = (portfolioData, irxData) => {
    if (!portfolioData?.length && !irxData?.length) {
      console.log("No data available, using default domain");
      return [-10, 10];
    }

    // Filter out any invalid values (NaN, Infinity, etc.)
    const validPortfolioValues = (portfolioData || []).filter(val =>
      typeof val === 'number' && isFinite(val)
    );
    const validIrxValues = (irxData || []).filter(val =>
      typeof val === 'number' && isFinite(val)
    );

    const allValues = [...validPortfolioValues, ...validIrxValues];

    if (allValues.length === 0) {
      console.log("No valid values found, using default domain");
      return [-10, 10];
    }

    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);

    console.log(`Y-axis calculation: Portfolio values range ${Math.min(...validPortfolioValues)} to ${Math.max(...validPortfolioValues)}`);
    console.log(`Y-axis calculation: IRX values range ${Math.min(...validIrxValues)} to ${Math.max(...validIrxValues)}`);
    console.log(`Y-axis calculation: Overall min=${minValue}, max=${maxValue}`);

    // Add padding to the range
    const range = maxValue - minValue;
    const padding = Math.max(range * 0.15, 2); // 15% padding, minimum 2%

    const domain = [
      Math.floor(minValue - padding),
      Math.ceil(maxValue + padding)
    ];

    console.log(`Y-axis domain calculated: [${domain[0]}, ${domain[1]}]`);
    return domain;
  };

  const yAxisDomain = calculateYAxisDomain(portfolioValues, irxValues);

  // Log final data for debugging
  // console.log("=== CHART DATA DEBUG ===");
  // console.log("Portfolio values:", portfolioValues);
  // console.log("IRX values:", irxValues);
  // console.log("Portfolio min/max:", Math.min(...portfolioValues), Math.max(...portfolioValues));
  // console.log("IRX min/max:", Math.min(...irxValues), Math.max(...irxValues));
  // console.log("Final Y-axis domain:", yAxisDomain);
  // console.log("Y-axis config will be:", {
  //   label: "Percentage Change (%)",
  //   min: yAxisDomain[0],
  //   max: yAxisDomain[1],
  //   domain: yAxisDomain
  // });
  // console.log("=== END CHART DEBUG ===");

  // Check if we have performance data to display
  const hasPerformanceData = performance && performance.length > 0;
  const hasAllocationData = allocation && allocation.length > 0;

  return (
    <Box sx={{ display: "flex", px: { xs: 1, sm: 2, md: 4 }, width: "100%"}}>
      <Box sx={{ flex: 1, p: { xs: 1, sm: 2 } }}>
        <Stack
          direction={{ xs: "column", lg: "row" }}
          sx={{ width: "100%" }}
          spacing={{ xs: 4, lg: 0 }}
        >
          {/* LEFT: Portfolio Performance Chart */}
          <Stack direction="column" sx={{ flex: 3 }} spacing={4}>
            <Container sx={{ px: { xs: 0, sm: 2 } }}>
              <Box
                sx={{
                  maxWidth: { xs: "100%", lg: 900 },
                  mx: "auto",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "start",
                  gap: 2,
                }}
              >
                <Stack
                  direction={{ xs: "column", sm: "row" }}
                  alignItems={{ xs: "start", sm: "center" }}
                  justifyContent="space-between"
                  sx={{ mt: 2, width: "100%", gap: 2 }}
                >
                  <Typography variant="h5" sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem" }, fontWeight: 700 }}>
                    Portfolio Performance
                  </Typography>

                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: { xs: "flex-start", sm: "flex-end" },
                      width: { xs: "100%", sm: "auto" },
                      overflowX: "auto",
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
                  sx={{ mt: 1, width: "100%", overflowX: "auto" }}
                >
                  <Stack direction="column" spacing={3} sx={{ width: "100%", minWidth: { xs: 300, sm: "100%" } }}>
                    {hasPerformanceData ? (
                      <LineChart
                        height={400}
                        xAxis={[
                          {
                            data: dates,
                            label: "Date",
                            scaleType: "time",
                          },
                        ]}
                        series={[
                          {
                            data: portfolioValues,
                            label: "Portfolio Performance (%)",
                            color: "#8884d8",
                            showMark: false,
                          },
                          {
                            data: irxValues,
                            label: "IRX Benchmark (%)",
                            color: "#82ca9d",
                            showMark: false,
                          }
                        ]}
                        yAxis={[
                          {
                            label: "Percentage Change (%)",
                            scaleType: "linear",
                            domain: yAxisDomain
                          }
                        ]}
                        margin={{ left: 80, right: 20, top: 20, bottom: 60 }}
                      >
                        {/* Add horizontal origin line */}
                        <ChartsReferenceLine y={0} />
                      </LineChart>
                    ) : (
                      <Box
                        sx={{
                          height: 400,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: '1px dashed #ccc',
                          borderRadius: 1
                        }}
                      >
                        <Typography variant="body1" color="text.secondary">
                          No performance data available for selected time range
                        </Typography>
                      </Box>
                    )}

                    {/* Portfolio Metrics */}
                    <Stack
                      direction={{ xs: "column", sm: "row" }}
                      spacing={{ xs: 2, sm: 4 }}
                      sx={{ mt: 2 }}
                    >
                      <Box>
                        <Typography
                          variant="h4"
                          sx={{
                            fontSize: { xs: "1.25rem", sm: "1.5rem", md: "1.75rem" }
                          }}
                        >
                          ${metrics.totalInvestment.toFixed(2).toLocaleString()} USD
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: "text.secondary",
                            mt: 0.5,
                            fontSize: { xs: "0.75rem", sm: "0.875rem" }
                          }}
                        >
                          Total Investment Amount
                        </Typography>
                      </Box>

                      <Box>
                        <Typography
                          variant="h4"
                          sx={{
                            fontSize: { xs: "1.25rem", sm: "1.5rem", md: "1.75rem" }
                          }}
                        >
                          ${metrics.totalPortfolioValue.toFixed(2).toLocaleString()} USD
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: "text.secondary",
                            mt: 0.5,
                            fontSize: { xs: "0.75rem", sm: "0.875rem" }
                          }}
                        >
                          Total Portfolio Value
                        </Typography>
                      </Box>
                    </Stack>

                    <Box>
                      <Typography
                        variant="h6"
                        sx={{
                          color:  metrics.unrealizedPL >= 0 ? "green" : 'red',
                          fontSize: { xs: "1rem", sm: "1.25rem" }
                        }}
                      >
                        {metrics.unrealizedPL >= 0 ? '+' : ''}{metrics.unrealizedPL.toFixed(2)} ({metrics.unrealizedPLPercent >= 0 ? '+' : ''}{metrics.unrealizedPLPercent.toFixed(2)}%)
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: "text.secondary",
                          mt: 0.5,
                          fontSize: { xs: "0.75rem", sm: "0.875rem" }
                        }}
                      >
                        Total unrealised profit/loss (P/L)
                      </Typography>
                    </Box>
                  </Stack>
                </Stack>
              </Box>
            </Container>
          </Stack>

          {/* Divider between Left & Right */}
          <Divider
            orientation={{ xs: "horizontal", lg: "vertical" }}
            flexItem
            sx={{ mx: { xs: 0, lg: 2 }, my: { xs: 2, lg: 0 } }}
          />

          {/* RIGHT: Product Allocation */}
          <Stack
            direction="column"
            sx={{
              flex: { xs: 1, lg: 1.2 },
              maxWidth: { xs: "100%", lg: 400 },
              width: "100%"
            }}
          >
            <Box sx={{ p: { xs: 1, sm: 2 } }}>
              <Typography
                variant="h5"
                sx={{
                  mb: 2,
                  fontSize: { xs: "1.25rem", sm: "1.5rem" }
                }}
              >
                Product Allocation
              </Typography>

              <Box>
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  {hasAllocationData ? (
                    <Box sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      position: 'relative'
                    }}>
                      <Box sx={{ position: 'relative', display: 'inline-block' }}>
                        <PieChart
                          series={[
                            {
                              data: allocation,
                              innerRadius: 60,
                              outerRadius: 100,
                              paddingAngle: 2,
                              cornerRadius: 4,
                            },
                          ]}
                          height={250}
                          width={300}
                          margin={{ right: 5 }}
                          slotProps={{
                            legend: { hidden: true }
                          }}
                        />

                        {/* Center Total */}
                        <Typography
                          variant="h3"
                          sx={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            color: 'text.primary',
                            pointerEvents: 'none',
                            fontSize: { xs: "2rem", sm: "3rem" }
                          }}
                        >
                          {totalAllocation}
                        </Typography>
                      </Box>

                      {/* Legend */}
                      <Stack spacing={1} sx={{ mt: 3, width: '100%' }}>
                        {allocation.map((item, index) => (
                          <Stack
                            key={index}
                            direction="row"
                            alignItems="center"
                            justifyContent="space-between"
                            sx={{ px: 1 }}
                          >
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <Box
                                sx={{
                                  width: { xs: 10, sm: 12 },
                                  height: { xs: 10, sm: 12 },
                                  borderRadius: '50%',
                                  bgcolor: item.color,
                                }}
                              />
                              <Typography
                                variant="body2"
                                sx={{
                                  color: 'text.secondary',
                                  fontSize: { xs: "0.75rem", sm: "0.875rem" }
                                }}
                              >
                                {item.name}
                              </Typography>
                            </Stack>
                            <Typography
                              variant="body2"
                              sx={{
                                color: 'text.primary',
                                fontSize: { xs: "0.75rem", sm: "0.875rem" }
                              }}
                            >
                              {item.value}
                            </Typography>
                          </Stack>
                        ))}
                      </Stack>
                    </Box>
                  ) : (
                    <Box
                      sx={{
                        height: 250,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '1px dashed #ccc',
                        borderRadius: 1
                      }}
                    >
                      <Typography variant="body1" color="text.secondary">
                        No allocation data available
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Box>
            </Box>
          </Stack>
        </Stack>

        <hr />

        {/* Transaction Table Component */}
        <ClientTransactionTable
          transactionData={transactionData}
          loading={transactionLoading}
        />
      </Box>
    </Box>
  );
};

export default PortfolioDashboard;