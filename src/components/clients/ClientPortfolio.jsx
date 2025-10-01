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

const PortfolioDashboard = () => {
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

  const mockTransactionData = [
    {
      "id": "txn_001",
      "dateTime": "2024-09-19T14:30:00Z",
      "source": "Chase Bank ****1234",
      "type": "Deposit",
      "currency": "USD",
      "amount": 5000.00,
      "status": "Completed",
      "description": "Initial funding"
    },
    {
      "id": "txn_002",
      "dateTime": "2024-09-19T14:35:00Z",
      "source": "AAPL",
      "type": "Purchase",
      "currency": "USD",
      "amount": -2500.00,
      "status": "Completed",
      "description": "Apple Inc. - 15 shares @ $166.67"
    },
    {
      "id": "txn_003",
      "dateTime": "2024-09-18T16:00:00Z",
      "source": "KO",
      "type": "Dividend",
      "currency": "USD",
      "amount": 45.50,
      "status": "Completed",
      "description": "The Coca-Cola Company quarterly dividend"
    },
    {
      "id": "txn_004",
      "dateTime": "2024-09-18T11:20:00Z",
      "source": "Wells Fargo ****5678",
      "type": "Deposit",
      "currency": "USD",
      "amount": 1200.00,
      "status": "Completed",
      "description": "Monthly investment contribution"
    },
    {
      "id": "txn_005",
      "dateTime": "2024-09-17T09:15:00Z",
      "source": "MSFT",
      "type": "Sale",
      "currency": "USD",
      "amount": 3250.75,
      "status": "Completed",
      "description": "Microsoft Corp. - 8 shares @ $406.34"
    },
    {
      "id": "txn_006",
      "dateTime": "2024-09-17T14:45:00Z",
      "source": "Bank Transfer",
      "type": "Withdrawal",
      "currency": "USD",
      "amount": -800.00,
      "status": "Completed",
      "description": "Transfer to savings account"
    },
    {
      "id": "txn_007",
      "dateTime": "2024-09-16T10:30:00Z",
      "source": "VOO",
      "type": "Purchase",
      "currency": "USD",
      "amount": -1500.00,
      "status": "Completed",
      "description": "Vanguard S&P 500 ETF - 3.2 shares @ $468.75"
    },
    {
      "id": "txn_008",
      "dateTime": "2024-09-15T13:22:00Z",
      "source": "AMZN",
      "type": "Capital Gains",
      "currency": "USD",
      "amount": 125.80,
      "status": "Completed",
      "description": "Amazon.com Inc. - Long term capital gains distribution"
    },
    {
      "id": "txn_009",
      "dateTime": "2024-09-14T16:00:00Z",
      "source": "Bank of America ****9012",
      "type": "Deposit",
      "currency": "USD",
      "amount": 500.00,
      "status": "Processing",
      "description": "ACH transfer"
    },
    {
      "id": "txn_010",
      "dateTime": "2024-09-13T11:45:00Z",
      "source": "GOOGL",
      "type": "Purchase",
      "currency": "USD",
      "amount": -2100.50,
      "status": "Completed",
      "description": "Alphabet Inc. - 12 shares @ $175.04"
    },
    {
      "id": "txn_011",
      "dateTime": "2024-09-12T15:30:00Z",
      "source": "JNJ",
      "type": "Sale",
      "currency": "USD",
      "amount": 4250.00,
      "status": "Completed",
      "description": "Johnson & Johnson - 25 shares @ $170.00"
    },
    {
      "id": "txn_012",
      "dateTime": "2024-09-11T08:15:00Z",
      "source": "TD",
      "type": "Dividend",
      "currency": "USD",
      "amount": 67.20,
      "status": "Completed",
      "description": "Toronto-Dominion Bank quarterly dividend"
    },
    {
      "id": "txn_013",
      "dateTime": "2024-09-10T12:00:00Z",
      "source": "JPM",
      "type": "Dividend",
      "currency": "USD",
      "amount": 32.40,
      "status": "Completed",
      "description": "JPMorgan Chase & Co. quarterly dividend"
    },
    {
      "id": "txn_014",
      "dateTime": "2024-09-09T14:20:00Z",
      "source": "Bank Transfer",
      "type": "Withdrawal",
      "currency": "USD",
      "amount": -1000.00,
      "status": "Failed",
      "description": "Insufficient funds - withdrawal cancelled"
    },
    {
      "id": "txn_015",
      "dateTime": "2024-09-08T16:45:00Z",
      "source": "NVDA",
      "type": "Purchase",
      "currency": "USD",
      "amount": -3500.00,
      "status": "Completed",
      "description": "NVIDIA Corporation - 25 shares @ $140.00"
    },
    {
      "id": "txn_016",
      "dateTime": "2024-09-07T10:10:00Z",
      "source": "Interest",
      "type": "Interest",
      "currency": "USD",
      "amount": 15.75,
      "status": "Completed",
      "description": "Cash balance interest payment"
    },
    {
      "id": "txn_017",
      "dateTime": "2024-09-06T13:55:00Z",
      "source": "PG",
      "type": "Purchase",
      "currency": "USD",
      "amount": -1850.00,
      "status": "Completed",
      "description": "Procter & Gamble Co. - 12 shares @ $154.17"
    },
    {
      "id": "txn_018",
      "dateTime": "2024-09-05T09:30:00Z",
      "source": "Schwab Transfer",
      "type": "Deposit",
      "currency": "USD",
      "amount": 7500.00,
      "status": "Completed",
      "description": "ACATS transfer from Charles Schwab"
    },
    {
      "id": "txn_019",
      "dateTime": "2024-09-04T11:25:00Z",
      "source": "SPY",
      "type": "Capital Gains",
      "currency": "USD",
      "amount": 89.25,
      "status": "Completed",
      "description": "SPDR S&P 500 ETF Trust - Capital gains distribution"
    },
    {
      "id": "txn_020",
      "dateTime": "2024-09-03T15:40:00Z",
      "source": "Wire Transfer",
      "type": "Deposit",
      "currency": "USD",
      "amount": 10000.00,
      "status": "Pending",
      "description": "Incoming wire transfer"
    },
    {
      "id": "txn_021",
      "dateTime": "2024-09-02T13:15:00Z",
      "source": "VTI",
      "type": "Purchase",
      "currency": "USD",
      "amount": -2200.00,
      "status": "Completed",
      "description": "Vanguard Total Stock Market ETF - 8.5 shares @ $258.82"
    },
    {
      "id": "txn_022",
      "dateTime": "2024-09-01T10:45:00Z",
      "source": "DIS",
      "type": "Dividend",
      "currency": "USD",
      "amount": 28.60,
      "status": "Completed",
      "description": "The Walt Disney Company semi-annual dividend"
    },
    {
      "id": "txn_023",
      "dateTime": "2024-08-31T14:30:00Z",
      "source": "BRK.B",
      "type": "Purchase",
      "currency": "USD",
      "amount": -4325.00,
      "status": "Completed",
      "description": "Berkshire Hathaway Inc. - 10 shares @ $432.50"
    },
    {
      "id": "txn_024",
      "dateTime": "2024-08-30T11:20:00Z",
      "source": "T",
      "type": "Dividend",
      "currency": "USD",
      "amount": 73.50,
      "status": "Completed",
      "description": "AT&T Inc. quarterly dividend"
    },
    {
      "id": "txn_025",
      "dateTime": "2024-08-29T09:00:00Z",
      "source": "QQQ",
      "type": "Purchase",
      "currency": "USD",
      "amount": -1875.00,
      "status": "Completed",
      "description": "Invesco QQQ Trust ETF - 5 shares @ $375.00"
    }
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
          totalPurchases += Math.abs(amount);
          break;
        case 'sale':
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

  const fetchPortfolioData = async (period = '1Y') => {
    setLoading(true);
    try {
      const calculatedMetrics = calculatePortfolioMetrics(mockTransactionData);
      
      const portfolioDataWithCalculatedMetrics = {
        ...mockPortfolioData,
        metrics: calculatedMetrics,
        performance: mockPortfolioData.performance
      };
      
      await new Promise(resolve => setTimeout(resolve, 500));
      setPortfolioData(portfolioDataWithCalculatedMetrics);
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactionData = async () => {
    setTransactionLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 300)); // Simulate API delay
      setTransactionData(mockTransactionData);
    } catch (error) {
      console.log('Error fetching transaction data:', error);
    } finally {
      setTransactionLoading(false);
    }
  };

  const handleTimeRangeChange = (event, newTimeRange) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
      fetchPortfolioData(newTimeRange);
    }
  };

  useEffect(() => {
    fetchPortfolioData(timeRange);
    fetchTransactionData();
  }, []);

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