import React, { useState } from "react";
import { Container, Box, Typography, ToggleButton, ToggleButtonGroup } from "@mui/material";
import { LineChart } from "@mui/x-charts/LineChart";
import useFetch from "../../hooks/useFetch"; // Adjust path if needed

function EntityVisuals({ id }) {
  const [timeRange, setTimeRange] = useState('1Y'); // Default to 1 year

  const timeRanges = [
    { value: '1D', label: '1D' },
    { value: '1W', label: '1W' },
    { value: '1M', label: '1M' },
    { value: '3M', label: '3M' },
    { value: '6M', label: '6M' },
    { value: '1Y', label: '1Y' },
    { value: 'YTD', label: 'YTD' },
    { value: '5Y', label: '5Y' },
  ];

  const handleTimeRangeChange = (event, newTimeRange) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
    }
  };

  // Function to sample data points based on time range
  const sampleDataPoints = (dates, prices, timeRange) => {
    if (!dates || !prices || dates.length !== prices.length) return { dates, prices };
    
    const dataLength = dates.length;
    let samplingInterval = 1; // Default: keep all points
    
    // Define sampling rules based on time range
    switch (timeRange) {
      case '1D':
      case '1W':
      case '1M':
        samplingInterval = 1; // Keep all data points for short periods
        break;
      case '3M':
      case '6M':
        samplingInterval = Math.max(1, Math.floor(dataLength / 20)); // ~80 points for 6 months
        break;
      case '1Y':
      case 'YTD':
      case '5Y':
        samplingInterval = Math.max(1, Math.floor(dataLength / 30)); // ~0 points for 5 years
        break;
      default:
        samplingInterval = 1;
    }
    
    // If sampling interval is 1, return original data
    if (samplingInterval === 1) {
      return { dates, prices };
    }
    
    // Sample the data while keeping first and last points
    const sampledDates = [];
    const sampledPrices = [];
    
    // Always include first point
    sampledDates.push(dates[0]);
    sampledPrices.push(prices[0]);
    
    // Sample intermediate points
    for (let i = samplingInterval; i < dataLength - 1; i += samplingInterval) {
      sampledDates.push(dates[i]);
      sampledPrices.push(prices[i]);
    }
    
    // Always include last point (if not already included)
    if (dataLength > 1 && (dataLength - 1) % samplingInterval !== 0) {
      sampledDates.push(dates[dataLength - 1]);
      sampledPrices.push(prices[dataLength - 1]);
    }
    
    return { dates: sampledDates, prices: sampledPrices };
  };

  // Function to calculate cumulative returns
  const calculateCumulativeReturns = (prices) => {
    if (!prices || prices.length === 0) return [];
    
    const basePrice = prices[0];
    return prices.map(price => ((price - basePrice) / basePrice) * 100);
  };

  const entityUrl = `/entities/${id}/chart?period=${timeRange}`;
  const irxUrl = `/entities/ticker=^IRX/chart?period=${timeRange}`;

  // Fetch entity data
  const { data: entityData, loading: entityLoading, error: entityError } = useFetch(entityUrl);
  
  // Fetch IRX data
  const { data: irxData, loading: irxLoading, error: irxError } = useFetch(irxUrl);

  if (entityLoading || irxLoading) return <p>Loading chart data...</p>;
  if (entityError) return <p>Entity Error: {entityError}</p>;
  if (irxError) return <p>IRX Error: {irxError}</p>;
  if (!entityData || !entityData.data || !entityData.data.stock_chart)
    return <p>No entity data available</p>;

  // Process entity data
  const entityDatesRaw = entityData.data.stock_chart.dates.filter((date) => date !== undefined && date !== null);
  const entityPricesRaw = entityData.data.stock_chart.prices.filter((price) => price !== undefined && price !== null);

  // Sample entity data based on time range
  const { dates: entityDates, prices: entityPrices } = sampleDataPoints(entityDatesRaw, entityPricesRaw, timeRange);

  // Calculate cumulative returns for entity
  const entityReturns = calculateCumulativeReturns(entityPrices);

  // Ensure entity dates and prices lengths match
  if (entityDates.length !== entityPrices.length) {
    return <p>Entity data mismatch: dates and prices lengths do not match</p>;
  }

  // Handle empty entity data
  if (!entityDates.length || !entityPrices.length) {
    return <p>No valid entity data available for the chart</p>;
  }

  // Convert entity dates to proper format
  const processedEntityDates = entityDates.map(date => {
    if (typeof date === 'string') {
      return new Date(date);
    }
    return date;
  });

  // Process IRX data if available
  let irxReturns = [];
  let processedIrxDates = [];
  
  if (irxData && irxData.data && irxData.data.stock_chart) {
    const irxDatesRawOriginal = irxData.data.stock_chart.dates.filter((date) => date !== undefined && date !== null);
    const irxPricesRawOriginal = irxData.data.stock_chart.prices.filter((price) => price !== undefined && price !== null);
    
    // Sample IRX data based on time range
    const { dates: irxDatesRaw, prices: irxPricesRaw } = sampleDataPoints(irxDatesRawOriginal, irxPricesRawOriginal, timeRange);
    
    if (irxDatesRaw.length === irxPricesRaw.length && irxDatesRaw.length > 0) {
      processedIrxDates = irxDatesRaw.map(date => {
        if (typeof date === 'string') {
          return new Date(date);
        }
        return date;
      });
      
      // Calculate cumulative returns for IRX
      irxReturns = calculateCumulativeReturns(irxPricesRaw);
      
      // Align IRX data with entity data dates if needed
      const minLength = Math.min(processedEntityDates.length, processedIrxDates.length);
      if (irxReturns.length > minLength) {
        irxReturns = irxReturns.slice(0, minLength);
      }
    }
  }

  // Prepare series data
  const seriesData = [
    {
      data: entityReturns,
      label: `${entityData.data.name} Cumulative Return (%)`,
      color: "#8884d8",
      showMark: false,
    }
  ];

  // Add IRX data if available
  if (irxReturns.length > 0) {
    seriesData.push({
      data: irxReturns,
      label: "13 Week Treasury Bill Cumulative Return (%)",
      color: "#82ca9d",
      showMark: false,
    });
  }

  return (
    <Container sx={{ mt: 4 }}>
      <Box
        sx={{
          maxWidth: 900,
          width: "100%",
          mx: "auto",
          borderRadius: 4,
          border: "1px solid #e0e0e0",
          boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
          backgroundColor: "#fafafa",
          p: { xs: 2, sm: 3 },
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 1,
        }}
      >
        <Typography
          variant="h5"
          sx={{ fontWeight: 700, textAlign: "center", mb: 2 }}
        >
          {entityData?.data?.name || "N/A"} vs Treasury Bills - Cumulative Returns
        </Typography>

        {/* Time Range Toggle Buttons */}
        <Box sx={{ mb: 3 }}>
          <ToggleButtonGroup
            value={timeRange}
            exclusive
            onChange={handleTimeRangeChange}
            aria-label="time range selection"
            size="small"
            sx={{
              '& .MuiToggleButton-root': {
                px: 2,
                py: 0.5,
                fontSize: '0.875rem',
                fontWeight: 600,
                borderRadius: 1,
                border: '1px solid #e0e0e0',
                color: '#666',
                '&.Mui-selected': {
                  backgroundColor: '#8884d8',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: '#7c7bd8',
                  },
                },
                '&:hover': {
                  backgroundColor: '#f5f5f5',
                },
              },
            }}
          >
            {timeRanges.map((range) => (
              <ToggleButton key={range.value} value={range.value}>
                {range.label}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        <Box sx={{ width: "100%", height: { xs: 200, sm: 300 } }}>
          <LineChart
            width={800}
            height={300}
            xAxis={[{ 
              data: processedEntityDates, 
              label: "Date",
              scaleType: 'time'
            }]}
            yAxis={[{
              label: "Cumulative Return (%)"
            }]}
            series={seriesData}
            margin={{ left: 70, right: 20, top: 20, bottom: 50 }}
          />
        </Box>
        
        {/* Show data availability status */}
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {irxReturns.length > 0 
            ? `Showing ${entityReturns.length} data points (${timeRange}) with Treasury Bill comparison`
            : `Showing ${entityReturns.length} data points (${timeRange}) - Treasury Bill data unavailable`
          }
          {timeRange !== '1D' && timeRange !== '1W' && timeRange !== '1M' && (
            <span style={{ fontStyle: 'italic', marginLeft: '8px' }}>
              (Optimized for performance)
            </span>
          )}
        </Typography>
      </Box>
    </Container>
  );
}

export default EntityVisuals;