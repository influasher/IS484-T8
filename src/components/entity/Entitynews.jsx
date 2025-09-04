import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import { Row, Col } from "react-bootstrap";
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
} from '@mui/material';
import SentimentScore from "../ui/Sentimentscore";
import { Link } from "react-router-dom";
import { useParams } from "react-router-dom";
import useFetch from "../../hooks/useFetch";
import NewsCard from '../../components/news/NewsCard';

// Main News Component
const News = ({ EntityName }) => {
  const styles = {
    newsBox: {
      position: "relative",

      borderRadius: "8px",
      boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
      padding: "20px",
      backgroundColor: "#fff",
      marginBottom: "20px",
      height: "auto", // Allow height to adjust dynamically
      width: "100%", // Full width of the column
      maxWidth: "600px", // Limit maximum width for larger screens
      margin: "0 auto", // Center the box horizontally
      boxSizing: "border-box",
    },
    sentimentScore: {
      display: "inline-block", // Groups SentimentScore and RatingsContainer together
      alignItems: "center", // Aligns items vertically
      justifyContent: "space-between", // Pushes SentimentScore to the left and RatingsContainer to the right
    },
    newsHeader: {
      display: "flex", // Ensures header & sentiment score are in the same row
      justifyContent: "space-between", // Pushes them apart
      alignItems: "center", // Aligns them vertically
      width: "100%", // Ensures full width usage
      flexWrap: "wrap", // Allows wrapping on smaller screens
      fontWeight: "bold",
    },
    newsSummary: {
      fontSize: "clamp(0.8rem, 1vw, 1rem)", // Dynamic font size
      color: "black",
      marginBottom: "5px",
    },
    newsDate: {
      fontSize: "clamp(0.7rem, 0.8vw, 0.9rem)", // Dynamic font size
      color: "black",
      marginBottom: "10px",
    },
    newsLink: {
      fontSize: "clamp(0.9rem, 1vw, 1.1rem)", // Dynamic font size
      color: "blue",
      textDecoration: "none",
    },
    paginationWrapper: {
      display: "flex",
      justifyContent: "center", // Center the pagination items
      marginTop: "20px",
    },
  };

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
  const paginate = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  // Pagination items (Show only a range of pages for better UX)
  const paginationItems = [];
  const pageRange = 5; // Show only 5 page buttons at a time
  let startPage = Math.max(1, currentPage - Math.floor(pageRange / 2));
  let endPage = Math.min(totalPages, startPage + pageRange - 1);

  if (endPage - startPage < pageRange) {
    startPage = Math.max(1, endPage - pageRange + 1);
  }

  for (let number = startPage; number <= endPage; number++) {
    paginationItems.push(
      <Pagination.Item
        key={number}
        active={number === currentPage}
        onClick={() => paginate(number)}
      >
        {number}
      </Pagination.Item>
    );
  }
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
      <Row className="justify-content-center">
        <Col xs={12} md={8} lg={6}>
          <div style={styles.paginationWrapper}>
            <Pagination>
              <Pagination.Prev
                onClick={() => paginate(currentPage - 1)}
                disabled={currentPage === 1}
              />
              {paginationItems}
              <Pagination.Next
                onClick={() => paginate(currentPage + 1)}
                disabled={currentPage === totalPages}
              />
            </Pagination>
          </div>
        </Col>
      </Row>
    </Container>
  );
};

export default News;
