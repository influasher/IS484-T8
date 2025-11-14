import React from 'react';
import { formatSentimentClassification } from '../../utils/sentimentAnalysis';
import Tooltip from '@mui/material/Tooltip';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';

const SentimentScore = ({ 
  score, 
  sentiment, 
  finbertScore,
  secondModelScore, 
  showDetails = false 
}) => {
  if (!score && score !== 0) {
    return (
      <Grid container spacing={1} alignItems="center" justifyContent="flex-end">
        <Grid item>
          <Chip
            label="No Score Found"
            variant="outlined"
            sx={{
              fontSize: "0.8rem",
              fontWeight: 500,
              borderRadius: "8px",
              borderColor: "default",
              color: "default",
              backgroundColor: "transparent",
            }}
          />
        </Grid>
      </Grid>
    );
  }

  const formattedSentiment = formatSentimentClassification(sentiment || 'neutral');
  console.log(formattedSentiment);

  const getColor = (score) => {
    if (score > 0) return 'success';
    if (score < 0) return 'error';
    return 'default';
  };

  const displayScore = typeof score === 'number' ? 
    (score > -100 && score < 100) ? score : (score > 0 ? 100 : -100) : 0;

  const getTooltipContent = () => {
    if (sentiment?.toLowerCase() === 'positive' || sentiment?.toLowerCase() === 'bullish') {
      return "Positive sentiment indicates favorable news or outlook for this entity";
    } else if (sentiment?.toLowerCase() === 'negative' || sentiment?.toLowerCase() === 'bearish') {
      return "Negative sentiment indicates unfavorable news or outlook for this entity";
    } else {
      return "Neutral sentiment indicates balanced or mixed news for this entity";
    }
  };

  const chipData = [
    {
      label: `${displayScore.toFixed(1)} (${formattedSentiment})`,
      tooltip: getTooltipContent(),
      value: displayScore,
    }
  ];

  // Add additional chips if showDetails is true
  if (showDetails) {
    if (finbertScore) {
      chipData.push({
        label: `FinBERT: ${finbertScore.toFixed(1)}`,
        tooltip: "Financial BERT model score",
        value: finbertScore,
      });
    }
    
    if (secondModelScore) {
      chipData.push({
        label: `Second Model: ${secondModelScore.toFixed(1)}`,
        tooltip: "Second NLP model score",
        value: secondModelScore,
      });
    }
  }

  return (
    <Box className="sentiment-score-container">
      <Grid container spacing={1} alignItems="center" justifyContent="flex-end">
        {chipData.map((chip, i) => (
          <Grid item key={i}>
            <Tooltip title={chip.tooltip} arrow>
              <Chip
                label={chip.label}
                variant="outlined"
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
      </Grid>
    </Box>
  );
};

export default SentimentScore;