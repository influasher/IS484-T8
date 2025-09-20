import React from 'react';
import { Typography, Box } from '@mui/material';
import Watchlist from '../../components/ui/Watchlist';
import ClientPortfolio from '../../components/clients/ClientPortfolio';
import { useParams } from 'react-router-dom';

function ClientHomePage() {
  console.log('ClientHomePage rendered');


  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h4" sx={{ mb: 4 }}>
        Hello,
      </Typography>
        <ClientPortfolio/>
      {/* <Watchlist /> */}
    </Box>
  );
}

export default ClientHomePage;