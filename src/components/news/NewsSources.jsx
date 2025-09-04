import React from 'react';
import {
  Container,
  Grid,
  Typography,
  Chip,
  Box,
  Tooltip,
  Link,
  Paper,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import useFetch from '../../hooks/useFetch';
import SentimentScore from '../ui/Sentimentscore';

const NewsSources = () => {
  const location = useLocation();
  const { id } = location.state || { id: null };
  const { data } = useFetch(`news/id/${id}`);

  const newsData = data ? data.data : null;

  const scores = {
    finbert: newsData ? parseFloat(newsData.finbert_score).toFixed(1) : 0,
    gemini: newsData ? parseFloat(newsData.second_model_score).toFixed(1) : 0,
    combine_score: newsData ? parseFloat(newsData.score).toFixed(1) : 0,
  };

  const getColor = (score) => {
    if (score > 0) return 'success';
    if (score < 0) return 'error';
    return 'default';
  };

  // Ensure that region_list is an array before calling map
  const region_list = Array.isArray(newsData?.regions)
    ? newsData.regions
    : typeof newsData?.regions === 'string'
    ? newsData.regions.split(',').map((item) => item.trim())
    : [];

  const sectors_list = Array.isArray(newsData?.sectors)
    ? newsData.sectors
    : typeof newsData?.sectors === 'string'
    ? newsData.sectors.split(',').map((item) => item.trim())
    : [];

  const company_name_list = Array.isArray(newsData?.company_names)
    ? newsData.company_names
    : typeof newsData?.company_names === 'string'
    ? newsData.company_names.split(',').map((item) => item.trim())
    : [];

  // Use navigate hook from react-router-dom
  const navigate = useNavigate();

  const handleChipClick = (badgeKey) => {
    // Navigate to /NewsPage and pass the badgeKey as state
    navigate('/NewsPage', {
      state: { search: badgeKey }, // Pass the badgeKey in the state
    });
  };

  if (!id) return <Typography>No ID provided. Please navigate correctly.</Typography>;
  if (!newsData) return <Typography>Loading...</Typography>;

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      {/* News Title and Sentiment Row */}
      <Grid container alignItems="center" spacing={2}>
        <Grid item xs={12} md={8}>
          <Link
            href={newsData.url}
            target="_blank"
            rel="noopener noreferrer"
            underline="none"
            sx={{
              color: '#1976d2',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            <Typography
              variant="h5"
              component="h4"
              sx={{
                fontSize: 'calc(7px + 1vw)',
                fontWeight: 'bold',
                color: '#1976d2',
              }}
            >
              {newsData.title}
            </Typography>
          </Link>
        </Grid>
        <Grid item xs={12} md={4}>
          <Box display="flex" justifyContent={{ xs: 'flex-start', md: 'flex-end' }}>
            {/* Sentiment Score Pill */}
            <SentimentScore score={newsData.score} sentiment={newsData.sentiment} />
          </Box>
        </Grid>
      </Grid>

      {/* News date and publisher */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          fontSize: 'calc(8px + 0.5vw)',
          color: 'text.secondary',
          mb: 1,
          mt: 1,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          📅 {new Date(newsData.published_date).toLocaleDateString()}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          📰 {newsData.publisher}
        </Typography>
      </Box>

      {/* Entities */}
      <Box sx={{ mb: 2 }}>
        {newsData.entities?.map((entity) => (
          <Chip
            key={entity}
            label={entity}
            variant="outlined"
            clickable
            onClick={() => handleChipClick(entity)}
            sx={{ 
              m: 0.5,
              fontSize: '1em',
              fontWeight: '500',
            }}
          />
        ))}
      </Box>

      {/* Sentiment Scores */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Tooltip
            title="Financial BERT model trained specifically on financial text to detect sentiment in financial news."
            arrow
          >
            <Chip
              label={`FinBERT: ${scores.finbert}`}
              color={getColor(scores.finbert)}
              clickable
              onClick={() => handleChipClick('FinBERT')}
              sx={{
                fontSize: '1em',
                fontWeight: '500',
              }}
            />
          </Tooltip>
          <Tooltip
            title="Google's Gemini model provides general language understanding for broader context analysis."
            arrow
          >
            <Chip
              label={`Gemini: ${scores.gemini}`}
              color={getColor(scores.gemini)}
              clickable
              onClick={() => handleChipClick('Gemini')}
              sx={{
                fontSize: '1em',
                fontWeight: '500',
              }}
            />
          </Tooltip>
          <Tooltip
            title="Weighted average of both models with confidence factoring to provide the most accurate sentiment score."
            arrow
          >
            <Chip
              label={`Combine Score: ${scores.combine_score}`}
              color={getColor(scores.combine_score)}
              clickable
              onClick={() => handleChipClick('Combine Score')}
              sx={{
                fontSize: '1em',
                fontWeight: '500',
              }}
            />
          </Tooltip>
        </Box>
      </Box>

      {/* News Summary */}
      <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.6 }}>
        {newsData.summary}
      </Typography>

      {/* Region, Sectors, and Affected Companies in separate columns */}
      <Grid container spacing={3}>
        {region_list?.length > 0 && (
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
              🌍 Region:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {region_list.map((region) => (
                <Chip
                  key={region}
                  label={region}
                  color="info"
                  clickable
                  onClick={() => handleChipClick(region)}
                  sx={{
                    fontSize: '1em',
                    fontWeight: '500',
                  }}
                />
              ))}
            </Box>
          </Grid>
        )}
        {sectors_list?.length > 0 && (
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
              🏢 Sectors:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {sectors_list.map((sector) => (
                <Chip
                  key={sector}
                  label={sector}
                  sx={{
                    backgroundColor: '#424242',
                    color: 'white',
                    fontSize: '1em',
                    fontWeight: '500',
                    '&:hover': {
                      backgroundColor: '#616161',
                    },
                  }}
                  clickable
                  onClick={() => handleChipClick(sector)}
                />
              ))}
            </Box>
          </Grid>
        )}
        {company_name_list?.length > 0 && (
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
              🏭 Affected Companies:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {company_name_list.map((company) => (
                <Chip
                  key={company}
                  label={company}
                  color="warning"
                  clickable
                  onClick={() => handleChipClick(company)}
                  sx={{
                    fontSize: '1em',
                    fontWeight: '500',
                  }}
                />
              ))}
            </Box>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default NewsSources;