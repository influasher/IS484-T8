import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Chip,
  Tooltip,
  CircularProgress,
  Typography,
  Container,
} from '@mui/material';
import Entity from '../../components/entity/Entity';
import Price from '../../components/ui/Price';
import EntityVisuals from '../../components/entity/Entityvisuals';
import EntityNews from '../../components/entity/Entitynews';
import useFetch from '../../hooks/useFetch';
import '../../styles/App.css';
import ReportButton from '../../components/ui/export';
import SendPDF from '../../components/ui/SendReport';

const EntityPage = () => {
 
  const getColor = (sentimentType) => {
    if (sentimentType > 0) return 'success';
    if (sentimentType < 0) return 'error';
    return 'default';
  };

  const { ticker } = useParams();
  console.log(ticker);
  const url = `/entities/${ticker}`;
  const { data, loading, error } = useFetch(url);
  const EntityName = data ? data.data.name : "N/A";
  const stockID = data ? data.data.id : "N/A";
  const EntityTicker = data ? data.data.ticker : "N/A";

  const sentimentTypes = {
    AvgSentiment: data ? parseFloat(data.data.sentiment_score).toFixed(1) : 0,
    simpleAverage: data ? parseFloat(data.data.simple_average).toFixed(1) : 0,
    TimeDecay: data ? parseFloat(data.data.time_decay).toFixed(1) : 0,
  };

  if (loading) return (
    <Box sx={styles.loading}>
      <CircularProgress size={60} />
      <Typography variant="h6" sx={{ mt: 2 }}>
        Loading...
      </Typography>
    </Box>
  );
  
  if (error) return (
    <Box sx={styles.error}>
      <Typography variant="h6" color="error">
        Error fetching entity data.
      </Typography>
    </Box>
  );

  return (
    <div className="App">
      <main className="App-content">

        {/* Top Row for Entity and Price & Buttons */}
        <Box sx={styles.topRow}>
          {/* Entity Ticker */}
          <Box sx={styles.entityWrapper}>
            <Entity EntityTicker={EntityTicker} />
          </Box>

          {/* Price and Buttons */}
          <Box sx={styles.priceAndButtonsContainer}>
            <Box sx={styles.priceWrapper}>
              <Price id={stockID} />
            </Box>
            <Box sx={styles.buttonWrapper}>
              <ReportButton EntityName={EntityName} />
              <SendPDF EntityName={EntityName} />
            </Box>
          </Box>
        </Box>

        {/* Sentiment Scores in a Centered Row */}
        <Box sx={styles.sentimentRow}>
          <Box sx={styles.sentimentWrapper}>
            <Box sx={styles.sentimentToggle}>
              <Box sx={{ display: 'flex', gap: '6px', flexWrap: 'wrap', justifyContent: 'center' }}>
                <Tooltip 
                  title="Weighted combination of multiple NLP models' sentiment predictions with confidence factored in."
                  arrow
                  placement="top"
                >
                  <Chip
                    label={`Confidence Weighted Sentiment Score: ${sentimentTypes.AvgSentiment}`}
                    color={getColor(sentimentTypes.AvgSentiment)}
                    sx={styles.badge}
                  />
                </Tooltip>
                <Tooltip 
                  title="Direct average of all article sentiment scores without weighting or adjustments."
                  arrow
                  placement="top"
                >
                  <Chip
                    label={`Simple Average: ${sentimentTypes.simpleAverage}`}
                    color={getColor(sentimentTypes.simpleAverage)}
                    sx={styles.badge}
                  />
                </Tooltip>
                <Tooltip 
                  title="Recent articles weighted more heavily than older ones to reflect current market sentiment."
                  arrow
                  placement="top"
                >
                  <Chip
                    label={`Time Decay: ${sentimentTypes.TimeDecay}`}
                    color={getColor(sentimentTypes.TimeDecay)}
                    sx={styles.badge}
                  />
                </Tooltip>
              </Box>
            </Box> 
          </Box>
        </Box>

        {/* Visuals Section */}
        <Box sx={styles.visualsWrapper}>
          <EntityVisuals id={stockID} />
        </Box>

        {/* News Section */}
        <Box sx={styles.newsWrapper}>
          <EntityNews EntityName={EntityName} />
        </Box>
      </main>
    </div>
  );
};

const styles = {
  // Single Row Layout for Top Section
  topRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between', // Distributes space evenly
    flexWrap: 'wrap', // Allows wrapping for smaller screens
    marginTop: '20px',
    padding: '0 10px',
  },
  entityWrapper: {
    flex: '3 3 auto',
    textAlign: 'center',
    margin: '5px', // Reduced margin
  },

  // Sentiment Scores in a new centered row
  sentimentRow: {
    display: 'flex',
    justifyContent: 'center', // Centering Sentiment Scores
    marginTop: '20px', // Space between other content
  },

  sentimentWrapper: {
    flex: '1 1 auto',
    display: 'flex',
    justifyContent: 'center', // Ensures the content is centered in the sentiment row
    alignItems: 'center',
  },
  
  sentimentToggle: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'center', // Center the badges in the row
  },

  badge: {
    fontSize: '1rem',
    padding: '6px 12px',
    borderRadius: '20px',
    fontWeight: '500',
    cursor: 'pointer',
    '&:hover': {
      transform: 'scale(1.02)',
      transition: 'transform 0.2s ease',
    },
  },

  priceAndButtonsContainer: {
    display: 'flex',
    flex: '3 3 auto', // Adjusted to take up 3 parts of the space
    justifyContent: 'space-between', // Evenly space Price and Buttons
    alignItems: 'center',
  },

  priceWrapper: {
    flex: '1 1 auto',
    textAlign: 'center',
    fontSize: 'clamp(0.8rem, 1vw, 1.2rem)',
    margin: '5px',
  },

  buttonWrapper: {
    flex: '1 1 auto',
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },

  visualsWrapper: {
    flex: '1 1 auto',
    margin: '5px',
  },

  newsWrapper: {
    flex: '1 1 auto',
    margin: '5px',
  },

  loading: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '1.5rem',
  },

  error: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '1.5rem',
  },
};

export default EntityPage;