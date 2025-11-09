import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip, LinearProgress, Grid, Card,
  CardContent, Avatar, Button, TextField, InputAdornment
} from '@mui/material';
import { Search, Person, Star, TrendingUp, Assignment } from '@mui/icons-material';
import { getData } from '../../services/api';

const UserStatistics = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [topPerformers, setTopPerformers] = useState([]);

  // Mock data - in real implementation, this would come from API
  const mockUsers = [
    {
      user_id: '1',
      email: 'admin@example.com',
      name: 'Admin User',
      total_votes: 45,
      gold_standard_correct: 8,
      gold_standard_total: 10,
      reliability_score: 0.92,
      last_active: '2024-01-15T10:30:00Z',
      agreement_with_majority: 0.87
    },
    {
      user_id: '2', 
      email: 'expert@finance.com',
      name: 'Financial Expert',
      total_votes: 128,
      gold_standard_correct: 18,
      gold_standard_total: 20,
      reliability_score: 0.95,
      last_active: '2024-01-16T14:20:00Z',
      agreement_with_majority: 0.91
    },
    {
      user_id: '3',
      email: 'analyst@bank.com', 
      name: 'Market Analyst',
      total_votes: 67,
      gold_standard_correct: 12,
      gold_standard_total: 15,
      reliability_score: 0.85,
      last_active: '2024-01-14T09:15:00Z',
      agreement_with_majority: 0.82
    }
  ];

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setUsers(mockUsers);
      setTopPerformers(mockUsers.sort((a, b) => b.reliability_score - a.reliability_score).slice(0, 3));
      setLoading(false);
    }, 1000);
  }, []);

  const getReliabilityColor = (score) => {
    if (score >= 0.9) return 'success';
    if (score >= 0.75) return 'info';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getReliabilityLabel = (score) => {
    if (score >= 0.9) return 'Excellent';
    if (score >= 0.75) return 'Good';
    if (score >= 0.6) return 'Fair';
    return 'Poor';
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

  return (
    <Box sx={{ width: '100%' }}>
      {/* Top Performers Cards */}
      <Typography variant="h5" sx={{ mb: 2 }}>
        Top Performers
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
                  <Typography variant="body2">Reliability Score:</Typography>
                  <Chip
                    label={`${(user.reliability_score * 100).toFixed(1)}%`}
                    color={getReliabilityColor(user.reliability_score)}
                    size="small"
                  />
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Total Votes:</Typography>
                  <Typography variant="body2">{user.total_votes}</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Gold Standard:</Typography>
                  <Typography variant="body2">
                    {user.gold_standard_correct}/{user.gold_standard_total}
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
              <TableCell align="center">Votes</TableCell>
              <TableCell align="center">Reliability</TableCell>
              <TableCell align="center">Gold Standard</TableCell>
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
                    <Chip
                      label={getReliabilityLabel(user.reliability_score)}
                      color={getReliabilityColor(user.reliability_score)}
                      size="small"
                    />
                    <Typography variant="caption">
                      {(user.reliability_score * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </TableCell>
                
                <TableCell align="center">
                  <Typography variant="body2">
                    {user.gold_standard_correct}/{user.gold_standard_total}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    ({user.gold_standard_total > 0 ? (user.gold_standard_correct / user.gold_standard_total * 100).toFixed(1) : 0}%)
                  </Typography>
                </TableCell>
                
                <TableCell align="center">
                  <LinearProgress
                    variant="determinate"
                    value={user.agreement_with_majority * 100}
                    sx={{ width: 60, mr: 1 }}
                  />
                  <Typography variant="caption">
                    {(user.agreement_with_majority * 100).toFixed(1)}%
                  </Typography>
                </TableCell>
                
                <TableCell align="center">
                  <Typography variant="body2">
                    {new Date(user.last_active).toLocaleDateString()}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {new Date(user.last_active).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Typography>
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
