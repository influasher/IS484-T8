import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Card, CardContent, Button,
  Paper, Tabs, Tab,
  LinearProgress, Alert
} from '@mui/material';
import {
  Refresh, CheckCircle, Warning,
  TrendingUp, People, Assessment
} from '@mui/icons-material';
import { getData } from '../../services/api';
import UserStatistics from './UserStatistics';
import ModelTraining from './ModelTraining';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const ActiveLearningDashboard = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch system statistics
  const fetchStats = async () => {
    try {
      const response = await getData('/labeling/stats');
      if (response?.status === 200) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
      setError('Failed to fetch system statistics');
    }
  };

  // Refresh all data
  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      await fetchStats();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Active Learning Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={refreshData}
          disabled={loading}
        >
          Refresh Data
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading Bar */}
      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Stats Cards - Focus on training and user activity */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Labeled Samples
                    </Typography>
                    <Typography variant="h4">
                      {stats.completed_count}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <People sx={{ mr: 1, color: 'info.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Active Contributors
                    </Typography>
                    <Typography variant="h4">
                      {stats.unique_users}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TrendingUp sx={{ mr: 1, color: 'warning.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Avg Agreement
                    </Typography>
                    <Typography variant="h4">
                      {(stats.avg_agreement_rate * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Training Readiness Indicator */}
          <Grid item xs={12}>
            {stats.completed_count > 20 ? (
              <Alert severity="success" icon={<CheckCircle />}>
                <strong>Training Data Available:</strong> {stats.completed_count} labeled samples ready for model training.
              </Alert>
            ) : (
              <Alert severity="info" icon={<Warning />}>
                <strong>Collecting Training Data:</strong> {stats.completed_count} of 20 minimum samples collected. 
                Provide feedback on news articles to generate more training data.
              </Alert>
            )}
          </Grid>
        </Grid>
      )}

      {/* Tabs - Only User Statistics and Model Training */}
      <Paper sx={{ width: '100%' }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="dashboard tabs">
          <Tab label="User Statistics" />
          <Tab label="Model Training" />
        </Tabs>

        {/* User Statistics Tab */}
        <TabPanel value={currentTab} index={0}>
          <UserStatistics />
        </TabPanel>

        {/* Model Training Tab */}
        <TabPanel value={currentTab} index={1}>
          <ModelTraining stats={stats} />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default ActiveLearningDashboard;
