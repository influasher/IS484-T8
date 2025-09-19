import React, { useState } from 'react';
import {
  Container,
  Grid,
  Typography,
  Chip,
  Box,
  Tooltip,
  Link as MuiLink,
  Stack,
  Divider,
  CircularProgress,
} from '@mui/material';
import { useLocation, useNavigate, Link, useParams } from 'react-router-dom';
import useFetch from '../../hooks/useFetch';
import SentimentScore from '../../components/ui/Sentimentscore';
import SentimentFeedbackForm from '../../components/ui/sentimentFeedback';
import PieChart from '../../components/ui/feedbackChart';
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import {ROUTES} from "../../routes";


function IndividualNewsPage() {
  const [refreshChart, setRefreshChart] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const id = location.state?.id || null;
  const newsTitle = location.state?.title || 'Unknown Title';
  
  const { data } = useFetch(`news/id/${id}`);
  const newsData = data ? data.data : null;

  // Sentiment scores calculation
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

  // Process arrays from newsData
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

  const handleChipClick = (badgeKey) => {
    navigate(`/entity/${badgeKey}`);
  };

  // Loading and error states
  if (!id) return <Typography>No ID provided. Please navigate correctly.</Typography>;
  if (!newsData) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading News...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", px: 4 }}>
      <Box sx={{ flex: 1, p: 2 }}>
        {/* News Content Section */}
        <Container maxWidth="lg" sx={{ py: 2 }}>
          {/* News Title and Sentiment Row */}
          <Grid item xs={12} md={8}>
            <MuiLink
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
              <Stack direction="column" spacing={0.5}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: "bold",
                    color: "text.secondary",
                  }}
                >
                  {newsData.publisher} |{" "}
                  {new Date(newsData.published_date).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </Typography>
                <Typography
                  variant="h4"
                  sx={{ color: "text.primary" }}
                >
                  {newsData.title}
                </Typography>
              </Stack>
            </MuiLink>
          </Grid>


          {/* News Summary */}
          <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.6 }}>
            {newsData.summary}
          </Typography>

          {/* Sentiment Scores */}
          <Grid container spacing={1} alignItems="center" justifyContent="flex-end" sx={{ mb: 4 }}>
          {[
            {
            label: `FinBERT: ${scores.finbert}`,
            tooltip: "Financial BERT model trained specifically on financial text to detect sentiment in financial news.",
            value: scores.finbert,
            onClick: () => handleChipClick('FinBERT')
            },
            {
            label: `Gemini: ${scores.gemini}`,
            tooltip: "Google's Gemini model provides general language understanding for broader context analysis.",
            value: scores.gemini,
            onClick: () => handleChipClick('Gemini')
            },
            {
            label: `Combine Score: ${scores.combine_score}`,
            tooltip: "Weighted average of both models with confidence factoring to provide the most accurate sentiment score.",
            value: scores.combine_score,
            onClick: () => handleChipClick('Combine Score')
            },
          ].map((chip, i) => (
            <Grid item key={i}>
            <Tooltip title={chip.tooltip} arrow>
              <Chip
              label={chip.label}
              variant="outlined"
              clickable
              onClick={chip.onClick}
              sx={{
                fontSize: "0.8rem",
                fontWeight: 500,
                borderRadius: "8px",
                borderColor: getColor(chip.value),
                color: getColor(chip.value),
                backgroundColor: "transparent",
              }}
              />
            </Tooltip>
            </Grid>
          ))}

          <SentimentScore score={newsData.score} sentiment={newsData.sentiment} />
          </Grid>

          {/* Entities */}
          <Box sx={{ mb: 2 }}>
            Entities:{" "}
            {newsData.entities?.map((entity) => (
              <Chip
                key={entity}
                label={entity}
                variant="outlined"
                clickable
                onClick={() => handleChipClick(entity)}
                sx={{ 
                  fontSize: "0.8rem",
                  fontWeight: 500,
                  borderRadius: "8px",
                  backgroundColor: "transparent",
                }}
              />
            ))}
          </Box>

          {/* Region, Sectors, and Affected Companies */}
          <Box sx={{ mb: 2 }}></Box>
            Regions:{" "}
            {region_list?.length > 0 && (
              <Grid item xs={12} md={4}>
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
          <Box/>

          <Box sx={{ mb: 2 }}>
            Sectors:{" "}
            {sectors_list?.length > 0 && (
              <Grid item xs={12} md={4}>
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
          </Box>

          
          {/* <Box sx={{ mb: 2 }}>
            Affected Companies:
             {company_name_list?.length > 0 && (
              <Grid item xs={12} md={4}>
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
          <Box/> */}

          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            sx={{ mt: 2 }}
          >
            <Typography variant="h6"></Typography>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              <MuiLink
                component={Link}
                to={ROUTES.NEWS}
                underline="hover"
                sx={{
                  color: "text.primary", // uses theme's default text color (black/dark gray)
                  "&:hover": { color: "text.secondary" }, // subtle hover effect
                  gap: 10,
                }}
              >
                View More News
                <ArrowForwardIcon />
              </MuiLink>
            </Typography>
          </Stack>
        </Container>

        <Divider sx={{ mt: 2, mb: 3 }} />

       

        {/* Feedback and Chart Section */}
        <Container maxWidth="xl">
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={4} sx={{ width: "100%" }}>
            {/* LEFT: Sentiment Feedback Form */}
            <Stack direction="column" sx={{ flex: 1 }}>
              <Box sx={{ p: 2 }}>
                <SentimentFeedbackForm 
                  newsTitle={newsTitle} 
                  onFeedbackSubmit={() => setRefreshChart((prev) => !prev)} 
                />
              </Box>
            </Stack>

            {/* Divider between Left & Right */}
            <Divider 
              orientation="vertical" 
              flexItem 
              sx={{ 
                mx: 2,
                display: { xs: 'none', md: 'block' }
              }} 
            />

            {/* RIGHT: Pie Chart */}
            <Stack direction="column" sx={{ flex: 1 }}>
              <Box sx={{ p: 2 }}>
                <PieChart key={refreshChart} />
              </Box>
            </Stack>
          </Stack>
          
        </Container>
      </Box>
    </Box>
  );
}

export default IndividualNewsPage;