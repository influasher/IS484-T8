import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col, Pagination } from 'react-bootstrap';
import SentimentScore from '../ui/Sentimentscore';
import { Link } from 'react-router-dom'; 
import { useParams } from 'react-router-dom';
// import SearchBar from '../ui/Searchbar';
import useFetch from '../../hooks/useFetch';

// Main News Component
const News = ( {EntityName} ) => {
  const styles = {

    newsBox: {
      position: 'relative',

      borderRadius: '8px',
      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
      padding: '20px',
      backgroundColor: '#fff',
      marginBottom: '20px',
      height: 'auto', // Allow height to adjust dynamically
      width: '100%', // Full width of the column
      maxWidth: '600px', // Limit maximum width for larger screens
      margin: '0 auto', // Center the box horizontally
      boxSizing: 'border-box',
    },
    sentimentScore: {
      display: 'inline-block', // Groups SentimentScore and RatingsContainer together
      alignItems: 'center', // Aligns items vertically
      justifyContent: 'space-between', // Pushes SentimentScore to the left and RatingsContainer to the right
    },    
    newsHeader:  {
      display: 'flex', // Ensures header & sentiment score are in the same row
      justifyContent: 'space-between', // Pushes them apart
      alignItems: 'center', // Aligns them vertically
      width: '100%', // Ensures full width usage
      flexWrap: 'wrap', // Allows wrapping on smaller screens
      fontWeight: 'bold'
    },
    newsSummary: {
      fontSize: 'clamp(0.8rem, 1vw, 1rem)', // Dynamic font size
      color: 'black',
      marginBottom: '5px',
    },
    newsDate: {
      fontSize: 'clamp(0.7rem, 0.8vw, 0.9rem)', // Dynamic font size
      color: 'black',
      marginBottom: '10px',
    },
    newsLink: {
      fontSize: 'clamp(0.9rem, 1vw, 1.1rem)', // Dynamic font size
      color: 'blue',
      textDecoration: 'none',
    },
    paginationWrapper: {
      display: 'flex',
      justifyContent: 'center', // Center the pagination items
      marginTop: '20px',

  }}

  const [searchTerm, setSearchTerm] = useState('');
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
  const filteredNews = newsData.filter((news) =>
    news.title.toLowerCase().includes(searchTerm.toLowerCase()) 
    || news.summary.toLowerCase().includes(searchTerm.toLowerCase())
  );

    // Handle search term change
    const handleSearchChange = (term) => {
    console.log('Search Term:', term);  // Check the updated search term
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
    <Container fluid>
      {/* Search Bar */}
      <Row className="justify-content-center mt-4">
  <Col xs={12} md={6}> {/* Reduced column width from md={8} to md={6} */}
    {/* <div style={styles.searchBarContainer}>
      <SearchBar onSearchChange={handleSearchChange} />
    </div> */}
  </Col>
</Row>

      {/* News Content */}
      <Row className=" justify-content-center mt-4">
        {currentNews.map((news, index) => {
          if (!news) {
            console.warn(`News item at index ${index} is missing or undefined`);
            return null;
          }

          return (
            <Col key={news.id || index} xs={12} sm={6} md={4} lg={3} className="mb-4 d-flex justify-content-center">
              <div style={styles.newsBox}>

                <h4 style={styles.newsHeader}>
                  {/* <Link to={news.url} target="_blank" rel="noopener noreferrer" style={styles.newsLink}>
                    {news.title}
                  </Link> */}
                      <Link
                    to='/Individualnewspage'
                    state={{ id: news.id , title: news.title }}
                    rel="noopener noreferrer"
                    style={styles.newsLink}
                    
                  // After selecting a news item
                    onClick={() => {
                      setSelectedNews(news);
                      console.log('Selected News:', news); // Debugging state change
                    }}                  >
                    {news.title}
                  </Link>
                </h4>
                <div style={styles.sentimentScore}>
                    <SentimentScore score={news.score} sentiment = {news.sentiment} />
                  </div>
                <p style={styles.newsSummary}><strong>Publisher:</strong> {news.publisher}</p>
                <p style={styles.newsDate}><strong>Date:</strong> {new Date(news.published_date).toDateString()}</p>
                <p style={styles.newsSummary}>{news.summary?.length > 300 ? `${news.summary.slice(0, 300)}...` : news.summary}</p>
                {/* SentimentScore component */}
              </div>
            </Col>
          );
        })}
      </Row>

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