import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip, LinearProgress, Grid, Card,
  CardContent, Avatar, Button, TextField, InputAdornment
} from '@mui/material';
import { Search, Person } from '@mui/icons-material';
import { getData } from '../../services/api';

const UserStatistics = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [topPerformers, setTopPerformers] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUserStatistics();
  }, []);

  const fetchUserStatistics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getData('/analytics/user-statistics');
      
      if (response && Array.isArray(response)) {
        setUsers(response);
        // Sort by total votes and get top 3
        const sorted = [...response].sort((a, b) => b.total_votes - a.total_votes);
        setTopPerformers(sorted.slice(0, 3));
      } else {
        setUsers([]);
        setTopPerformers([]);
      }
    } catch (err) {
      console.error('Error fetching user statistics:', err);
      setError('Failed to load user statistics. Please try again later.');
      setUsers([]);
      setTopPerformers([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user =>
    user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading user statistics...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ width: '100%', textAlign: 'center', py: 4 }}>
        <Typography color="error" variant="h6">
          {error}
        </Typography>
        <Button onClick={fetchUserStatistics} sx={{ mt: 2 }} variant="contained">
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Top Performers Cards */}
      <Typography variant="h5" sx={{ mb: 2 }}>
        Top Contributors
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {topPerformers.map((user, index) => (
          <Grid item xs={12} md={4} key={user.user_id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ mr: 2, bgcolor: index === 0 ? 'gold' : index === 1 ? 'silver' : '#cd7f32' }}>
                    {index + 1}
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{user.name}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {user.email}
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Total Labels:</Typography>
                  <Chip 
                    label={user.total_votes} 
                    color="primary"
                    sx={{ fontWeight: 600 }}
                  />
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Agreement Rate:</Typography>
                  <Typography variant="body2">
                    {(user.agreement_with_majority * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Search and Filters */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search users by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            )
          }}
        />
      </Box>

      {/* Detailed User Statistics Table */}
      <Typography variant="h5" sx={{ mb: 2 }}>
        All Users ({filteredUsers.length})
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell align="center">Total Labels</TableCell>
              <TableCell align="center">Agreement Rate</TableCell>
              <TableCell align="center">Last Active</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers.map((user) => (
              <TableRow key={user.user_id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                      <Person />
                    </Avatar>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {user.name}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {user.email}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                
                <TableCell align="center">
                  <Chip
                    label={user.total_votes}
                    color={user.total_votes >= 100 ? 'success' : user.total_votes >= 50 ? 'info' : 'default'}
                    size="small"
                  />
                </TableCell>
                
                <TableCell align="center">
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <LinearProgress
                      variant="determinate"
                      value={user.agreement_with_majority * 100}
                      sx={{ width: 80, mb: 0.5 }}
                      color={user.agreement_with_majority >= 0.8 ? 'success' : user.agreement_with_majority >= 0.6 ? 'warning' : 'error'}
                    />
                    <Typography variant="caption">
                      {(user.agreement_with_majority * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </TableCell>
                
                <TableCell align="center">
                  <Typography variant="body2">
                    {user.last_active ? new Date(user.last_active).toLocaleDateString() : 'Never'}
                  </Typography>
                  {user.last_active && (
                    <Typography variant="caption" color="textSecondary">
                      {new Date(user.last_active).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredUsers.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="textSecondary">
            No users found matching your search criteria.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default UserStatistics;
