import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from "@mui/material";
import { Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import useFetch from "../../hooks/useFetch";
import { ROUTES } from "../../routes";

const url = "/entities/get_all_tickers";

const TrendChart = ({ data, trend }) => {
  const svgWidth = 97;
  const svgHeight = 40;
  const padding = 8;

  const points = data
    .map((value, index) => {
      const x =
        padding + (index / (data.length - 1)) * (svgWidth - 2 * padding);
      const y = padding + (1 - value / 100) * (svgHeight - 2 * padding);
      return `${x},${y}`;
    })
    .join(" ");

  const color = trend === "up" ? "#2e7d32" : "#d32f2f";

  return (
    <svg width="97" height="40" viewBox={`0 0 ${svgWidth} ${svgHeight}`}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const StockWatchlist = () => {
  const { data: stocks, loading, error } = useFetch(url);
  console.log("Fetched stocks data:", stocks);
  const [data, setData] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Access stocks.data instead of stocks directly
    if (stocks && Array.isArray(stocks.data)) {
      const initialData = stocks.data.map((stock, index) => {
        const price = 100 + Math.random() * 500;
        const change = (Math.random() - 0.5) * 20;
        const changePercent = (change / price) * 100;
        const isPositive = change >= 0;

        return {
          id: index,
          ...stock,
          price,
          change,
          changePercent,
          volume: Math.floor(Math.random() * 10000000),
          trend: isPositive ? "up" : "down",
          trendData: Array.from({ length: 10 }, () => Math.random() * 50 + 50),
        };
      });
      setData(initialData);
    }
  }, [stocks]);

  useEffect(() => {
    const interval = setInterval(() => {
      setData((prevData) =>
        prevData.map((stock) => {
          const priceChange = (Math.random() - 0.5) * 2;
          const newPrice = Math.max(0.01, stock.price + priceChange);
          const change = newPrice - stock.price;
          const changePercent = (change / stock.price) * 100;

          return {
            ...stock,
            price: newPrice,
            change,
            changePercent,
            trend: change >= 0 ? "up" : "down",
          };
        })
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Filter data by name or ticker
  const filteredData = data.filter(
    (stock) =>
      stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.ticker.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatCurrency = (value) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);

  const formatChange = (value) => (value >= 0 ? "+" : "") + value.toFixed(2);

  const formatChangePercent = (value) =>
    (value >= 0 ? "+" : "") + value.toFixed(2) + "%";

  const formatVolume = (value) => new Intl.NumberFormat("en-US").format(value);

  if (loading) {
    return <Typography>Loading...</Typography>;
  }

  if (error) {
    return <Typography>Error: {error}</Typography>;
  }

  return (
    <>
      <Typography variant="h6" sx={{ fontWeight: 500, p: 2 }}>
        Watchlist
      </Typography>
      <Box sx={{ p: 2 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search by company name or ticker..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <Search style={{ marginRight: 8, color: "gray" }} />
            ),
          }}
        />
      </Box>
      {filteredData.length === 0 ? (
        <Box sx={{ p: 2, textAlign: "center", color: "gray" }}>
          No stocks found matching "{searchTerm}"
        </Box>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Ticker</TableCell>
                <TableCell>Company</TableCell>
                <TableCell align="center">Trend</TableCell>
                <TableCell align="right">Price</TableCell>
                <TableCell align="right">Change</TableCell>
                <TableCell align="right">% Change</TableCell>
                <TableCell align="right">Volume</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredData.map((stock) => (
                <TableRow
                  key={stock.id}
                  hover
                  sx={{ cursor: "pointer" }}
                  onClick={() => navigate(`${ROUTES.ENTITY}/${stock.ticker}`)}
                >
                  <TableCell>{stock.ticker}</TableCell>
                  <TableCell>{stock.name}</TableCell>
                  <TableCell align="center">
                    <TrendChart data={stock.trendData} trend={stock.trend} />
                  </TableCell>
                  <TableCell align="right">
                    {formatCurrency(stock.price)}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ color: stock.change >= 0 ? "#2e7d32" : "#d32f2f" }}
                  >
                    {formatChange(stock.change)}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      color: stock.changePercent >= 0 ? "#2e7d32" : "#d32f2f",
                    }}
                  >
                    {formatChangePercent(stock.changePercent)}
                  </TableCell>
                  <TableCell align="right">
                    {formatVolume(stock.volume)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </>
  );
};

export default StockWatchlist;
