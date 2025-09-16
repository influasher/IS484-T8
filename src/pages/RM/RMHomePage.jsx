
import React from 'react';
import ClientCards from '../../components/clients/ClientCards';
import StockWatchlist from '../../components/ui/Watchlist';
import { Box } from '@mui/material';
import News from '../../components/news/News';

const RMHomePage = () => {
    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 2, gap: 2 }}>
            {/* ClientCards takes one full row */}
            <Box sx={{ width: '100%' }}>
                <ClientCards sx={{ pt: "84px" }} />
            </Box>

            {/* StockWatchlist and News share one row as two columns */}
            <Box sx={{ display: 'flex', flexDirection: 'row', width: '100%', gap: 2 }}>
                <Box sx={{ flex: 1 }}>
                    <StockWatchlist />
                </Box>
                <Box sx={{ flex: 1 }}>
                    <News />
                </Box>
            </Box>
        </Box>
    );
};

export default RMHomePage;