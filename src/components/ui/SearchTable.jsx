import React from "react";
import {
  Box,
  Grid,
  Table,
  TableBody,
  TableContainer,
  TableRow,
  TableCell,
  Paper,
  Typography,
  Stack,
  Pagination,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import { Search, Sort } from "@mui/icons-material";
import { useState } from "react";
import { useEffect } from "react";

function SearchTable({
  data = [],
  loading = false,
  totalPages = 1,
  currentPage = 1,
  onPageChange,
  onSearchChange,
  onSortChange,
  searchTerm = "",
  sortOrder = "",
  searchPlaceholder = "Search...",
  sortOptions = [],
  renderTableBody,
  itemsPerPage = 5,
  entityType = "items",
}) {
  const [internalSearchTerm, setInternalSearchTerm] = useState(searchTerm);
  const [internalSortOrder, setInternalSortOrder] = useState(sortOrder);

  // Update internal state when props change
  useEffect(() => {
    setInternalSearchTerm(searchTerm);
  }, [searchTerm]);

  useEffect(() => {
    setInternalSortOrder(sortOrder);
  }, [sortOrder]);

  // Handle search input change
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setInternalSearchTerm(value);
    if (onSearchChange) {
      onSearchChange(value);
    }
  };

  // Handle sort change
  const handleSortChange = (e) => {
    const value = e.target.value;
    setInternalSortOrder(value);
    if (onSortChange) {
      onSortChange(value);
    }
  };

  // Handle pagination
  const handlePageChange = (event, pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages && onPageChange) {
      onPageChange(event, pageNumber);
    }
  };

  return (
    <div>
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
        <Grid
          container
          spacing={2}
          justifyContent="space-between"
          alignItems="center"
        >
          <Grid item size="grow">
            <TextField
              fullWidth
              variant="outlined"
              placeholder={searchPlaceholder}
              value={internalSearchTerm}
              onChange={handleSearchChange}
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
          {sortOptions.length > 0 && (
            <Grid item size={{ xs: 6, sm: 4, md: 4, lg: 3, xl: 3 }}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="sort-select-label">Sort By</InputLabel>
                <Select
                  labelId="sort-select-label"
                  value={internalSortOrder}
                  onChange={handleSortChange}
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
                  {sortOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}
        </Grid>

        {/* Results Counter */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Showing {data.length} {entityType} on page {currentPage} of{" "}
            {totalPages}
            {internalSearchTerm && ` for "${internalSearchTerm}"`}
          </Typography>
        </Box>
      </Box>

      {/* Table Display */}
      {loading && <Typography>Loading...</Typography>}
      <TableContainer component={Paper} elevation={0}>
        <Table size="small">
          {renderTableBody ? (
            renderTableBody(data)
          ) : (
            <TableBody>
              {data.map((item, i) => (
                <TableRow key={i} hover>
                  <TableCell>
                    <Typography>No custom table body provided</Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          )}
        </Table>
      </TableContainer>

      {/* Pagination */}
      {totalPages > 1 && (
        <Grid container justifyContent="center" sx={{ mt: 4, mb: 4 }}>
          <Grid size={{ xs: 12, md: 8, lg: 6 }}>
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={handlePageChange}
              shape="rounded"
              showFirstButton
              showLastButton
              siblingCount={2}
              boundaryCount={1}
              sx={{
                display: "flex",
                justifyContent: "center",
                "& .MuiPagination-ul": {
                  justifyContent: "center",
                  flexWrap: "nowrap",
                },
                "& .MuiPaginationItem-root.Mui-selected": {
                  backgroundColor: "#212121",
                  color: "#fff",
              },
              }}
            />
          </Grid>
        </Grid>
      )}
    </div>
  );
}

export default SearchTable;