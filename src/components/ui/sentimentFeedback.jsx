import React, { useState, useEffect, useRef } from "react";
import "../../styles/sentimentFeedback.css"; // External CSS file
import useFetch from "../../hooks/useFetch";
import { useLocation } from "react-router-dom";
import { postData } from "../../services/api";
import { ToastContainer, toast } from "react-toastify"; // Import Toastify
import "react-toastify/dist/ReactToastify.css"; // Import Toastify styles
import useAuth from "../../hooks/useAuth"; // Import useAuth hook
import FeedbackModal from "./FeedbackModal";
import {
  Box,
  Typography,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Divider,
  Button,
  Stack,
} from "@mui/material";

const SentimentFeedbackForm = ({ newsTitle, onFeedbackSubmit }) => {
  const { user } = useAuth(); // Get authenticated user
  const [selectedOption, setSelectedOption] = useState(null);
  const [showModal, setShowModal] = useState(false); // State for modal visibility
  const [queueItemId, setQueueItemId] = useState(null); // Track queue item ID
  const [isActiveCase, setIsActiveCase] = useState(false); // Track if this is an active learning case

  // Use ref instead of state to track toast display
  const toastDisplayed = useRef(false);

  const location = useLocation();
  const { id } = location.state || { id: null }; // Retrieve the id from state

  const { data, loading, error } = useFetch(`/news/id/${id}`); // Fetch news data from the API with the id parameter
  const filteredNewsData = data ? data.data : []; // Extract news data from the response
  const agreementScore = filteredNewsData.agreement_rate;
  const needsHumanFeedback = filteredNewsData.needs_human_feedback;
  const disagreementDetected = filteredNewsData.disagreement_detected;

  // Handle sentiment option changes
  const handleOptionChange = (event) => {
    setSelectedOption(event.target.value);
  };

  // Check if this news item has a corresponding queue item for active learning
  useEffect(() => {
    const checkForActiveCase = async () => {
      if (needsHumanFeedback && id) {
        try {
          // Check if there's a pending queue item for this news
          const response = await fetch(`/api/labeling/pending?limit=100`);
          const data = await response.json();

          if (data.status === 200 && data.data) {
            const matchingItem = data.data.find(
              (item) => item.news_id === parseInt(id)
            );
            if (matchingItem) {
              setQueueItemId(matchingItem.id);
              setIsActiveCase(true);
              console.log("Found active learning case:", matchingItem);
            }
          }
        } catch (error) {
          console.error("Error checking for active learning case:", error);
        }
      }
    };

    if (!loading && filteredNewsData && needsHumanFeedback) {
      checkForActiveCase();
    }
  }, [needsHumanFeedback, id, loading, filteredNewsData]);

  // Handle feedback submission - ONLY uses active learning
  const handleSubmit = () => {
    if (!selectedOption) {
      alert("Please select a sentiment option before submitting.");
      return;
    }

    // UNIFIED SYSTEM: All feedback goes through active learning - SIMPLIFIED
    const voteData = {
      queue_item_id: queueItemId || null,
      vote: selectedOption,
      session_info: {
        timestamp: new Date().toISOString(),
        news_id: id,
        was_high_priority: isActiveCase,
      },
    };

    console.log("Submitting vote to active learning system:", voteData);

    postData("/labeling/vote", voteData)
      .then((response) => {
        console.log("Vote submitted successfully:", response);
        if (response && response.status === 201) {
          setShowModal(true);
          onFeedbackSubmit();
        } else {
          console.error("Unexpected response:", response);
          alert("Failed to submit feedback. Please try again.");
        }
      })
      .catch((error) => {
        console.error("Error submitting vote:", error);

        // Show more specific error messages
        if (error.response?.data?.message) {
          alert(`Failed to submit feedback: ${error.response.data.message}`);
        } else if (error.response?.status === 400) {
          alert("Invalid feedback data. Please try again.");
        } else if (error.response?.status === 401) {
          alert("Please log in to submit feedback.");
        } else {
          alert("Failed to submit feedback. Please try again.");
        }
      });
  };

  useEffect(() => {
    const showToastOnce = () => {
      if (agreementScore !== 1 && !toastDisplayed.current) {
        let message = "Model disagreement detected!";
        let toastType = "info";
        let duration = 5000;

        if (needsHumanFeedback) {
          message = "High-priority case! Your feedback is especially valuable.";
          toastType = "warning";
          duration = 8000;
        } else if (disagreementDetected) {
          message = "Model disagreement detected - your input helps!";
          toastType = "info";
          duration = 6000;
        }

        toast[toastType](message, {
          position: "top-center",
          autoClose: duration,
          hideProgressBar: false,
          closeOnClick: true,
          draggable: true,
          pauseOnHover: true,
          style: {
            minWidth: "310px",
            maxWidth: "310px",
            fontSize: "14px",
            lineHeight: "1.2",
            padding: "12px 16px",
            borderRadius: "8px",
            marginTop: "0px",
            margin: "0px",
          },
          bodyStyle: {
            marginTop: "0px",
          },
          progressStyle: {
            background: toastType === "warning" ? "#ff9500" : "#3498db",
          },
        });

        toastDisplayed.current = true;
      }
    };

    if (!loading && filteredNewsData) {
      showToastOnce();
    }
  }, [filteredNewsData, loading, needsHumanFeedback, disagreementDetected]);

  // Loading state
  if (loading) {
    return <div>Loading...</div>;
  }

  // Error state
  if (error) {
    return <div>Error fetching news data.</div>;
  }

  // No feedback required if agreementScore is 1
  if (!filteredNewsData || agreementScore === 1) {
    return (
      <div style={{ color: "white", fontStyle: "italic" }}>
        No feedback required
      </div>
    );
  }

  return (
    <Box
      sx={{
        mb: 4,
        p: 2,
        borderRadius: 1,
      }}
    >
      <ToastContainer
        limit={1}
        toastStyle={{
          minWidth: "300px",
          maxWidth: "300px",
        }}
      />

      {needsHumanFeedback && (
        <div
          style={{
            backgroundColor: "#fff3cd",
            color: "#856404",
            borderRadius: "4px",
            marginBottom: "10px",
            border: "1px solid #ffeaa7",
          }}
        >
          🎯 <strong>High Priority:</strong> Models strongly disagree - your
          expertise is needed!
          {isActiveCase && (
            <small
              style={{
                display: "block",
                marginTop: "4px",
                fontStyle: "italic",
              }}
            >
              This case will help improve our sentiment analysis models.
            </small>
          )}
        </div>
      )}

      <Stack
        direction="column"
        justifyContent="space-between"
        sx={{
          height: "100%",
          minHeight: 350,
        }}
      >
        <Typography variant="h6" gutterBottom>
          {newsTitle}
        </Typography>

        <Typography variant="body1" gutterBottom>
          The models show low agreement ({(agreementScore * 100).toFixed(0)}%)
          on this article’s sentiment. FinBERT has a score of{" "}
          {Math.ceil(filteredNewsData.finbert_score)}, while{" "}
          {filteredNewsData.model_type_used === "openai" ? "OpenAI" : "Gemini"}{" "}
          has a score of {Math.ceil(filteredNewsData.second_model_score)}. Your
          expert feedback will help us resolve this disagreement and improve the
          model’s accuracy over time.
        </Typography>

        <Divider sx={{ my: 1.5 }} />

        <FormControl>
          <Typography variant="body1">Human Assessment</Typography>
          <RadioGroup
            aria-labelledby="demo-radio-buttons-group-label"
            value={selectedOption} // controlled component
            onChange={handleOptionChange} // your handler
          >
            <FormControlLabel
              value="bullish"
              control={<Radio />}
              label="Bullish (Positive news likely to increase stock price)"
            />
            <FormControlLabel
              value="neutral"
              control={<Radio />}
              label="Neutral (Factual information, no clear market impact)"
            />
            <FormControlLabel
              value="bearish"
              control={<Radio />}
              label="Bearish (Negative news likely to decrease stock price)"
            />
          </RadioGroup>
        </FormControl>

        {/* Button at Bottom Left */}
        <Box sx={{ mt: 3, display: "flex", justifyContent: "flex-start" }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSubmit}
            sx={{
              textTransform: "none",
            }}
          >
            {isActiveCase ? "Submit Expert Feedback" : "Submit Feedback"}
          </Button>
        </Box>
      </Stack>

      <FeedbackModal
        open={showModal}
        onClose={() => setShowModal(false)}
        selectedOption={selectedOption}
      />
    </Box>
  );
};

export default SentimentFeedbackForm;
