import React from "react";
import { Container, Box, Typography } from "@mui/material";
import { LineChart } from "@mui/x-charts/LineChart";
import useFetch from "../../hooks/useFetch"; // Adjust path if needed

function EntityVisuals({ id }) {
  const number = id;

  const entityUrl = `/entities/${number}/chart`;
  const irxUrl = `/entities/ticker=^IRX/chart`; // Fetching IRX data

  // Fetch entity data
  const { data: entityData, loading: entityLoading, error: entityError } = useFetch(entityUrl);
  
  // Fetch IRX data
  const { data: irxData, loading: irxLoading, error: irxError } = useFetch(irxUrl);

  if (entityLoading || irxLoading) return <p>Loading chart data...</p>;
  if (entityError) return <p>Entity Error: {entityError}</p>;
  if (irxError) return <p>IRX Error: {irxError}</p>;
  if (!entityData || !entityData.data || !entityData.data.stock_chart)
    return <p>No entity data available</p>;

  // Function to calculate cumulative returns
  const calculateCumulativeReturns = (prices) => {
    if (!prices || prices.length === 0) return [];
    
    const basePrice = prices[0];
    return prices.map(price => ((price - basePrice) / basePrice) * 100);
  };

  // Process entity data
  const entityDates = entityData.data.stock_chart.dates.filter((date) => date !== undefined && date !== null);
  const entityPrices = entityData.data.stock_chart.prices.filter((price) => price !== undefined && price !== null);

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
    const irxDatesRaw = irxData.data.stock_chart.dates.filter((date) => date !== undefined && date !== null);
    const irxPricesRaw = irxData.data.stock_chart.prices.filter((price) => price !== undefined && price !== null);
    
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
    }
  ];

  // Add IRX data if available
  if (irxReturns.length > 0) {
    seriesData.push({
      data: irxReturns,
      label: "13 Week Treasury Bill Cumulative Return (%)",
      color: "#82ca9d",
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
          sx={{ fontWeight: 700, textAlign: "center" }}
        >
          {entityData?.data?.name || "N/A"} vs Treasury Bills - Cumulative Returns
        </Typography>

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
            ? `Showing ${entityReturns.length} data points with Treasury Bill comparison`
            : `Showing ${entityReturns.length} data points (Treasury Bill data unavailable)`
          }
        </Typography>
      </Box>
    </Container>
  );
}

export default EntityVisuals;