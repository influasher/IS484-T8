import React from 'react';
import { Typography, Box } from '@mui/material';
import Watchlist from '../../components/ui/Watchlist';
import ClientPortfolio from '../../components/clients/ClientPortfolio';
import useAuth from '../../hooks/useAuth';

function ClientHomePage() {
  const { user, getUserFullName } = useAuth();
  const clientId = user?.id;

  console.log('ClientHomePage rendered, clientId:', clientId);

  if (!clientId) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h4" sx={{ mb: 4 }}>
        Hello, {getUserFullName()}
      </Typography>
      <ClientPortfolio clientId={clientId} />
      {/* <Watchlist /> */}
    </Box>
  );
}

export default ClientHomePage;