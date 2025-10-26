import React, { useState, useEffect } from 'react';
import { Typography, Box, Card, CardContent, Stack, Grid, Divider, useTheme, useMediaQuery } from '@mui/material';
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

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  console.log('ClientHomePage rendered, clientId:', clientId);

  useEffect(() => {
    const fetchWalletBalance = async () => {
      if (!clientId) return;

      try {
        const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
        const response = await fetch(`${API_BASE_URL}/api/transactions/client/${clientId}`);

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

      {/* Mobile Wallet Balance Cards */}
      {isMobile && (
        <Stack direction="column" spacing={2} sx={{ mb: 4 }}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box>
                  <Typography variant="body2" sx={{ opacity: 0.8, mb: 1 }}>
                    Cash Balance
                  </Typography>
                  <Typography variant="h5">
                    {loading ? '...' : `$${(walletBalance || 0).toFixed(2)} USD`}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box>
                  <Typography variant="body2" sx={{ opacity: 0.8, mb: 1 }}>
                    Total Portfolio Value
                  </Typography>
                  <Typography variant="h5">
                    {loading ? '...' : `$${(totalPortfolioValue || 0).toFixed(2)} USD`}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      )}

      {/* Desktop/Tablet Layout */}
      {!isMobile ? (
        <Stack direction="row" sx={{ width: "100%" }}>
          <ClientPortfolio clientId={clientId} />

          {/* Divider between Left & Right */}
          <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />

          {/* RIGHT: Sticky Sidebar */}
          <Stack
            direction="column"
            sx={{
              flex: 1.2,
              maxWidth: 400,
              position: 'sticky',
              top: "15%",
              alignSelf: 'flex-start',
              height: 'fit-content'
            }}
          >
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Cash Balance
                </Typography>
                <Typography variant="h5">
                  {loading ? '...' : `$${(walletBalance || 0).toFixed(2)} USD`}
                </Typography>
              </Box>
            </Stack>

            <Divider sx={{ my: 2 }} />

            <Stack direction="row" alignItems="center" spacing={2}>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Total Portfolio Value
                </Typography>
                <Typography variant="h5">
                  {loading ? '...' : `$${(totalPortfolioValue || 0).toFixed(2)} USD`}
                </Typography>
              </Box>
            </Stack>
          </Stack>
        </Stack>
      ) : (
        /* Mobile Layout - Only Portfolio */
        <Box sx={{ width: "100%" }}>
          <ClientPortfolio clientId={clientId} />
        </Box>
      )}
    </Box>
  );
}

export default ClientHomePage;