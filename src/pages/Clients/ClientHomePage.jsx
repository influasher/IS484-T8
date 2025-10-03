import React, { useState, useEffect } from 'react';
import { Typography, Box, Card, CardContent, Stack } from '@mui/material';
import { AccountBalanceWallet, TrendingUp } from '@mui/icons-material';
import Watchlist from '../../components/ui/Watchlist';
import ClientPortfolio from '../../components/clients/ClientPortfolio';
import useAuth from '../../hooks/useAuth';

function ClientHomePage() {
  const { user, getUserFullName } = useAuth();
  const clientId = user?.id;
  const [walletBalance, setWalletBalance] = useState(null);
  const [totalPortfolioValue, setTotalPortfolioValue] = useState(null);
  const [loading, setLoading] = useState(true);

  console.log('ClientHomePage rendered, clientId:', clientId);

  useEffect(() => {
    const fetchWalletBalance = async () => {
      if (!clientId) return;

      try {
        const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
        const response = await fetch(`${API_BASE_URL}/transactions/client/${clientId}`);

        if (response.ok) {
          const result = await response.json();

          // Calculate wallet balance from transactions
          let deposits = 0;
          let withdrawals = 0;
          let purchases = 0;
          let sales = 0;
          let dividends = 0;

          result.transactions.forEach(txn => {
            const amount = parseFloat(txn.amount);
            switch (txn.type.toLowerCase()) {
              case 'deposit':
                deposits += amount;
                break;
              case 'withdrawal':
                withdrawals += Math.abs(amount);
                break;
              case 'buy':
              case 'purchase':
                purchases += Math.abs(amount);
                break;
              case 'sell':
              case 'sale':
                sales += amount;
                break;
              case 'dividend':
                dividends += amount;
                break;
            }
          });

          const cashBalance = deposits - withdrawals - purchases + sales + dividends;
          setWalletBalance(cashBalance);

          // Also calculate total portfolio value
          const netInvested = deposits - withdrawals;
          const investedInSecurities = purchases - sales;
          const estimatedSecuritiesValue = investedInSecurities * 1.15; // 15% estimated growth
          const totalValue = cashBalance + estimatedSecuritiesValue;
          setTotalPortfolioValue(totalValue);
        }
      } catch (error) {
        console.error('Error fetching wallet balance:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchWalletBalance();
  }, [clientId]);

  if (!clientId) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Hello, {getUserFullName()}
      </Typography>

      {/* Wallet Balance Cards */}
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 4 }}>
        <Card sx={{ flex: 1, bgcolor: 'secondary' }}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={2}>
              <AccountBalanceWallet sx={{ fontSize: 40, color: 'secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Cash Balance
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  {loading ? '...' : `$${(walletBalance || 0).toFixed(2)} SGD`}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, bgcolor: 'secondary' }}>
          <CardContent>
            <Stack direction="row" alignItems="center" spacing={2}>
              <TrendingUp sx={{ fontSize: 40, color: 'secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total Portfolio Value
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  {loading ? '...' : `$${(totalPortfolioValue || 0).toFixed(2)} SGD`}
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      <ClientPortfolio clientId={clientId} />
      {/* <Watchlist /> */}
    </Box>
  );
}

export default ClientHomePage;