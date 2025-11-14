import React from "react";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Container,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableRow,
  TableHead,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Card,
  CardContent,
  Divider,
  CircularProgress,
} from '@mui/material';
import { getData } from "../../services/api";
import SearchTable from "../ui/SearchTable";


const ClientPortfolioTable = ({ clientId }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortOrder, setSortOrder] = useState("name-asc");
  const [currentPage, setCurrentPage] = useState(1);
  const [filterOperator, setFilterOperator] = useState("");
  const [filterValue, setFilterValue] = useState("");
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const entitiesPerPage = 5;

  useEffect(() => {
    const fetchPortfolioData = async () => {
      if (clientId) {
        setLoading(true);
        try {
          const response = await getData(`/portfolio/${clientId}`);
          console.log("Portfolio data:", response);
          setPortfolioData(response);
        } catch (error) {
          console.error("Error fetching portfolio:", error);
          setPortfolioData(null);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchPortfolioData();
  }, [clientId]);

  const rawAllocation = portfolioData?.allocation || [];

  // Apply search filter
  let filteredAllocation = rawAllocation.filter(item =>
    searchTerm === "" || item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Apply sorting
  const sortedAllocation = [...filteredAllocation].sort((a, b) => {
    switch (sortOrder) {
      case 'name-asc':
        return a.name.localeCompare(b.name);
      case 'name-desc':
        return b.name.localeCompare(a.name);
      case 'profit-loss-high':
        return (b.unrealized_pnl || 0) - (a.unrealized_pnl || 0);
      case 'profit-loss-low':
        return (a.unrealized_pnl || 0) - (b.unrealized_pnl || 0);
      default:
        return 0;
    }
  });

  const allocation = sortedAllocation;
  const totalPages = Math.ceil(allocation.length / entitiesPerPage);

  // Sort options for entities
  const sortOptions = [
    { value: 'name-asc', label: 'Name (A-Z)' },
    { value: 'name-desc', label: 'Name (Z-A)' },
    { value: 'profit-loss-high', label: 'Profit Loss (High to Low)' },
    { value: 'profit-loss-low', label: 'Profit Loss (Low to High)' },
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

  // Handle advanced filter change
  const handleFilterChange = (operator, value) => {
    setFilterOperator(operator);
    setFilterValue(value);
    setCurrentPage(1);
  };

  // Render entities table body
  const renderEntitiesTableBody = (data) => {
    // Calculate pagination
    const startIndex = (currentPage - 1) * entitiesPerPage;
    const endIndex = startIndex + entitiesPerPage;
    const paginatedData = data.slice(startIndex, endIndex);

    return (
      <Table>
        <TableHead>
          <TableCell sx={{ fontWeight: 600 }}> Ticker </TableCell>
          <TableCell sx={{ fontWeight: 600 }}> Average Cost Basis </TableCell>
          <TableCell sx={{ fontWeight: 600 }}> Quantity </TableCell>
          <TableCell sx={{ fontWeight: 600 }}> Total Invested </TableCell>
          <TableCell sx={{ fontWeight: 600 }}> Current Market Value </TableCell>
          <TableCell sx={{ fontWeight: 600 }}> Profit-Loss </TableCell>
          <TableCell sx={{ fontWeight: 600 }}> Profit-Loss (%) </TableCell>
        </TableHead>
        <TableBody>
          {paginatedData.map((entity, i) => (
        <TableRow key={i} hover>
          <TableCell>
            {entity.name}
          </TableCell>
          <TableCell>
            ${entity.average_cost_basis?.toFixed(2) || 'N/A'}
          </TableCell>
          <TableCell>
            {entity.quantity || 0}
          </TableCell>
          <TableCell>
            ${entity.total_invested.toFixed(2)}
          </TableCell>
          <TableCell>
            {entity.market_value ? `$${entity.market_value.toFixed(2)}` : 'N/A'}
          </TableCell>
          <TableCell sx={{
            color: entity.unrealized_pnl !== null ? (entity.unrealized_pnl >= 0 ? 'green' : 'red') : 'black'
            }}>
            {entity.unrealized_pnl !== null ? `$${entity.unrealized_pnl.toFixed(2)}` : 'N/A'}
          </TableCell>
          <TableCell sx={{
            color: entity.unrealized_pnl_percent !== null ? (entity.unrealized_pnl_percent >= 0 ? 'green' : 'red') : 'black'
            }}>
            {entity.unrealized_pnl_percent !== null ? `${entity.unrealized_pnl_percent.toFixed(2)}%` : 'N/A'}
          </TableCell>
        </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  };

  if (loading) {
    return (
      <Container maxWidth={false} sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ p: 2, my: 2 }}>
      <SearchTable
        data={allocation}
        loading={loading}
        totalPages={totalPages}
        currentPage={currentPage}
        onPageChange={handlePageChange}
        onSearchChange={handleSearchChange}
        onSortChange={handleSortChange}
        onFilterChange={handleFilterChange}
        searchTerm={searchTerm}
        sortOrder={sortOrder}
        filterOperator={filterOperator}
        filterValue={filterValue}
        searchPlaceholder="Search holdings by ticker..."
        sortOptions={sortOptions}
        renderTableBody={renderEntitiesTableBody}
        itemsPerPage={entitiesPerPage}
        entityType="holdings"
        enableAdvancedFilter={false}
      />
    </Container>
  );
}

export default ClientPortfolioTable