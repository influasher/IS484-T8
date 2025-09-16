import React, { useState } from 'react';
import {
  Container,
  TableBody,
  TableRow,
  TableCell,
  Typography,
  Link as MuiLink,
  Stack,
} from '@mui/material';
import { Link } from 'react-router-dom'; 
import SearchTable from '../ui/SearchTable';
import useFetch from '../../hooks/useFetch';
import SentimentFeedbackForm from '../ui/sentimentFeedback';

const News = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortOrder, setSortOrder] = useState('name-asc');
  const [selectedNews, setSelectedNews] = useState(null);
  const newsPerPage = 5;
  
  // Construct API URL
  const url = `/news/?page=${currentPage}&per_page=${newsPerPage}&sort_order=${sortOrder}&search=${encodeURIComponent(searchTerm)}`;
  const { data, loading, error } = useFetch(url);
  
  const newsData = data ? data.data.news : [];
  const totalPages = data ? data.data.pages : 1;

  // Sort options for news
  const sortOptions = [
    { value: 'name-asc', label: 'Name (A-Z)' },
    { value: 'name-desc', label: 'Name (Z-A)' },
    { value: 'sentiment-high', label: 'Sentiment (High to Low)' },
    { value: 'sentiment-low', label: 'Sentiment (Low to High)' },
  ];

  // Handle search change
  const handleSearchChange = (term) => {
    setSearchTerm(term);
    setCurrentPage(1);
  };

  // Handle sort change
  const handleSortChange = (order) => {
    setSortOrder(order);
    setCurrentPage(1);
  };

  // Handle pagination
  const handlePageChange = (event, pageNumber) => {
    setCurrentPage(pageNumber);
  };

  // Render news table body
  const renderNewsTableBody = (newsData) => (
    <TableBody>
      {newsData.map((news, i) => (
        <TableRow key={i} hover>
          <TableCell
            sx={{
              height: "100px",
              maxHeight: "100px",
              whiteSpace: "normal",
              wordWrap: "break-word",
            }}
          >
            <MuiLink
              component={Link}
              to={`/Individualnewspage/${news.id}`}
              state={{ id: news.id, title: news.title }}
              sx={{
                display: "block",
                textDecoration: "none",
                color: "inherit",
                "&:hover": { textDecoration: "none" },
              }}
              onClick={() => {
                setSelectedNews(news);
                console.log("Selected News:", news);
              }}
            >
              <Stack direction="column" spacing={0.5}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: "bold",
                    color: "text.secondary",
                  }}
                >
                  {news.publisher} |{" "}
                  {new Date(news.published_date).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </Typography>
                <Typography
                  variant="subtitle1"
                  sx={{ color: "text.primary" }}
                >
                  {news.title}
                </Typography>
              </Stack>
            </MuiLink>
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  );

  return (
    <Container maxWidth={false} sx={{ p: 2 }}>
      <SearchTable
        data={newsData}
        loading={loading}
        totalPages={totalPages}
        currentPage={currentPage}
        onPageChange={handlePageChange}
        onSearchChange={handleSearchChange}
        onSortChange={handleSortChange}
        searchTerm={searchTerm}
        sortOrder={sortOrder}
        searchPlaceholder="Search news by title, publisher, or content..."
        sortOptions={sortOptions}
        renderTableBody={renderNewsTableBody}
        itemsPerPage={newsPerPage}
        entityType="news articles"
      />

      {/* Render Sentiment Feedback Form if a news item is selected */}
      {selectedNews && (
        <SentimentFeedbackForm newsTitle={selectedNews.title} />
      )}
    </Container>
  );
};

export default News;