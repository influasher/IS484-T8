import React, { useState, useMemo } from "react";
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
  Pagination,
  CircularProgress,
} from "@mui/material";
import { Search, Sort } from "@mui/icons-material";
import SentimentScore from "../ui/Sentimentscore";
import { Link } from "react-router-dom";
import useFetch from "../../hooks/useFetch";

const Entities = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortOrder, setSortOrder] = useState("name-asc");
  const [currentPage, setCurrentPage] = useState(1);
  const entitiesPerPage = 4; // Items per page

  const url = `/entities/?page=${currentPage}&per_page=${entitiesPerPage}&sort_order=${sortOrder}&search=${encodeURIComponent(searchTerm)}`;

  const { data, loading, error } = useFetch(url);
  console.log(data)
  const entityData = data ? data.data.entities : [];
  const totalPages = data ? data.data.pages : 1;

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
        maxWidth: "100%",
        width: "100%",
        margin: "0 auto",
        minHeight: "calc(100vh - 100px)",
        p: 2,
        boxSizing: "border-box",
      }}
    >
      {/* Search and Filter Controls */}
      <Box
        sx={{
          p: 2,
          mb: 3,
          borderRadius: 2,
          backgroundColor: "#fafafa",
          border: 1,
          borderColor: "grey.300",
          boxShadow: 1,
        }}
      >
        <Grid container spacing={2} justifyContent="space-between" alignItems="center">
          <Grid item size="grow">
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
                "& .MuiOutlinedInput-root": {
                  backgroundColor: "white",
                },
              }}
            />
          </Grid>
          <Grid item size={{ xs: 6, sm: 4, md: 4, lg: 3, xl: 3 }}>
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
                  backgroundColor: "white",
                }}
              >
                <MenuItem value="name-asc">Name (A-Z)</MenuItem>
                <MenuItem value="name-desc">Name (Z-A)</MenuItem>
                <MenuItem value="sentiment-high">
                  Sentiment (High to Low)
                </MenuItem>
                <MenuItem value="sentiment-low">
                  Sentiment (Low to High)
                </MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Results Counter */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Showing {entityData.length} entities on page {currentPage} of {totalPages}
            {searchTerm && ` for "${searchTerm}"`}
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {loading ? (
          <Grid item xs={12}>
            <Box
              sx={{
                height: "500px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CircularProgress size={60} />
              <Typography variant="h6" sx={{ mt: 2 }}>
                Loading...
              </Typography>
            </Box>
          </Grid>
        ) : entityData.length > 0 ? (
          entityData.map((entityItem) => (
            <Grid key={entityItem.id} item xs={6} sm={4} md={4} lg={3} xl={3}>
              {/* xs: 6, sm: 4, md: 4, lg: 3, xl: 3 */}
              <MuiLink
                component={Link}
                to={`/entity/${entityItem.ticker}`}
                sx={{ textDecoration: "none" }}
              >
                <Card
                  sx={{
                    p: 2,
                    border: 1,
                    borderColor: "grey.300",
                    borderRadius: 2,
                    backgroundColor: "white",
                    boxShadow: 2,
                    transition: "transform 0.3s ease, box-shadow 0.3s ease",
                    width: "100%",
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    minHeight: "250px",
                    "&:hover": {
                      transform: "translateY(-2px)",
                      boxShadow: 3,
                    },
                  }}
                >
                  <CardContent sx={{ p: 0, "&:last-child": { pb: 0 }, width: '100%' }}>
                    {/* Entity Header */}
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        mb: 1,
                      }}
                    >
                      <Typography
                        variant="h6"
                        component="h4"
                        sx={{
                          fontSize: "clamp(1rem, 2vw, 1.5rem)",
                          fontWeight: "bold",
                          color: "black",
                          mr: 2,
                        }}
                      >
                        {entityItem.name}
                      </Typography>
                      <Box sx={{ ml: "auto" }}>
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
                        whiteSpace: 'pre-wrap', // Preserve spaces and wrap text
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 5, // Increased from 4 to use the saved space
                        WebkitBoxOrient: 'vertical',
                        lineHeight: 1.4, // Slightly tighter line height
                      }}
                    >
                      {entityItem.summary.padEnd(200, ' ')} {/* Pad summary to a fixed length */}
                    </Typography>
                  </CardContent>
                </Card>
              </MuiLink>
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
                No entities available.
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

export default Entities;
