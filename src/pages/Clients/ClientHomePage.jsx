import React from 'react';
import { Typography, Box } from '@mui/material';
import Watchlist from '../../components/ui/Watchlist';

function ClientHomePage() {
  console.log('ClientHomePage rendered');

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h4" sx={{ mb: 4 }}>
        Client Home Page
      </Typography>
      <Watchlist />
    </Box>
  );
}

export default ClientHomePage;