import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
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
  Card,
  CardContent,
  CardHeader,
  Tabs,
  Tab,
} from '@mui/material';
import { Search, TrendingUp, AccountBalance, Wallet } from '@mui/icons-material';
import { red } from '@mui/material/colors';

const ClientTransactionTable = ({ transactionData = [], loading = false }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState('date_desc');
  const [currentPages, setCurrentPages] = useState({
    trading: 1,
    dividends: 1,
    wallet: 1
  });
  const [activeTab, setActiveTab] = useState(0); // For mobile view
  
  const itemsPerPage = 5; // Reduced for better layout

  // Transaction sort options
  const transactionSortOptions = [
    { label: 'Latest First', value: 'date_desc' },
    { label: 'Oldest First', value: 'date_asc' },
    { label: 'Amount (High to Low)', value: 'amount_desc' },
    { label: 'Amount (Low to High)', value: 'amount_asc' },
  ];

  // Helper functions
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
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
      color: isPositive ? "green" : 'red'
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

  // Categorize transactions
  const categorizeTransactions = (data) => {
    const trading = data.filter(t =>
      ['purchase', 'sale', 'buy', 'sell'].includes(t.type.toLowerCase())
    );

    const dividends = data.filter(t =>
      ['dividend', 'capital gains', 'interest'].includes(t.type.toLowerCase())
    );

    const wallet = data.filter(t =>
      ['deposit', 'withdrawal'].includes(t.type.toLowerCase())
    );

    return { trading, dividends, wallet };
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
      default:
        filtered.sort((a, b) => new Date(b.dateTime) - new Date(a.dateTime));
    }
    
    return filtered;
  };

  // Event handlers
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  const handleSortChange = (e) => {
    setSortOrder(e.target.value);
  };
  
  const handlePageChange = (category, pageNumber) => {
    setCurrentPages(prev => ({
      ...prev,
      [category]: pageNumber
    }));
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Process transactions
  const categorizedTransactions = categorizeTransactions(transactionData);
  const filteredCategorized = {
    trading: filterAndSortTransactions(categorizedTransactions.trading, searchTerm, sortOrder),
    dividends: filterAndSortTransactions(categorizedTransactions.dividends, searchTerm, sortOrder),
    wallet: filterAndSortTransactions(categorizedTransactions.wallet, searchTerm, sortOrder)
  };

  // Pagination calculations
  const paginatedData = {};
  Object.keys(filteredCategorized).forEach(category => {
    const data = filteredCategorized[category];
    const currentPage = currentPages[category];
    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    
    paginatedData[category] = {
      data: data.slice(startIndex, endIndex),
      totalPages,
      totalItems: data.length
    };
  });

  // Reset pages when filters change
  useEffect(() => {
    setCurrentPages({
      trading: 1,
      dividends: 1,
      wallet: 1
    });
  }, [searchTerm, sortOrder]);

  // Table component for each category
  const TransactionCategoryTable = ({ 
    category, 
    title, 
    icon, 
    data, 
    totalPages, 
    totalItems, 
    currentPage,
    color 
  }) => (
    <Card sx={{ height: 'fit-content' }}>
      <CardHeader
        avatar={icon}
        title={
          <Typography variant="h6" sx={{ color: color}}>
            {title}
          </Typography>
        }
        subheader={
          <Typography variant="body2" color="text.secondary">
            {totalItems} transactions
          </Typography>
        }
      />
      <CardContent sx={{ pt: 0 }}>
        <TableContainer>
          <Table size="small" aria-label={`${title} table`}>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Source</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Amount</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} sx={{ textAlign: 'center', py: 3 }}>
                    <Typography color="text.secondary">Loading...</Typography>
                  </TableCell>
                </TableRow>
              ) : data.length > 0 ? (
                data.map((transaction) => {
                  const { amount: formattedAmount, isPositive, color: amountColor } = formatAmount(transaction.amount, transaction.currency);
                  
                  return (
                    <TableRow 
                      key={transaction.id} 
                      hover 
                      sx={{ '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' } }}
                    >
                      <TableCell>
                        <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                          {formatDate(transaction.dateTime)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            maxWidth: 100,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            fontSize: '0.875rem'
                          }}
                          title={transaction.source}
                        >
                          {transaction.source}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: amountColor,
                            fontWeight: 500,
                            fontSize: '0.875rem'
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
                          sx={{ fontSize: '0.75rem' }}
                        />
                      </TableCell>
                    </TableRow>
                  );
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={4} sx={{ textAlign: 'center', py: 3 }}>
                    <Typography color="text.secondary" variant="body2">
                      No {category} transactions found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={(event, page) => handlePageChange(category, page)}
              size="small"
              shape="rounded"
              sx={{
                "& .MuiPaginationItem-root.Mui-selected": {
                  backgroundColor: color,
                  color: "#fff",
                },
              }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 3 }}>
        Transaction History
      </Typography>
      
      {/* Search and Filter Controls */}
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
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search across all transactions..."
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
          
          <Grid item xs={12} md={4}>
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

        {/* Results Summary */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Trading: {paginatedData.trading?.totalItems || 0} | 
            Dividends: {paginatedData.dividends?.totalItems || 0} | 
            Wallet: {paginatedData.wallet?.totalItems || 0}
            {searchTerm && ` (filtered by "${searchTerm}")`}
          </Typography>
        </Box>
      </Box>

      <Box
      sx={{
        mb: 3,
        borderRadius: 2,
        backgroundColor: "#fafafa",
        border: 1,
        borderColor: "grey.300",
        boxShadow: 1,
      }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          variant="fullWidth"
        >
          <Tab 
            icon={<TrendingUp />} 
            label="Trading" 
            iconPosition="start"
          />
          <Tab 
            icon={<AccountBalance />} 
            label="Dividends" 
            iconPosition="start"
          />
          <Tab 
            icon={<Wallet />} 
            label="Wallet" 
            iconPosition="start"
          />
        </Tabs>

        {activeTab === 0 && (
          <TransactionCategoryTable
            category="trading"
            title="Stock Trading"
            icon={<TrendingUp sx={{ color: 'red' }} />}
            data={paginatedData.trading?.data || []}
            totalPages={paginatedData.trading?.totalPages || 0}
            totalItems={paginatedData.trading?.totalItems || 0}
            currentPage={currentPages.trading}
            color="red"
          />
        )}
        
        {activeTab === 1 && (
          <TransactionCategoryTable
            category="dividends"
            title="Dividends & Returns"
            icon={<AccountBalance sx={{ color: 'red' }} />}
            data={paginatedData.dividends?.data || []}
            totalPages={paginatedData.dividends?.totalPages || 0}
            totalItems={paginatedData.dividends?.totalItems || 0}
            currentPage={currentPages.dividends}
            color="red"
          />
        )}
        
        {activeTab === 2 && (
          <TransactionCategoryTable
            category="wallet"
            title="Wallet Transactions"
            icon={<Wallet sx={{ color: "red" }} />}
            data={paginatedData.wallet?.data || []}
            totalPages={paginatedData.wallet?.totalPages || 0}
            totalItems={paginatedData.wallet?.totalItems || 0}
            currentPage={currentPages.wallet}
            color="red"
          />
        )}
      </Box>
    </Box>
  );
};

export default ClientTransactionTable;