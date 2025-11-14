import React from 'react';
import { Container, Box, Typography } from '@mui/material';
import ActiveLearningDashboard from '../components/analysis/ActiveLearningDashboard';
import useAuth from '../hooks/useAuth';

const AnalysisPage = () => {
  const { user } = useAuth();

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Sentiment Analysis Dashboard
        </Typography>
        <Typography variant="subtitle1" color="textSecondary" sx={{ mb: 4 }}>
          Monitor active learning system and analyze sentiment model performance
        </Typography>
        
        <ActiveLearningDashboard />
      </Box>
    </Container>
  );
};

export default AnalysisPage;
