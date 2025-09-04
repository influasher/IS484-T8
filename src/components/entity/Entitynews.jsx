import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import {
  Container,
  Grid,
  Typography,
  Box,
  Pagination,
  CircularProgress,
} from '@mui/material';
import useFetch from "../../hooks/useFetch";
import NewsCard from '../../components/news/NewsCard';

// Main News Component
const News = ({ EntityName }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedNews, setSelectedNews] = useState(null); // State to track selected news
  const newsPerPage = 3; // Matches backend

  // Construct API URL with pagination parameters
  const url = `/news/entity/${EntityName}?page=${currentPage}&per_page=${newsPerPage}`;

  const { data, loading, error } = useFetch(url);

  // Extract news data
  const newsData = data?.data.news ?? [];
  const totalPages = data?.data.pages ?? 1; // Ensure valid number

  const currentNews = newsData; // Directly use API response

  // Filter news based on search term
  const filteredNews = newsData.filter(
    (news) =>
      news.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      news.summary.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle search term change
  const handleSearchChange = (term) => {
    console.log("Search Term:", term); // Check the updated search term
    setSearchTerm(term); // Update search term in the parent component
  };

  console.log("Current Page:", currentPage);
  console.log("Total Pages:", totalPages);
  console.log("Current News Data:", currentNews);

  // Handle pagination
  const handlePageChange = (event, pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  return (
    <Container sx={{ mt: 4 }}>
      {/* News Content */}
      <Grid container spacing={3}>
        {loading ? (
          <Grid item size={12}>
            <Box 
              sx={{
                height: '200px',
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
        ) : currentNews.length > 0 ? (
          currentNews.map((news, index) => (
            <Grid key={news.id || index} item size={4}>
              <NewsCard news={news}/>
            </Grid>
          ))
        ) : (
          <Grid item size={12}>
            <Box 
              sx={{
                height: '200px',
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
