import React, { useState } from "react";
import {
  Container,
  TableBody,
  TableRow,
  TableCell,
  Typography,
  Link as MuiLink,
  Stack,
  Box,
} from "@mui/material";
import { Link } from "react-router-dom";
import SearchTable from '../ui/SearchTable';
import SentimentScore from "../ui/Sentimentscore";
import useFetch from "../../hooks/useFetch";
import { ROUTES } from "../../routes";

const Entities = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortOrder, setSortOrder] = useState("name-asc");
  const [currentPage, setCurrentPage] = useState(1);
  const entitiesPerPage = 5;

  const url = `/entities/?page=${currentPage}&per_page=${entitiesPerPage}&sort_order=${sortOrder}&search=${encodeURIComponent(searchTerm)}`;
  const { data, loading, error } = useFetch(url);
  
  const entityData = data ? data.data.entities : [];
  const totalPages = data ? data.data.pages : 1;

  // Sort options for entities
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

  // Render entities table body
  const renderEntitiesTableBody = (entityData) => (
    <TableBody>
      {entityData.map((entity, i) => (
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
              to={`${ROUTES.ENTITY}/${entity.ticker}`}
              sx={{
                display: "block",
                textDecoration: "none",
                color: "inherit",
                "&:hover": { textDecoration: "none" },
              }}
            >
              <Stack direction="column" spacing={0.5}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: "bold",
                      color: "text.secondary",
                    }}
                  >
                    {entity.ticker || 'N/A'}
                  </Typography>
                  <SentimentScore
                    score={entity.sentiment_score}
                    sentiment={entity.classification}
                  />
                </Box>
                <Typography
                  variant="subtitle1"
                  sx={{ color: "text.primary", fontWeight: "bold" }}
                >
                  {entity.name}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: "text.secondary",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                  }}
                >
                  {entity.summary}
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
        data={entityData}
        loading={loading}
        totalPages={totalPages}
        currentPage={currentPage}
        onPageChange={handlePageChange}
        onSearchChange={handleSearchChange}
        onSortChange={handleSortChange}
        searchTerm={searchTerm}
        sortOrder={sortOrder}
        searchPlaceholder="Search entities by name, ticker, or summary..."
        sortOptions={sortOptions}
        renderTableBody={renderEntitiesTableBody}
        itemsPerPage={entitiesPerPage}
        entityType="entities"
      />
    </Container>
  );
};

export default Entities;