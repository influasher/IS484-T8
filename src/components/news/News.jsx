import React, { useState } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Link as MuiLink,
  Box,
  Pagination,
  CircularProgress,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Search, FilterList } from '@mui/icons-material';
import SentimentScore from '../ui/Sentimentscore';
import { useLocation, Link } from 'react-router-dom'; 
import Filter from "./Filter";
import Sort from './Sort'; 
import useFetch from '../../hooks/useFetch';
import SentimentFeedbackForm from '../ui/sentimentFeedback';

// Main News Component
const News = () => {
  const location = useLocation();
  const [searchTerm, setSearchTerm] = useState(location.state?.search || '');
  const [currentPage, setCurrentPage] = useState(1);
  const [filter, setFilter] = useState("all"); // Default: all time
  const [sortOrder, setSortOrder] = useState('desc'); // Default: descending order
  const [selectedNews, setSelectedNews] = useState(null); // State to track selected news
  const newsPerPage = 4; // Items per page
  
  // Construct API URL with search parameter
  const url = `/news/?page=${currentPage}&per_page=${newsPerPage}&sort_order=${sortOrder}&filter=${filter}&search=${encodeURIComponent(searchTerm)}`;

  const { data, loading, error } = useFetch(url);
  console.log(data);  
  const newsData = data ? data.data.news : [];
  const totalPages = data ? data.data.pages : 1;
  
  console.log("Current Page:", currentPage);
  console.log("Sort Order:", sortOrder);

  // Handle sort order change
  const handleSortChange = (event) => {
    console.log('Sort Order:', event);
    setSortOrder(event);
    setCurrentPage(1); // Reset to first page when sorting
  };  

  // Handle search term change
  const handleSearchChange = (term) => {
    console.log('Search Term:', term);
    setSearchTerm(term);
    setCurrentPage(1); // Reset to first page when searching
  };

  // Handle filter change
  const handleFilterChange = (selectedFilter) => {
    console.log('Selected Filter:', selectedFilter);
    setFilter(selectedFilter);
    setCurrentPage(1); // Reset to first page when filtering
  };

  // Handle pagination
  const handlePageChange = (event, pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  return (
    <Container 
      maxWidth={false}
      sx={{
        maxWidth: '100%',
        width: '100%',
        margin: '0 auto',
        minHeight: 'calc(100vh - 100px)',
        p: 2,
        boxSizing: 'border-box',
      }}
    >
      {/* Search and Filter Controls - matching EntitiesSummary style */}
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
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search news by title, publisher, or content..."
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
          <Grid item xs={6} md={4}>
            <Filter onFilterChange={handleFilterChange} />
          </Grid>
          <Grid item xs={6} md={4}>
            <Sort onSortChange={handleSortChange} />
          </Grid>
        </Grid>
        
        {/* Results Counter */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Showing {newsData.length} news articles on page {currentPage} of {totalPages}
            {searchTerm && ` for "${searchTerm}"`}
          </Typography>
        </Box>
      </Box>

      {/* News Content */}
      <Grid container spacing={3}>
        {loading ? (
          <Grid item xs={12}>
            <Box 
              sx={{
                height: '500px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <CircularProgress size={60} />
              <Typography variant="h6" sx={{ mt: 2 }}>
                Loading...
              </Typography>
            </Box>
          </Grid>
        ) : newsData.length > 0 ? (
          newsData.map((news, index) => (
            <Grid key={news.id || index} item xs={12} sm={6}>
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
                  minHeight: '250px', // Reduced from 400px
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 16px rgba(0, 0, 0, 0.15)',
                  },
                }}
              >
                <CardContent sx={{ p: 0, '&:last-child': { pb: 0 }, flexGrow: 1 }}>
                  {/* News Header */}
                  <Box sx={{ mb: 1 }}> {/* Reduced from mb: 2 */}
                    <Typography variant="h6" sx={{ mb: 0.5 }}> {/* Reduced from mb: 1 */}
                      <MuiLink
                        component={Link}
                        to='/Individualnewspage'
                        state={{ id: news.id, title: news.title }}
                        sx={{
                          fontSize: 'clamp(0.9rem, 2vw, 1.2rem)',
                          fontWeight: 'bold',
                          color: '#1976d2',
                          textDecoration: 'none',
                          '&:hover': {
                            textDecoration: 'underline',
                          },
                        }}
                        onClick={() => {
                          setSelectedNews(news);
                          console.log('Selected News:', news);
                        }}
                      >
                        {news.title}
                      </MuiLink>
                    </Typography>
                    
                    {/* Sentiment Score - aligned to right like in entities */}
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 0.5 }}> {/* Reduced from mb: 1 */}
                      <SentimentScore 
                        score={news.score} 
                        sentiment={news.sentiment} 
                        confidence={news.confidence}
                        finbertScore={news.finbert_score}
                        secondModelScore={news.gemini_score}
                        showDetails={false}
                      />
                    </Box>
                  </Box>

                  {/* Publisher and Date */}
                  <Typography variant="body2" sx={{ mb: 0.5, color: '#666' }}> {/* Reduced from mb: 1 */}
                    <strong>Publisher:</strong> {news.publisher}
                  </Typography>
                  
                  <Typography variant="body2" sx={{ mb: 1, color: '#666' }}> {/* Reduced from mb: 2 */}
                    <strong>Date:</strong> {new Date(news.published_date).toDateString()}
                  </Typography>
                  
                  {/* Summary with text clamping like entities */}
                  <Typography
                    variant="body2"
                    sx={{
                      fontSize: 'clamp(0.8rem, 1.5vw, 1rem)',
                      color: '#555555',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 5, // Increased from 4 to use the saved space
                      WebkitBoxOrient: 'vertical',
                      lineHeight: 1.4, // Slightly tighter line height
                    }}
                    >
                    {news.summary?.length > 300
                      ? `${news.summary.slice(0, 300)}...`
                      : `${news.summary}${' '.repeat(300 - news.summary.length)}`}
                    </Typography>
                  </CardContent>
                  </Card>
                </Grid>
                ))
              ) : (
                <Grid item xs={12}>
                <Box 
                  sx={{
                  height: '500px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  }}
                >
                  <Typography 
                  variant="h6" 
                  align="center" 
                  sx={{ fontSize: '16px', fontWeight: 'bold', color: 'black' }}
                  >
                  No news available.
                  </Typography>
                </Box>
                </Grid>
              )}
              </Grid>

              {/* Render Sentiment Feedback Form if a news item is selected */}
      {selectedNews && (
        <>
          {console.log('Rendering SentimentFeedbackForm with title:', selectedNews.title)}
          <SentimentFeedbackForm newsTitle={selectedNews.title} />
        </>
      )}
      
      {/* Pagination Controls */}
      {totalPages > 1 && (
        <Grid container justifyContent="center" sx={{ mt: 4, mb: 4 }}>
          <Grid item xs={12} md={8} lg={6}>
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
                siblingCount={2}
                boundaryCount={1}
              />
            </Box>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default News;