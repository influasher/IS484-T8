import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Card, CardContent, Alert, LinearProgress,
  List, ListItem, ListItemIcon, ListItemText, Divider, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper
} from '@mui/material';
import {
  CheckCircle, Warning, Error, Info, TrendingUp, TrendingDown,
  Schedule, Analytics, Refresh
} from '@mui/icons-material';
import { getData, postData } from '../../services/api';

const SystemHealth = ({ stats }) => {
  const [retrainStatus, setRetrainStatus] = useState(null);
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchRetrainStatus = async () => {
    try {
      // postData wrapper prefixes /api, target labeling retrain endpoint
      const response = await postData('/labeling/retrain-needed', { threshold: 100 });
      if (response?.status === 200) {
        setRetrainStatus(response.data);
      }
    } catch (error) {
      console.error('Error fetching retrain status:', error);
    }
  };

  const calculateSystemMetrics = () => {
    if (!stats) return null;

    const totalItems = stats.pending_count + stats.completed_count;
    const completionRate = totalItems > 0 ? (stats.completed_count / totalItems) * 100 : 0;
    const votesPerUser = stats.unique_users > 0 ? stats.total_votes / stats.unique_users : 0;
    
    return {
      totalItems,
      completionRate,
      votesPerUser,
      agreementRate: stats.avg_agreement_rate * 100,
      healthScore: calculateHealthScore(stats)
    };
  };

  const calculateHealthScore = (stats) => {
    let score = 100;
    
    // Penalize high pending count
    if (stats.pending_count > 100) score -= 20;
    else if (stats.pending_count > 50) score -= 10;
    
    // Penalize low agreement rate
    if (stats.avg_agreement_rate < 0.7) score -= 15;
    else if (stats.avg_agreement_rate < 0.8) score -= 5;
    
    // Penalize high priority pending items
    if (stats.high_priority_pending > 20) score -= 25;
    else if (stats.high_priority_pending > 10) score -= 15;
    
    // Bonus for active participation
    if (stats.unique_users > 10) score += 5;
    if (stats.total_votes > 500) score += 5;
    
    return Math.max(0, Math.min(100, score));
  };

  const getHealthColor = (score) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'info';
    if (score >= 50) return 'warning';
    return 'error';
  };

  const getHealthLabel = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  useEffect(() => {
    fetchRetrainStatus();
    if (stats) {
      setSystemMetrics(calculateSystemMetrics());
    }
  }, [stats]);

  const refreshData = async () => {
    setLoading(true);
    try {
      await fetchRetrainStatus();
    } finally {
      setLoading(false);
    }
  };

  if (!stats || !systemMetrics) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
        <Typography>Loading system health data...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* System Health Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Analytics sx={{ mr: 1, color: getHealthColor(systemMetrics.healthScore) }} />
                <Typography variant="h6">System Health</Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h3" color={`${getHealthColor(systemMetrics.healthScore)}.main`}>
                  {systemMetrics.healthScore}
                </Typography>
                <Typography variant="h6" sx={{ ml: 1 }}>
                  / 100
                </Typography>
              </Box>
              
              <Typography variant="body2" color="textSecondary">
                {getHealthLabel(systemMetrics.healthScore)}
              </Typography>
              
              <LinearProgress
                variant="determinate"
                value={systemMetrics.healthScore}
                color={getHealthColor(systemMetrics.healthScore)}
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Completion Rate</Typography>
              </Box>
              
              <Typography variant="h3" color="info.main">
                {systemMetrics.completionRate.toFixed(1)}%
              </Typography>
              
              <Typography variant="body2" color="textSecondary">
                {stats.completed_count} of {systemMetrics.totalItems} items completed
              </Typography>
              
              <LinearProgress
                variant="determinate"
                value={systemMetrics.completionRate}
                color="info"
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Schedule sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Avg Votes/User</Typography>
              </Box>
              
              <Typography variant="h3" color="warning.main">
                {systemMetrics.votesPerUser.toFixed(1)}
              </Typography>
              
              <Typography variant="body2" color="textSecondary">
                {stats.total_votes} votes by {stats.unique_users} users
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts and Warnings */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          System Alerts
        </Typography>
        
        {stats.high_priority_pending > 10 && (
          <Alert severity="error" sx={{ mb: 2 }} icon={<Error />}>
            <strong>Critical:</strong> {stats.high_priority_pending} high-priority items require immediate attention!
          </Alert>
        )}
        
        {stats.avg_agreement_rate < 0.7 && (
          <Alert severity="warning" sx={{ mb: 2 }} icon={<Warning />}>
            <strong>Low Agreement:</strong> Average agreement rate is {(stats.avg_agreement_rate * 100).toFixed(1)}%. 
            Consider reviewing annotation guidelines.
          </Alert>
        )}
        
        {stats.pending_count > 50 && (
          <Alert severity="info" sx={{ mb: 2 }} icon={<Info />}>
            <strong>Queue Backlog:</strong> {stats.pending_count} items pending. Consider increasing annotation capacity.
          </Alert>
        )}
        
        {retrainStatus?.retrain_needed && (
          <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>
            <strong>Ready for Retraining:</strong> {retrainStatus.new_labels_count} new labels collected. 
            Model retraining is recommended.
          </Alert>
        )}
        
        {/* Default message if no alerts */}
        {stats.high_priority_pending <= 10 && 
         stats.avg_agreement_rate >= 0.7 && 
         stats.pending_count <= 50 && 
         !retrainStatus?.retrain_needed && (
          <Alert severity="success" icon={<CheckCircle />}>
            All systems operating normally. No immediate action required.
          </Alert>
        )}
      </Box>

      {/* Detailed Metrics Table */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Detailed Metrics</Typography>
          <Button
            startIcon={<Refresh />}
            onClick={refreshData}
            disabled={loading}
            size="small"
          >
            Refresh
          </Button>
        </Box>
        
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Metric</TableCell>
                <TableCell align="right">Value</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>Total Queue Items</TableCell>
                <TableCell align="right">{systemMetrics.totalItems}</TableCell>
                <TableCell>
                  {systemMetrics.totalItems > 0 ? 
                    <CheckCircle color="success" fontSize="small" /> : 
                    <Warning color="warning" fontSize="small" />
                  }
                </TableCell>
              </TableRow>
              
              <TableRow>
                <TableCell>Average Agreement Rate</TableCell>
                <TableCell align="right">{systemMetrics.agreementRate.toFixed(1)}%</TableCell>
                <TableCell>
                  {systemMetrics.agreementRate >= 70 ? 
                    <CheckCircle color="success" fontSize="small" /> : 
                    <Warning color="warning" fontSize="small" />
                  }
                </TableCell>
              </TableRow>
              
              <TableRow>
                <TableCell>High Priority Pending</TableCell>
                <TableCell align="right">{stats.high_priority_pending}</TableCell>
                <TableCell>
                  {stats.high_priority_pending <= 10 ? 
                    <CheckCircle color="success" fontSize="small" /> : 
                    <Error color="error" fontSize="small" />
                  }
                </TableCell>
              </TableRow>
              
              {retrainStatus && (
                <TableRow>
                  <TableCell>New Labels Since Last Training</TableCell>
                  <TableCell align="right">{retrainStatus.new_labels_count}</TableCell>
                  <TableCell>
                    {retrainStatus.retrain_needed ? 
                      <CheckCircle color="success" fontSize="small" /> : 
                      <Info color="info" fontSize="small" />
                    }
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
};

export default SystemHealth;
