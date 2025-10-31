import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Card, CardContent, Chip, Button, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Paper, Tabs, Tab,
  LinearProgress, Alert, IconButton, Tooltip, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField
} from '@mui/material';
import {
  Refresh, CheckCircle, Cancel, Info, Warning, Assignment,
  TrendingUp, People, Assessment
} from '@mui/icons-material';
import { getData, postData } from '../../services/api';
import UserStatistics from './UserStatistics';
import SystemHealth from './SystemHealth';

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
  const [pendingItems, setPendingItems] = useState([]);
  const [userStats, setUserStats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [finalizeDialog, setFinalizeDialog] = useState({ open: false, itemId: null });

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

  // Fetch pending items
  const fetchPendingItems = async () => {
    try {
      const response = await getData('/labeling/pending?limit=50');
      if (response?.status === 200) {
        setPendingItems(response.data);
      }
    } catch (error) {
      console.error('Error fetching pending items:', error);
      setError('Failed to fetch pending items');
    }
  };

  // Fetch user statistics
  const fetchUserStats = async () => {
    try {
      // We'll need to implement a user list endpoint or get unique users from votes
      // For now, we'll use placeholder data structure
      setUserStats([
        // This would come from an actual endpoint
      ]);
    } catch (error) {
      console.error('Error fetching user stats:', error);
      setError('Failed to fetch user statistics');
    }
  };

  // Refresh all data
  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchStats(),
        fetchPendingItems(),
        fetchUserStats()
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Finalize an item
  const finalizeItem = async (itemId) => {
    try {
      // postData wrapper prefixes /api => /api/labeling/finalize/:id
      const response = await postData(`/labeling/finalize/${itemId}`, {});
      if (response?.status === 200) {
        await refreshData();
        setFinalizeDialog({ open: false, itemId: null });
      } else {
        setError('Failed to finalize item');
      }
    } catch (error) {
      console.error('Error finalizing item:', error);
      setError('Failed to finalize item');
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 1: return 'error';
      case 2: return 'warning'; 
      case 3: return 'info';
      default: return 'default';
    }
  };

  const getPriorityLabel = (priority) => {
    switch (priority) {
      case 1: return 'Critical';
      case 2: return 'High';
      case 3: return 'Medium';
      case 4: return 'Low';
      case 5: return 'Lowest';
      default: return 'Unknown';
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Sentiment Analysis Dashboard
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

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Assignment sx={{ mr: 1, color: 'primary.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Pending Items
                    </Typography>
                    <Typography variant="h4">
                      {stats.pending_count}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Completed
                    </Typography>
                    <Typography variant="h4">
                      {stats.completed_count}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <People sx={{ mr: 1, color: 'info.main' }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Active Users
                    </Typography>
                    <Typography variant="h4">
                      {stats.unique_users}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
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

          {stats.high_priority_pending > 0 && (
            <Grid item xs={12}>
              <Alert severity="warning" icon={<Warning />}>
                <strong>{stats.high_priority_pending} high-priority items</strong> are pending human feedback!
              </Alert>
            </Grid>
          )}
        </Grid>
      )}

      {/* Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="dashboard tabs">
          <Tab label="Pending Queue" />
          <Tab label="User Statistics" />
          <Tab label="System Health" />
        </Tabs>

        {/* Pending Queue Tab */}
        <TabPanel value={currentTab} index={0}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Priority</TableCell>
                  <TableCell>Text Preview</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Disagreement</TableCell>
                  <TableCell>Votes</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pendingItems.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Chip
                        label={getPriorityLabel(item.priority)}
                        color={getPriorityColor(item.priority)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell sx={{ maxWidth: 200 }}>
                      <Typography variant="body2" noWrap>
                        {item.text?.substring(0, 100)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {item.sampling_reason}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {(item.disagreement_score * 100).toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={item.vote_count || 0}
                        color={item.vote_count >= 3 ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(item.created_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Force finalize">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => setFinalizeDialog({ open: true, itemId: item.id })}
                        >
                          <CheckCircle />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
                {pendingItems.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="textSecondary">
                        No pending items
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* User Statistics Tab */}
        <TabPanel value={currentTab} index={1}>
          <UserStatistics />
        </TabPanel>

        {/* System Health Tab */}
        <TabPanel value={currentTab} index={2}>
          <SystemHealth stats={stats} />
        </TabPanel>
      </Paper>

      {/* Finalize Dialog */}
      <Dialog 
        open={finalizeDialog.open} 
        onClose={() => setFinalizeDialog({ open: false, itemId: null })}
      >
        <DialogTitle>Force Finalize Item</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to force finalize this item? This will complete the labeling process
            even if it hasn't reached the minimum vote threshold.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFinalizeDialog({ open: false, itemId: null })}>
            Cancel
          </Button>
          <Button 
            onClick={() => finalizeItem(finalizeDialog.itemId)} 
            variant="contained"
            color="primary"
          >
            Finalize
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ActiveLearningDashboard;
