import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Card, CardContent, Alert, LinearProgress,
  List, ListItem, ListItemIcon, ListItemText, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Chip, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions,
  Accordion, AccordionSummary, AccordionDetails, IconButton, Tooltip
} from '@mui/material';
import {
  CheckCircle, Warning, Error, Info, TrendingUp,
  Schedule, Refresh, Download, DataObject, BarChart,
  ExpandMore, History, Delete, PlayArrow
} from '@mui/icons-material';
import { getData, postData } from '../../services/api';

const ModelTraining = ({ stats }) => {
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exportStats, setExportStats] = useState(null);
  const [downloading, setDownloading] = useState(false);
  
  // NEW: Training history and auto-trigger states
  const [trainingHistory, setTrainingHistory] = useState([]);
  const [showTrainingDialog, setShowTrainingDialog] = useState(false);
  const [trainingInProgress, setTrainingInProgress] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, modelId: null });
  const [cleanupDialog, setCleanupDialog] = useState({ open: false, type: null });
  const [confirmPhrase, setConfirmPhrase] = useState('');

  const fetchExportStats = async () => {
    try {
      const response = await getData('/labeling/export/stats');
      if (response?.status === 200) {
        setExportStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching export stats:', error);
    }
  };

  const downloadLabeledData = async () => {
    setDownloading(true);
    try {
      // Use full URL to ensure we hit the backend, not React router
      const apiUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5001';
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${apiUrl}/api/labeling/export`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/csv',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Export failed:', errorText);
        throw new Error(`Export failed: ${response.status}`);
      }

      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
      const filename = filenameMatch ? filenameMatch[1] : `labeled_data_${new Date().toISOString().split('T')[0]}.csv`;

      const blob = await response.blob();
      
      // Verify it's actually CSV
      const text = await blob.text();
      if (text.trim().startsWith('<!DOCTYPE html>') || text.trim().startsWith('<html')) {
        throw new Error('Received HTML instead of CSV - check API endpoint');
      }
      
      // Re-create blob from text for download
      const csvBlob = new Blob([text], { type: 'text/csv' });
      const url = window.URL.createObjectURL(csvBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      console.log('Export successful:', filename);
      alert(`Downloaded ${filename} successfully!`);
    } catch (error) {
      console.error('Error downloading labeled data:', error);
      alert(`Failed to download: ${error.message}`);
    } finally {
      setDownloading(false);
    }
  };

  // Fetch training history
  const fetchTrainingHistory = async () => {
    try {
      const response = await getData('/labeling/training-history');
      if (response?.status === 200) {
        setTrainingHistory(response.data);
      }
    } catch (error) {
      console.error('Error fetching training history:', error);
    }
  };

  // NEW: Trigger retraining
  const triggerRetraining = async () => {
    setTrainingInProgress(true);
    try {
      const response = await postData('/labeling/trigger-retrain', {});
      if (response?.status === 200) {
        alert('Retraining job started successfully! Check the backend logs for progress.');
        await fetchTrainingHistory();
        await fetchExportStats();
      } else {
        alert(`Failed to start retraining: ${response?.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error triggering retraining:', error);
      alert('Failed to start retraining job. Please check server logs.');
    } finally {
      setTrainingInProgress(false);
      setShowTrainingDialog(false);
    }
  };

  // Delete old model
  const deleteOldModel = async (modelId) => {
    try {
      const response = await postData(`/labeling/delete-model/${modelId}`, {});
      if (response?.status === 200) {
        alert('Model deleted successfully');
        await fetchTrainingHistory();
      } else {
        alert('Failed to delete model');
      }
    } catch (error) {
      console.error('Error deleting model:', error);
      alert('Failed to delete model');
    } finally {
      setDeleteDialog({ open: false, modelId: null });
    }
  };

  // Archive labels
  const archiveLabels = async (clearAfter = false) => {
    try {
      const response = await postData('/labeling/archive-labels', {
        clear_after_archive: clearAfter
      });
      
      if (response?.status === 200) {
        alert(`Archived ${response.data.archived_count} labels${clearAfter ? ` and cleared ${response.data.cleared_count} from database` : ''}`);
        await refreshData();
      } else {
        alert('Failed to archive labels');
      }
    } catch (error) {
      console.error('Error archiving labels:', error);
      alert('Failed to archive labels');
    } finally {
      setCleanupDialog({ open: false, type: null });
    }
  };

  // Clear queue
  const clearQueue = async (olderThanDays = null) => {
    try {
      const response = await postData('/labeling/clear-queue', {
        confirm: true,
        older_than_days: olderThanDays
      });
      
      if (response?.status === 200) {
        alert(`Cleared ${response.data.cleared_count} pending items`);
        await refreshData();
      } else {
        alert('Failed to clear queue');
      }
    } catch (error) {
      console.error('Error clearing queue:', error);
      alert('Failed to clear queue');
    } finally {
      setCleanupDialog({ open: false, type: null });
    }
  };

  // Reset votes
  const resetVotes = async () => {
    try {
      const response = await postData('/labeling/reset-votes', {
        confirm: true
      });
      
      if (response?.status === 200) {
        alert(`Reset ${response.data.votes_deleted} votes`);
        await refreshData();
      } else {
        alert('Failed to reset votes');
      }
    } catch (error) {
      console.error('Error resetting votes:', error);
      alert('Failed to reset votes');
    } finally {
      setCleanupDialog({ open: false, type: null });
      setConfirmPhrase('');
    }
  };

  const calculateSystemMetrics = () => {
    if (!stats) return null;

    const totalItems = stats.completed_count;
    const votesPerUser = stats.unique_users > 0 ? stats.total_votes / stats.unique_users : 0;
    
    return {
      totalItems,
      votesPerUser,
      agreementRate: stats.avg_agreement_rate * 100,
    };
  };

  useEffect(() => {
    fetchExportStats();
    fetchTrainingHistory(); // Fetch training history on mount
    if (stats) {
      setSystemMetrics(calculateSystemMetrics());
    }
  }, [stats]);

  const refreshData = async () => {
    setLoading(true);
    try {
      await fetchExportStats();
      await fetchTrainingHistory();
    } finally {
      setLoading(false);
    }
  };

  if (!stats || !systemMetrics) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
        <Typography>Loading Model Training data...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Remove Completion Rate card - only show relevant metrics */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%', minHeight: 190 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Schedule sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Avg Votes/User</Typography>
              </Box>
              
              <Typography variant="h3" color="warning.main">
                {systemMetrics.votesPerUser.toFixed(1)}
              </Typography>
              
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                {stats.total_votes} votes by {stats.unique_users} users
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%', minHeight: 190 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Label Agreement</Typography>
              </Box>
              
              <Typography variant="h3" color="info.main">
                {systemMetrics.agreementRate.toFixed(1)}%
              </Typography>
              
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Average agreement across {stats.completed_count} samples
              </Typography>
              
              <LinearProgress
                variant="determinate"
                value={systemMetrics.agreementRate}
                color="info"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* NEW: Export Statistics Section */}
      {exportStats && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Training Data Export
          </Typography>
          
          <Grid container spacing={3}>
            {/* Total Completed Labels */}
            <Grid item xs={12} md={3}>
              <Card sx={{ height: '100%', minHeight: 160 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <DataObject sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="h6">Total Labels</Typography>
                  </Box>
                  
                  <Typography variant="h3" color="primary.main">
                    {exportStats.total_completed}
                  </Typography>
                  
                  <Typography variant="body2" color="textSecondary">
                    Completed labels
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* New Labels Since Training */}
            <Grid item xs={12} md={3}>
              <Card sx={{ height: '100%', minHeight: 160 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TrendingUp sx={{ mr: 1, color: exportStats.ready_for_retraining ? 'success.main' : 'info.main' }} />
                    <Typography variant="h6">New Labels</Typography>
                  </Box>
                  
                  <Typography variant="h3" color={exportStats.ready_for_retraining ? 'success.main' : 'info.main'}>
                    {exportStats.new_samples_since_last_training}
                  </Typography>
                  
                  <Typography variant="body2" color="textSecondary">
                    Since last training
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Label Distribution */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%', minHeight: 160 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <BarChart sx={{ mr: 1, color: 'info.main' }} />
                    <Typography variant="h6">Label Distribution</Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    {Object.entries(exportStats.label_distribution || {}).map(([label, count]) => (
                      <Box key={label} sx={{ flex: 1, minWidth: 100 }}>
                        <Typography variant="caption" color="textSecondary" sx={{ textTransform: 'capitalize' }}>
                          {label}
                        </Typography>
                        <Typography variant="h5" color={
                          label === 'bullish' ? 'success.main' : 
                          label === 'bearish' ? 'error.main' : 
                          'warning.main'
                        }>
                          {count}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                  
                  {exportStats.last_training_date && (
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
                      Last trained: {new Date(exportStats.last_training_date).toLocaleString()}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* NEW: Progress Indicator */}
            <Grid item xs={12}>
              <Card sx={{ height: '100%', minHeight: 160 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TrendingUp sx={{ mr: 1, color: 'info.main' }} />
                    <Typography variant="h6">Retraining Progress</Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="textSecondary">
                        Labeled Samples: {exportStats.new_samples_since_last_training} / 20
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {((exportStats.new_samples_since_last_training / 20) * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.min((exportStats.new_samples_since_last_training / 20) * 100, 100)}
                      color={exportStats.ready_for_retraining ? 'success' : 'primary'}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                  
                  {exportStats.ready_for_retraining ? (
                    <Chip 
                      label="Ready for Retraining!" 
                      color="success" 
                      icon={<CheckCircle />}
                    />
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      {20 - exportStats.new_samples_since_last_training} more samples needed
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Export Button + Auto-Trigger Button */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={downloading ? <CircularProgress size={20} /> : <Download />}
                  onClick={downloadLabeledData}
                  disabled={downloading || exportStats.total_completed === 0}
                  size="large"
                >
                  {downloading ? 'Downloading...' : 'Download Labeled Data (CSV)'}
                </Button>
                
                {/* NEW: Auto-Trigger Retraining Button */}
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={trainingInProgress ? <CircularProgress size={20} /> : <PlayArrow />}
                  onClick={() => setShowTrainingDialog(true)}
                  disabled={!exportStats.ready_for_retraining || trainingInProgress}
                  size="large"
                >
                  {trainingInProgress ? 'Training...' : 'Start Retraining'}
                </Button>
                
                <Typography variant="body2" color="textSecondary">
                  {exportStats.total_completed === 0 ? 
                    'No labeled data available' : 
                    `${exportStats.total_completed} samples ready for export`
                  }
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* NEW: Training History Accordion */}
      {trainingHistory.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <History />
                <Typography variant="h6">Training History ({trainingHistory.length} runs)</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Version</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>Samples</TableCell>
                      <TableCell>Accuracy</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {trainingHistory.map((run) => (
                      <TableRow key={run.id}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {run.model_version}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {new Date(run.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell>{run.training_samples}</TableCell>
                        <TableCell>
                          <Chip 
                            label={`${(run.performance_metrics?.accuracy * 100).toFixed(1)}%`}
                            size="small"
                            color={run.performance_metrics?.accuracy >= 0.8 ? 'success' : 'warning'}
                          />
                        </TableCell>
                        <TableCell>
                          {run.is_active ? (
                            <Chip label="Active" color="success" size="small" />
                          ) : (
                            <Chip label="Inactive" size="small" />
                          )}
                        </TableCell>
                        <TableCell>
                          {!run.is_active && (
                            <Tooltip title="Delete this model">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => setDeleteDialog({ open: true, modelId: run.id })}
                              >
                                <Delete fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      {/* Alerts and Warnings - Remove pending queue alerts */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          System Alerts
        </Typography>
        
        {stats.avg_agreement_rate < 0.7 && (
          <Alert severity="warning" sx={{ mb: 2 }} icon={<Warning />}>
            <strong>Low Agreement:</strong> Average agreement rate is {(stats.avg_agreement_rate * 100).toFixed(1)}%. 
            Consider reviewing annotation guidelines.
          </Alert>
        )}
        
        {exportStats?.ready_for_retraining && (
          <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>
            <strong>Ready for Retraining:</strong> {exportStats.new_samples_since_last_training} new labels collected. 
            Model retraining is recommended. 
            <Button 
              size="small" 
              sx={{ ml: 2 }} 
              variant="outlined" 
              startIcon={<Download />}
              onClick={downloadLabeledData}
              disabled={downloading}
            >
              Export Training Data
            </Button>
          </Alert>
        )}
        
        {/* Default message if no alerts */}
        {stats.avg_agreement_rate >= 0.7 && 
         !exportStats?.ready_for_retraining && (
          <Alert severity="success" icon={<CheckCircle />}>
            All systems operating normally. No immediate action required.
          </Alert>
        )}
      </Box>

      {/* Detailed Metrics Table - Remove pending-related metrics */}
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
                <TableCell>Total Labeled Samples</TableCell>
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
              
              {exportStats && (
                <TableRow>
                  <TableCell>New Labels Since Last Training</TableCell>
                  <TableCell align="right">{exportStats.new_samples_since_last_training}</TableCell>
                  <TableCell>
                    {exportStats.ready_for_retraining ? 
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

      {/* NEW: Retraining Confirmation Dialog */}
      <Dialog open={showTrainingDialog} onClose={() => setShowTrainingDialog(false)}>
        <DialogTitle>Start Model Retraining?</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            This will start the meta-classifier retraining job using {exportStats?.total_completed} labeled samples.
          </Typography>
          <Typography paragraph>
            <strong>What will happen:</strong>
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="Export labeled data from database" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="Train Random Forest meta-classifier" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="Save new model and mark as active" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
              <ListItemText primary="Future predictions will use new model" />
            </ListItem>
          </List>
          <Alert severity="info" sx={{ mt: 2 }}>
            Training may take 2-5 minutes. Check backend logs for progress.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTrainingDialog(false)}>
            Cancel
          </Button>
          <Button 
            onClick={triggerRetraining} 
            variant="contained" 
            color="primary"
            disabled={trainingInProgress}
          >
            {trainingInProgress ? 'Training...' : 'Start Training'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* NEW: Delete Model Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false, modelId: null })}>
        <DialogTitle>Delete Old Model?</DialogTitle>
        <DialogContent>
          <Typography>
            This will permanently delete the model file and database record. This action cannot be undone.
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            Only delete old models if you're sure they won't be needed for rollback.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, modelId: null })}>
            Cancel
          </Button>
          <Button 
            onClick={() => deleteOldModel(deleteDialog.modelId)} 
            variant="contained" 
            color="error"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* NEW: Data Management Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Data Management
        </Typography>
        
        <Grid container spacing={2}>
          {/* Archive Completed Labels */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Archive Completed Labels
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Export completed labels to CSV. Optionally clear from database to free space.
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    onClick={() => setCleanupDialog({ open: true, type: 'archive' })}
                    startIcon={<Download />}
                  >
                    Archive Only
                  </Button>
                  <Button
                    variant="outlined"
                    color="warning"
                    onClick={() => setCleanupDialog({ open: true, type: 'archive-clear' })}
                    startIcon={<Delete />}
                  >
                    Archive & Clear
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Reset User Votes */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Reset User Votes
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Clear all user votes and statistics. Cannot be undone!
                </Typography>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={() => setCleanupDialog({ open: true, type: 'reset-votes' })}
                  startIcon={<Warning />}
                >
                  Reset Votes
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* NEW: Cleanup Confirmation Dialogs */}
      <Dialog 
        open={cleanupDialog.open} 
        onClose={() => {
          setCleanupDialog({ open: false, type: null });
          setConfirmPhrase('');
        }}
      >
        <DialogTitle>
          {cleanupDialog.type === 'archive' && 'Archive Completed Labels'}
          {cleanupDialog.type === 'archive-clear' && 'Archive & Clear Labels'}
          {cleanupDialog.type === 'clear-queue' && 'Clear Pending Queue'}
          {cleanupDialog.type === 'reset-votes' && 'Reset User Votes'}
        </DialogTitle>
        <DialogContent>
          {cleanupDialog.type === 'archive' && (
            <Typography>
              This will export all completed labels to a CSV file. Database records will remain unchanged.
            </Typography>
          )}
          
          {cleanupDialog.type === 'archive-clear' && (
            <>
              <Typography paragraph>
                This will:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                  <ListItemText primary="Export labels to CSV" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Delete color="warning" /></ListItemIcon>
                  <ListItemText primary="Clear labels from database" />
                </ListItem>
              </List>
              <Alert severity="warning" sx={{ mt: 2 }}>
                Cleared data can only be recovered from CSV archive!
              </Alert>
            </>
          )}
          
          {cleanupDialog.type === 'clear-queue' && (
            <>
              <Typography paragraph>
                This will remove all pending items from the labeling queue.
              </Typography>
              <Alert severity="warning">
                Pending items will be permanently deleted. This cannot be undone.
              </Alert>
            </>
          )}
          
          {cleanupDialog.type === 'reset-votes' && (
            <>
              <Typography paragraph>
                This will:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><Delete color="error" /></ListItemIcon>
                  <ListItemText primary="Delete all user votes" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Delete color="error" /></ListItemIcon>
                  <ListItemText primary="Reset all user statistics" />
                </ListItem>
              </List>
              <Alert severity="error" sx={{ mt: 2 }}>
                This cannot be undone! All voting history will be lost.
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCleanupDialog({ open: false, type: null });
            setConfirmPhrase('');
          }}>
            Cancel
          </Button>
          <Button 
            onClick={() => {
              if (cleanupDialog.type === 'archive') archiveLabels(false);
              else if (cleanupDialog.type === 'archive-clear') archiveLabels(true);
              else if (cleanupDialog.type === 'clear-queue') clearQueue();
              else if (cleanupDialog.type === 'reset-votes') resetVotes();
            }}
            variant="contained"
            color={cleanupDialog.type === 'archive' ? 'primary' : 'error'}
          >
            {cleanupDialog.type === 'archive' ? 'Archive' : 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ModelTraining;
