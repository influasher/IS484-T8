import React, { useState } from 'react';
import NewsSources from '../../components/news/NewsSources';
import SentimentFeedbackForm from '../../components/ui/sentimentFeedback';
import { useLocation } from 'react-router-dom';
import PieChart from '../../components/ui/feedbackChart';
import { Link } from 'react-router-dom';
import { Typography, Link as MuiLink } from '@mui/material';

function IndividualNewsPage() {
  const [refreshChart, setRefreshChart] = useState(false); // State to trigger chart refresh
  console.log('Rendering IndividualNewsPage ');
  const location = useLocation();
  const newsTitle = location.state?.title || 'Unknown Title'; // Get title from state
  console.log('Rendering IndividualNewsPage with title:', newsTitle);

  return (
    <div style={{ color: 'black', padding: '20px' }}>
      <NewsSources />
      
      <div style={styles.container}>
        {/* Sentiment Feedback Form */}
        <div style={styles.sentimentFeedbackWrapper}>
          <SentimentFeedbackForm newsTitle={newsTitle} onFeedbackSubmit={() => setRefreshChart((prev) => !prev)} />

        </div>

        {/* Pie Chart */}
        <div style={styles.pieChartWrapper}>
        <PieChart key={refreshChart} />
        </div>
      </div>

      <div style={{ textAlign: "center" }}>
        <Typography variant="h6" sx={{ mt: 2 }}>
          <MuiLink 
            component={Link}
            to="/NewsPage">
              Search for more news
          </MuiLink>
        </Typography>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'row', // Default layout for desktop
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    maxWidth: '1200px',
    marginLeft: 'auto',
    marginRight: 'auto',
    flexWrap: 'wrap', // Allows wrapping for smaller screens
  },
  sentimentFeedbackWrapper: {
    flex: 1,
    textAlign: 'left',
    maxWidth: '100%', // Full width on mobile
    marginBottom: '20px', // Adds spacing between components on mobile
  },
  pieChartWrapper: {
    flex: 1,
    textAlign: 'center',
    maxWidth: '100%', // Full width on mobile
  },
  chartTitle: {
    fontSize: '2.5rem',
    textAlign: 'center',
    marginBottom: '10px',
  },
  // Media query for mobile view
  '@media (max-width: 768px)': {
    container: {
      flexDirection: 'column', // Stack components vertically on mobile
    },
    sentimentFeedbackWrapper: {
      order: 1, // Ensure the feedback form appears first
    },
    pieChartWrapper: {
      order: 2, // Ensure the pie chart appears below the feedback form
    },
  },
};

export default IndividualNewsPage;