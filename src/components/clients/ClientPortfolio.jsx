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
import { PieChart } from '@mui/x-charts/PieChart';
import ClientTransactionTable from './ClientTransactionTable';

const PortfolioDashboard = ({ clientId }) => {
  // Portfolio-related state
  const [timeRange, setTimeRange] = useState('1Y');
  const [portfolioData, setPortfolioData] = useState(null);
  const [transactionData, setTransactionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [transactionLoading, setTransactionLoading] = useState(true);

  const timeRanges = [
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '6M', value: '6M' },
    { label: '1Y', value: '1Y' },
    { label: '2Y', value: '2Y' },
    { label: '5Y', value: '5Y' },
  ];

  // Mock portfolio data - replace with actual API calls
  const mockPortfolioData = {
    performance: [
      { date: new Date('2014-01-01'), value: 1000 },
      { date: new Date('2015-01-01'), value: 6500 },
      { date: new Date('2016-01-01'), value: 5800 },
      { date: new Date('2017-01-01'), value: 6200 },
      { date: new Date('2018-01-01'), value: 4200 },
      { date: new Date('2019-01-01'), value: 5000 },
      { date: new Date('2020-01-01'), value: 6500 },
      { date: new Date('2021-01-01'), value: 6800 },
      { date: new Date('2022-01-01'), value: 8000 },
    ],
    allocation: [
      { name: 'AAPL', value: 80, color: '#6366f1' },
      { name: 'HSBC', value: 41, color: '#10b981' },
      { name: 'TSMC', value: 35, color: '#f59e0b' },
    ]
  };

  

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
    const totalInvestmentAmount = totalPurchases;
    const currentCashPosition = totalDeposits - totalWithdrawals - totalPurchases + totalSales + totalDividends + totalCapitalGains + totalInterest;
    const netSecuritiesInvestment = totalPurchases - totalSales;
    const estimatedSecuritiesValue = netSecuritiesInvestment * 1.15; // 15% estimated growth
    const estimatedTotalPortfolioValue = currentCashPosition + estimatedSecuritiesValue;
    const totalRealizedGains = totalSales + totalDividends + totalCapitalGains + totalInterest - (totalPurchases - netSecuritiesInvestment);
    const unrealizedPL = estimatedTotalPortfolioValue - netCashInvested;
    const unrealizedPLPercent = netCashInvested > 0 ? (unrealizedPL / netCashInvested) * 100 : 0;

    return {
      totalInvestment: netCashInvested,
      totalMarketValue: estimatedTotalPortfolioValue,
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

  const fetchPortfolioData = async (transactions, period = '1Y') => {
    setLoading(true);
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";

      // Fetch portfolio allocation
      const portfolioResponse = await fetch(`${API_BASE_URL}/portfolio/${clientId}`);
      const portfolioResult = portfolioResponse.ok ? await portfolioResponse.json() : null;

      // Fetch performance history
      const performanceResponse = await fetch(`${API_BASE_URL}/performance/${clientId}`);
      const performanceResult = performanceResponse.ok ? await performanceResponse.json() : null;

      const calculatedMetrics = calculatePortfolioMetrics(transactions);

      // Use fetched data if available, otherwise fall back to mock data
      const allocation = portfolioResult?.allocation?.length > 0
        ? portfolioResult.allocation
        : mockPortfolioData.allocation;

      const performance = performanceResult?.performance?.length > 0
        ? performanceResult.performance.map(p => ({
            date: new Date(p.date),
            value: p.value
          }))
        : mockPortfolioData.performance;

      const portfolioDataWithCalculatedMetrics = {
        metrics: calculatedMetrics,
        allocation: allocation,
        performance: performance
      };

      setPortfolioData(portfolioDataWithCalculatedMetrics);
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
      // Fall back to mock data on error
      const calculatedMetrics = calculatePortfolioMetrics(transactions);
      setPortfolioData({
        ...mockPortfolioData,
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
      const response = await fetch(`${API_BASE_URL}/transactions/client/${clientId}`, {
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
        status: "Completed", // You may need to add status field to your DB
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

  const handleTimeRangeChange = (event, newTimeRange) => {
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

  const { performance, metrics, allocation } = portfolioData;
  const totalAllocation = allocation.reduce((sum, item) => sum + item.value, 0);

  // Prepare data for LineChart
  const dates = performance.map(item => item.date);
  const values = performance.map(item => item.value);

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
                  <Typography variant="h5" sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem" } }}>
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
                          px: { xs: 1, sm: 2 },
                          py: 0.5,
                          fontSize: { xs: "0.75rem", sm: "0.875rem" },
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
                          data: values,
                          label: "Portfolio Value ($)",
                          showMark: false,
                        }
                      ]}
                      margin={{ left: 80, right: 20, top: 20, bottom: 60 }}
                    />

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
                          ${metrics.totalInvestment.toFixed(2).toLocaleString()} SGD
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
                          ${metrics.totalMarketValue.toFixed(2).toLocaleString()} SGD
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: "text.secondary",
                            mt: 0.5,
                            fontSize: { xs: "0.75rem", sm: "0.875rem" }
                          }}
                        >
                          Total Market Value
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
                        +{metrics.unrealizedPL.toFixed(2)} ({metrics.unrealizedPLPercent.toFixed(2)}%)
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