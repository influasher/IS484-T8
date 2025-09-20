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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Chip,
  Pagination,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Paper,
} from '@mui/material';
import { Search } from '@mui/icons-material';
import { LineChart } from '@mui/x-charts/LineChart';
import { PieChart } from '@mui/x-charts/PieChart';
import { ChartsReferenceLine } from '@mui/x-charts/ChartsReferenceLine';

const PortfolioDashboard = () => {
  // All hooks declared at the top level - this fixes the hook order issue
  const [timeRange, setTimeRange] = useState('1Y');
  const [portfolioData, setPortfolioData] = useState(null);
  const [transactionData, setTransactionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState('date_desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  
  const itemsPerPage = 10;

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

  // Transaction sort options - moved outside of functions to avoid recreation
  const transactionSortOptions = [
    { label: 'Latest First', value: 'date_desc' },
    { label: 'Oldest First', value: 'date_asc' },
    { label: 'Amount (High to Low)', value: 'amount_desc' },
    { label: 'Amount (Low to High)', value: 'amount_asc' },
    { label: 'Type (A-Z)', value: 'type_asc' },
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

  // Helper functions (moved up to be defined before use)
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const formatAmount = (amount, currency) => {
    const isPositive = amount >= 0;
    const formattedAmount = `${currency} ${Math.abs(amount).toLocaleString()}`;
    return {
      amount: formattedAmount,
      isPositive,
      color: isPositive ? '#10b981' : '#ef4444'
    };
  };
  
  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'pending':
        return 'info';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const getTypeColor = (type) => {
    switch (type.toLowerCase()) {
      case 'deposit':
        return '#10b981';
      case 'withdrawal':
        return '#ef4444';
      case 'purchase':
        return '#f59e0b';
      case 'sale':
        return '#06b6d4';
      case 'dividend':
        return '#8b5cf6';
      case 'capital gains':
        return '#ec4899';
      case 'interest':
        return '#84cc16';
      default:
        return '#6b7280';
    }
  };

  const filterAndSortTransactions = (data, search, sort) => {
    let filtered = [...data];
    
    // Apply search filter
    if (search) {
      filtered = filtered.filter(transaction =>
        transaction.source.toLowerCase().includes(search.toLowerCase()) ||
        transaction.type.toLowerCase().includes(search.toLowerCase()) ||
        transaction.description.toLowerCase().includes(search.toLowerCase()) ||
        transaction.status.toLowerCase().includes(search.toLowerCase()) ||
        transaction.id.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    // Apply sorting
    switch (sort) {
      case 'date_desc':
        filtered.sort((a, b) => new Date(b.dateTime) - new Date(a.dateTime));
        break;
      case 'date_asc':
        filtered.sort((a, b) => new Date(a.dateTime) - new Date(b.dateTime));
        break;
      case 'amount_desc':
        filtered.sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
        break;
      case 'amount_asc':
        filtered.sort((a, b) => Math.abs(a.amount) - Math.abs(b.amount));
        break;
      case 'type_asc':
        filtered.sort((a, b) => a.type.localeCompare(b.type));
        break;
      default:
        filtered.sort((a, b) => new Date(b.dateTime) - new Date(a.dateTime));
    }
    
    return filtered;
  };

  const fetchPortfolioData = async (period = '1Y') => {
    setLoading(true);
    try {
      // Mock API call - replace with actual implementation
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
      setPortfolioData(mockPortfolioData);
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactionData = async () => {
    try {
      setTransactionData(mockTransactionData);
    } catch (error) {
      console.log('Error fetching transaction data:', error);
    }
  };

  const handleTimeRangeChange = (event, newTimeRange) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
      fetchPortfolioData(newTimeRange);
    }
  };

  // Event handlers
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  const handleSortChange = (e) => {
    setSortOrder(e.target.value);
  };
  
  const handlePageChange = (event, pageNumber) => {
    setCurrentPage(pageNumber);
  };

  // All useEffect hooks declared together
  useEffect(() => {
    fetchPortfolioData(timeRange);
    fetchTransactionData();
  }, []);

  useEffect(() => {
    if (transactionData.length > 0) {
      const filtered = filterAndSortTransactions(transactionData, searchTerm, sortOrder);
      setFilteredTransactions(filtered);
      setCurrentPage(1); // Reset to first page when filters change
    }
  }, [transactionData, searchTerm, sortOrder]);

  // Loading state check AFTER all hooks are declared
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

  // Calculate pagination
  const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTransactions = filteredTransactions.slice(startIndex, endIndex);

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
                    />

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
        <hr></hr>
        <Box sx={{ mt: 4 }}>
            <Typography variant="h5" sx={{ mb: 3 }}>
                Transaction History
            </Typography>
            
            {/* Search and Filter Controls - Same styling as SearchTable */}
            <Box
                sx={{
                p: 2,
                mb: 3,
                borderRadius: 2,
                backgroundColor: "#fafafa",
                border: 1,
                borderColor: "grey.300",
                boxShadow: 1,
                }}
            >
                <Grid
                container
                spacing={2}
                justifyContent="space-between"
                alignItems="center"
                >
                <Grid item xs={12} sm={8} md={8}>
                    <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="Search transactions by ID, source, type, or description..."
                    value={searchTerm}
                    onChange={handleSearchChange}
                    InputProps={{
                        startAdornment: (
                        <InputAdornment position="start">
                            <Search color="action" />
                        </InputAdornment>
                        ),
                    }}
                    sx={{
                        "& .MuiOutlinedInput-root": {
                        backgroundColor: "white",
                        },
                    }}
                    />
                </Grid>
                
                <Grid item xs={12} sm={4} md={4}>
                    <FormControl fullWidth variant="outlined">
                    <InputLabel id="sort-select-label">Sort By</InputLabel>
                    <Select
                        labelId="sort-select-label"
                        value={sortOrder}
                        onChange={handleSortChange}
                        label="Sort By"
                        sx={{
                        backgroundColor: "white",
                        }}
                    >
                        {transactionSortOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                            {option.label}
                        </MenuItem>
                        ))}
                    </Select>
                    </FormControl>
                </Grid>
                </Grid>

                {/* Results Counter */}
                <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                    Showing {paginatedTransactions.length} transactions on page {currentPage} of{" "}
                    {totalPages} ({filteredTransactions.length} total)
                    {searchTerm && ` for "${searchTerm}"`}
                </Typography>
                </Box>
            </Box>

            {/* Transaction Table */}
            <TableContainer component={Paper} elevation={0}>
                <Table>
                <TableHead>
                    <TableRow>
                    <TableCell>Transaction ID</TableCell>
                    <TableCell>Date & Time</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Description</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {loading ? (
                    <TableRow>
                        <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                        <Typography color="text.secondary">Loading transactions...</Typography>
                        </TableCell>
                    </TableRow>
                    ) : paginatedTransactions.length > 0 ? (
                    paginatedTransactions.map((transaction) => {
                        const { amount: formattedAmount, isPositive, color } = formatAmount(transaction.amount, transaction.currency);
                        
                        return (
                        <TableRow 
                            key={transaction.id} 
                            hover 
                            sx={{ 
                            '&:hover': { 
                                backgroundColor: 'rgba(0, 0, 0, 0.04)' 
                            } 
                            }}
                        >
                            <TableCell>
                            <Typography 
                                variant="body2" 
                                sx={{ 
                                color: 'text.secondary'
                                }}
                            >
                                {transaction.id}
                            </Typography>
                            </TableCell>
                            
                            <TableCell>
                            <Typography variant="body2">
                                {formatDate(transaction.dateTime)}
                            </Typography>
                            </TableCell>
                            
                            <TableCell>
                            <Typography 
                                variant="body2" 
                                sx={{ 
                                maxWidth: 120,
                                whiteSpace: 'nowrap'
                                }}
                            >
                                {transaction.source}
                            </Typography>
                            </TableCell>
                            
                            <TableCell>
                            <Chip
                                label={transaction.type}
                                size="small"
                                sx={{
                                backgroundColor: getTypeColor(transaction.type),
                                color: 'white',
                                fontWeight: 500,
                                fontSize: '0.75rem',
                                }}
                            />
                            </TableCell>
                            
                            <TableCell>
                            <Typography 
                                variant="body2" 
                                sx={{ 
                                color: color,
                                }}
                            >
                                {isPositive ? '+' : '-'}{formattedAmount}
                            </Typography>
                            </TableCell>
                            
                            <TableCell>
                            <Chip
                                label={transaction.status}
                                size="small"
                                color={getStatusColor(transaction.status)}
                                variant="outlined"
                            />
                            </TableCell>
                            
                            <TableCell>
                            <Typography 
                                variant="body2" 
                                sx={{ 
                                maxWidth: 200,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                color: 'text.secondary'
                                }}
                                title={transaction.description}
                            >
                                {transaction.description}
                            </Typography>
                            </TableCell>
                        </TableRow>
                        );
                    })
                    ) : (
                    <TableRow>
                        <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                        <Typography color="text.secondary">
                            No transactions found
                        </Typography>
                        </TableCell>
                    </TableRow>
                    )}
                </TableBody>
                </Table>
            </TableContainer>

            {/* Pagination */}
            {totalPages > 1 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, mb: 4 }}>
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
                    "& .MuiPaginationItem-root.Mui-selected": {
                        backgroundColor: "#212121",
                        color: "#fff",
                    },
                    }}
                />
                </Box>
            )}
            </Box>
      </Box>
    </Box>
  );
};

export default PortfolioDashboard;