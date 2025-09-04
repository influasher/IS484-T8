import React, { useState, useMemo } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Link as MuiLink,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Search, Sort } from '@mui/icons-material';
import SentimentScore from '../ui/Sentimentscore';
import { Link } from 'react-router-dom'; 
import useFetch from '../../hooks/useFetch';

const Entities = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState('name-asc');
  
  const url = `/entities/`;
  const { data, loading, error } = useFetch(url);
  const entityData = data ? data.data : [];

  // Filter and sort entities based on search term and sort order
  const filteredAndSortedEntities = useMemo(() => {
    let filtered = entityData.filter(entity =>
      entity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entity.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entity.ticker.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return filtered.sort((a, b) => {
      switch (sortOrder) {
        case 'name-asc':
          return a.name.localeCompare(b.name);
        case 'name-desc':
          return b.name.localeCompare(a.name);
        case 'sentiment-high':
          return parseFloat(b.sentiment_score || 0) - parseFloat(a.sentiment_score || 0);
        case 'sentiment-low':
          return parseFloat(a.sentiment_score || 0) - parseFloat(b.sentiment_score || 0);
        default:
          return 0;
      }
    });
  }, [entityData, searchTerm, sortOrder]);

  return ( 
    <Container 
      maxWidth={false}
      sx={{
        maxWidth: '100%',
        width: '100%',
        margin: '0 auto',
        height: 'calc(100vh - 100px)',
        overflowY: 'auto',
        p: 2,
        boxSizing: 'border-box',
      }}
    >
      {/* Search and Filter Controls */}
      <Box 
        sx={{ 
          p: 2, 
          mb: 3,
          borderRadius: 2,
          backgroundColor: '#fafafa',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search entities by name, ticker, or summary..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search color="action" />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: 'white',
                },
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth variant="outlined">
              <InputLabel id="sort-select-label">Sort By</InputLabel>
              <Select
                labelId="sort-select-label"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                label="Sort By"
                startAdornment={
                  <InputAdornment position="start" sx={{ ml: 1 }}>
                    <Sort color="action" />
                  </InputAdornment>
                }
                sx={{
                  backgroundColor: 'white',
                }}
              >
                <MenuItem value="name-asc">Name (A-Z)</MenuItem>
                <MenuItem value="name-desc">Name (Z-A)</MenuItem>
                <MenuItem value="sentiment-high">Sentiment (High to Low)</MenuItem>
                <MenuItem value="sentiment-low">Sentiment (Low to High)</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        
        {/* Results Counter */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Showing {filteredAndSortedEntities.length} of {entityData.length} entities
            {searchTerm && ` for "${searchTerm}"`}
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {filteredAndSortedEntities.map((entityItem) => (
          <Grid key={entityItem.id} item xs={12} sm={6} lg={4} xl={3}>
            <MuiLink 
              component={Link}
              to={`/entity/${entityItem.ticker}`} 
              sx={{ textDecoration: 'none' }}
            >
              <Card
                sx={{
                  p: 2,
                  border: '1px solid #ddd',
                  borderRadius: '12px',
                  backgroundColor: '#fff',
                  boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
                  transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minHeight: '300px',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 16px rgba(0, 0, 0, 0.15)',
                  },
                }}
              >
                <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
                  {/* Entity Header */}
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1,
                    }}
                  >
                    <Typography
                      variant="h6"
                      component="h4"
                      sx={{
                        fontSize: 'clamp(1rem, 2vw, 1.5rem)',
                        fontWeight: 'bold',
                        color: 'black',
                        mr: 2,
                      }}
                    >
                      {entityItem.name}
                    </Typography>
                    <Box sx={{ ml: 'auto' }}>
                      <SentimentScore 
                        score={entityItem.sentiment_score} 
                        sentiment={entityItem.classification}  
                      />
                    </Box>
                  </Box>

                  {/* Entity Summary */}
                  <Typography
                    variant="body2"
                    sx={{
                      fontSize: 'clamp(0.8rem, 1.5vw, 1rem)',
                      color: '#555555',
                      flexGrow: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 5,
                      WebkitBoxOrient: 'vertical',
                      m: 0,
                      p: 0,
                    }}
                  >
                    {entityItem.summary}
                  </Typography>
                </CardContent>
              </Card>
            </MuiLink>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default Entities