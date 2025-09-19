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
import { ChartsReferenceLine } from '@mui/x-charts/ChartsReferenceLine';

const PortfolioDashboard = () => {
  const [timeRange, setTimeRange] = useState('1Y');
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Hard coded data - client portfolio with allocation details
  const client_portfolio = [
    { name: 'AAPL', value: 80, color: '#6366f1' },
    { name: 'HSBC', value: 41, color: '#10b981' },
    { name: 'TSMC', value: 35, color: '#f59e0b' },
  ];

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
    metrics: {
      totalInvestment: 12056.36,
      totalMarketValue: 13982.35,
      unrealizedPL: 47.59,
      unrealizedPLPercent: 3.28,
    },
    allocation: client_portfolio
  };

  const handleTimeRangeChange = (event, newTimeRange) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
      // Here you would typically fetch new data based on the time range
      fetchPortfolioData(newTimeRange);
    }
  };

  const fetchPortfolioData = async (period = '1Y') => {
    setLoading(true);
    try {
      // Mock API call - replace with actual implementation
      // Example API calls you could make:
      // const promises = client_portfolio.map(stock => 
      //   fetch(`/api/entities/ticker=${stock.name}/chart?period=${period}`)
      // );
      // const responses = await Promise.all(promises);
      
      // For now, using mock data
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
      setPortfolioData(mockPortfolioData);
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolioData(timeRange);
  }, []);

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
          Loading...
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
    <Box sx={{ display: "flex", px: 4 }}>
      <Box sx={{ flex: 1, p: 2 }}>
        <Stack direction="row" sx={{ width: "100%" }}>
          {/* LEFT: Portfolio Performance Chart */}
          <Stack direction="column" sx={{ flex: 3 }} spacing={4}>
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
                  <Typography variant="h5">
                    Portfolio Performance
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
                    >
                      {/* <ChartsReferenceLine y={0} /> */}
                    </LineChart>

                    {/* Portfolio Metrics */}
                    <Stack direction="row" spacing={4} sx={{ mt: 2 }}>
                      <Box>
                        <Typography 
                          variant="h4" 
                          sx={{ 
                            color: "#10b981",
                            fontSize: "1.75rem" 
                          }}
                        >
                          ${metrics.totalInvestment.toLocaleString()} SGD
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: "text.secondary", 
                            mt: 0.5 
                          }}
                        >
                          Total Investment Amount
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography 
                          variant="h4" 
                          sx={{ 
                            fontSize: "1.75rem" 
                          }}
                        >
                          ${metrics.totalMarketValue.toLocaleString()} SGD
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: "text.secondary", 
                            mt: 0.5 
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
                          color: "#10b981",
                          fontSize: "1.25rem" 
                        }}
                      >
                        +{metrics.unrealizedPL} ({metrics.unrealizedPLPercent}%)
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          color: "text.secondary", 
                          mt: 0.5 
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
          <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />

          {/* RIGHT: Product Allocation */}
          <Stack direction="column" sx={{ flex: 1.2, maxWidth: 400 }}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h5" sx={{ mb: 2}}>
                Product Allocation
              </Typography>
              
              <Card 
                sx={{ 
                  borderRadius: 2,
                  boxShadow: 1,
                  bgcolor: "background.paper"
                }}
              >
                <CardContent sx={{ p: 3 }}>
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
                          pointerEvents: 'none'
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
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                bgcolor: item.color,
                              }}
                            />
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                color: 'text.secondary',
                              }}
                            >
                              {item.name}
                            </Typography>
                          </Stack>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              color: 'text.primary' 
                            }}
                          >
                            {item.value}
                          </Typography>
                        </Stack>
                      ))}
                    </Stack>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Stack>
        </Stack>
      </Box>
    </Box>
  );
};

export default PortfolioDashboard;