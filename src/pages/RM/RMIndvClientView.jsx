import React from 'react';
import ClientRecc from '../../components/clients/ClientRecc';
import StockWatchlist from '../../components/ui/Watchlist';

const RMIndvClientView = () => {
    return (
        <div>
            <ClientRecc />
            <StockWatchlist/>
        </div>
    );
};

export default RMIndvClientView;