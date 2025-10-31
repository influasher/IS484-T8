import React, { useState, useEffect, useRef } from 'react';
import '../../styles/sentimentFeedback.css'; // External CSS file
import { Modal, Button } from 'react-bootstrap';
import useFetch from '../../hooks/useFetch';
import { useLocation } from 'react-router-dom';
import { postData } from '../../services/api';
import { ToastContainer, toast } from 'react-toastify';  // Import Toastify
import 'react-toastify/dist/ReactToastify.css';  // Import Toastify styles
import useAuth from '../../hooks/useAuth'; // Import useAuth hook

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
            const matchingItem = data.data.find(item => item.news_id === parseInt(id));
            if (matchingItem) {
              setQueueItemId(matchingItem.id);
              setIsActiveCase(true);
              console.log('Found active learning case:', matchingItem);
            }
          }
        } catch (error) {
          console.error('Error checking for active learning case:', error);
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
      alert('Please select a sentiment option before submitting.');
      return;
    }

    // UNIFIED SYSTEM: All feedback goes through active learning - SIMPLIFIED
    const voteData = {
      queue_item_id: queueItemId || null,
      vote: selectedOption,
      session_info: {
        timestamp: new Date().toISOString(),
        news_id: id,
        was_high_priority: isActiveCase
      }
    };

    console.log('Submitting vote to active learning system:', voteData);

    postData('/labeling/vote', voteData)
      .then((response) => {
        console.log('Vote submitted successfully:', response);
        if (response && response.status === 201) {
          setShowModal(true);
          onFeedbackSubmit();
        } else {
          console.error('Unexpected response:', response);
          alert('Failed to submit feedback. Please try again.');
        }
      })
      .catch((error) => {
        console.error('Error submitting vote:', error);
        
        // Show more specific error messages
        if (error.response?.data?.message) {
          alert(`Failed to submit feedback: ${error.response.data.message}`);
        } else if (error.response?.status === 400) {
          alert('Invalid feedback data. Please try again.');
        } else if (error.response?.status === 401) {
          alert('Please log in to submit feedback.');
        } else {
          alert('Failed to submit feedback. Please try again.');
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
            minWidth: '310px',
            maxWidth: '310px',
            fontSize: '14px',
            lineHeight: '1.2',
            padding: '12px 16px',
            borderRadius: '8px',
            marginTop: '0px',
            margin: '0px',
          },
          bodyStyle: {
            marginTop: '0px'
          },
          progressStyle: {
            background: toastType === 'warning' ? '#ff9500' : '#3498db'
          }
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
    return <div style={{ color: 'white', fontStyle: 'italic' }}>No feedback required</div>;
  }

  return (
    <div className="feedback-form">
      <ToastContainer 
        limit={1}
        toastStyle={{
          minWidth: '300px',
          maxWidth: '300px',
        }}
      />
      <h3>Sentiment Feedback Form</h3>
      {needsHumanFeedback && (
        <div style={{ 
          backgroundColor: '#fff3cd', 
          color: '#856404', 
          borderRadius: '4px', 
          marginBottom: '10px',
          border: '1px solid #ffeaa7'
        }}>
          🎯 <strong>High Priority:</strong> Models strongly disagree - your expertise is needed!
          {isActiveCase && (
            <small style={{ display: 'block', marginTop: '4px', fontStyle: 'italic' }}>
              This case will help improve our sentiment analysis models.
            </small>
          )}
        </div>
      )}
      <p>Article: {newsTitle}</p>
      <div>
        <span>
          FinBERT: {Math.ceil(filteredNewsData.finbert_score)}
        </span>
        &nbsp;&nbsp;
        <span>
          {filteredNewsData.model_type_used === 'openai' ? 'OpenAI' : 'Gemini'}: {Math.ceil(filteredNewsData.second_model_score)}
        </span>
      </div>
      {/* Enhanced agreement information */}
      <div style={{ fontSize: '0.9em', color: '#ccc', marginTop: '5px' }}>
        <span>Agreement: {(agreementScore * 100).toFixed(0)}%</span>
        &nbsp;&nbsp;
        <span>Confidence: {(filteredNewsData.confidence * 100).toFixed(0)}%</span>
        {needsHumanFeedback && (
          <>
            &nbsp;&nbsp;
            <span style={{ color: '#ff9500' }}>⚠️ High Priority</span>
          </>
        )}
      </div>
      <hr />
      <div>
      <p>Your assessment:</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ display: 'flex', alignItems: 'center' }}>
            <input
              type="radio"
              name="sentiment"
              value="bullish"
              onChange={handleOptionChange}
              style={{ marginRight: '8px' }}
            />
            <span style={{ color: '#28a745', fontWeight: 'bold' }}>📈 Bullish</span>
            <span style={{ marginLeft: '8px', fontSize: '0.85em', color: '#666' }}>
              (Positive news likely to increase stock price)
            </span>
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center' }}>
            <input
              type="radio"
              name="sentiment"
              value="neutral"
              onChange={handleOptionChange}
              style={{ marginRight: '8px' }}
            />
            <span style={{ color: '#6c757d', fontWeight: 'bold' }}>➡️ Neutral</span>
            <span style={{ marginLeft: '8px', fontSize: '0.85em', color: '#666' }}>
              (Factual information, no clear market impact)
            </span>
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center' }}>
            <input
              type="radio"
              name="sentiment"
              value="bearish"
              onChange={handleOptionChange}
              style={{ marginRight: '8px' }}
            />
            <span style={{ color: '#dc3545', fontWeight: 'bold' }}>📉 Bearish</span>
            <span style={{ marginLeft: '8px', fontSize: '0.85em', color: '#666' }}>
              (Negative news likely to decrease stock price)
            </span>
          </label>
        </div>
      </div>

      <button onClick={handleSubmit}>
        {isActiveCase ? 'Submit Expert Feedback' : 'Submit Feedback'}
      </button>

      {/* Submission Success Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Header closeButton style={{ paddingRight: '50px', marginTop: '0px', paddingTop: '0px' }}>
          <Modal.Title style={{ fontSize: '1.2em', fontWeight: 'bold' }}>
            Feedback Submitted
          </Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ padding: '20px', minWidth: '300px' }}>
          <p style={{ marginBottom: '15px' }}>
            <strong>Sentiment:</strong>{' '}
            {selectedOption ? selectedOption.charAt(0).toUpperCase() + selectedOption.slice(1) : 'N/A'}
          </p>
          <p style={{ marginBottom: '0' }}>Thank you for your feedback!</p>
        </Modal.Body>
        <Modal.Footer style={{ justifyContent: 'center', padding: '15px 20px' }}>
          <Button 
            variant="success" 
            onClick={() => setShowModal(false)}
            style={{ minWidth: '100px' }}
          >
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default SentimentFeedbackForm;