import React from 'react';
import { formatSentimentClassification } from '../../utils/sentimentAnalysis';
import Tooltip from '@mui/material/Tooltip';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

const SentimentScore = ({ 
  score, 
  sentiment, 
  confidence, 
  finbertScore,
  secondModelScore, 
  showDetails = false 
}) => {
  if (!score && score !== 0) {
    return (
      <Box
        sx={{
          backgroundColor: '#808080',
          borderRadius: '15px',
          padding: '5px 15px',
          color: 'white',
          fontSize: 'calc(1px + 1vw)',
          fontWeight: 'bold',
        }}
      >
        No score found
      </Box>
    );
  }

  const formattedSentiment = formatSentimentClassification(sentiment || 'neutral');
  console.log(formattedSentiment);

  const getBackgroundColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
      case 'bullish':
        return '#28a745'; // Green
      case 'negative':
      case 'bearish':
        return '#dc3545'; // Red
      case 'neutral':
        return '#ffc107'; // Yellow
      default:
        return '#6c757d'; // Default to grey for unknown sentiment
    }
  }; 
  const bgColor = getBackgroundColor(sentiment);

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

  return (
    <Box className="sentiment-score-container">
      <Tooltip title={getTooltipContent()} arrow>
        <Box
          sx={{
            backgroundColor: bgColor,
            borderRadius: '15px',
            padding: '5px 15px',
            color: 'white',
            fontSize: 'calc(1px + 1vw)',
            fontWeight: 'bold',
            display: 'inline-block',
            cursor: 'pointer',
          }}
        >
          {displayScore.toFixed(1)} ({formattedSentiment})
        </Box>
      </Tooltip>
      
      {showDetails && (
        <Box className="sentiment-details" sx={{ mt: 2, fontSize: '0.875rem' }}>
          {confidence && (
            <Tooltip title="Higher confidence indicates more reliable sentiment analysis" arrow>
              <Typography 
                className="sentiment-confidence" 
                sx={{ cursor: 'pointer', color: 'text.secondary' }}
                variant="body2"
              >
                Confidence: {(confidence * 100).toFixed(0)}%
              </Typography>
            </Tooltip>
          )}
          
          {finbertScore && secondModelScore && (
            <Tooltip title="Scores from different NLP models used in sentiment analysis" arrow>
              <Typography 
                className="model-scores" 
                sx={{ cursor: 'pointer', color: 'text.secondary', mt: 1 }}
                variant="body2"
              >
                FinBERT: {finbertScore.toFixed(1)} | 
                Second Model: {secondModelScore.toFixed(1)}
              </Typography>
            </Tooltip>
          )}
        </Box>
      )}
    </Box>
  );
};

export default SentimentScore;
