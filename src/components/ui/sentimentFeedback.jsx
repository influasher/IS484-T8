import React, { useState, useEffect, useRef } from 'react';
import '../../styles/sentimentFeedback.css'; // External CSS file
import { Modal, Button } from 'react-bootstrap';
import useFetch from '../../hooks/useFetch';
import { useLocation } from 'react-router-dom';
import { postData } from '../../services/api';
import { ToastContainer, toast } from 'react-toastify';  // Import Toastify
import 'react-toastify/dist/ReactToastify.css';  // Import Toastify styles

const SentimentFeedbackForm = ({ newsTitle, onFeedbackSubmit }) => {
  const [selectedOption, setSelectedOption] = useState(null);
  const [showModal, setShowModal] = useState(false); // State for modal visibility
  
  // Use ref instead of state to track toast display
  const toastDisplayed = useRef(false);

  const location = useLocation();
  const { id } = location.state || { id: null }; // Retrieve the id from state

  const { data, loading, error } = useFetch(`/news/id/${id}`); // Fetch news data from the API with the id parameter
  const filteredNewsData = data ? data.data : []; // Extract news data from the response
  const agreementScore = filteredNewsData.agreement_rate;

  // Handle sentiment option changes
  const handleOptionChange = (event) => {
    setSelectedOption(event.target.value);
  };

  // Handle feedback submission
  const handleSubmit = () => {
    if (!selectedOption) {
      alert('Please select a sentiment option before submitting.');
      return;
    }

    // Prepare feedback data
    const feedbackData = {
      userID: 1, // Replace with actual user ID for now dummy data
      newsID: id,
      assessment: selectedOption,
    };

    console.log('Feedback data:', feedbackData);

    // Send feedback to the backend
    postData('/feedback/', feedbackData)
      .then((response) => {
        console.log('Feedback submitted successfully:', response);
        setShowModal(true); // Show success modal
        onFeedbackSubmit(); // Trigger parent component refresh
      })
      .catch((error) => {
        console.error('Error submitting feedback:', error);
      });
  };

  // Show toast only once when component mounts and meets condition
  useEffect(() => {
    const showToastOnce = () => {
      // Only show toast if agreement score is not 1 and toast hasn't already been displayed
      if (agreementScore !== 1 && !toastDisplayed.current) {
        toast.info("Model disagreement detected!", {
          position: "top-center",
          autoClose: 2000,
          hideProgressBar: true,
          closeOnClick: true,
          draggable: true,
          pauseOnHover: true,
        });
        // Mark toast as displayed
        toastDisplayed.current = true;
      }
    };

    // Only run if data is loaded
    if (!loading && filteredNewsData) {
      showToastOnce();
    }
  }, [filteredNewsData, loading]); // Depend on data loading state instead

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
      <ToastContainer limit={1} /> {/* Limit to 1 toast at a time */}
      <h3>Sentiment Feedback Form</h3>
      <p>Article: {newsTitle}</p>
      <div>
        <span>
          FinBERT: {Math.ceil(filteredNewsData.finbert_score)}
        </span>
        &nbsp;&nbsp;
        <span>
          Gemini: {Math.ceil(filteredNewsData.second_model_score)}
        </span>
      </div>
      <hr />
      <div>
      <p>Your assessment:</p>
        <label>
          <input
            type="radio"
            name="sentiment"
            value="bullish"
            onChange={handleOptionChange}
          />
          &nbsp; Bullish
        </label>
        &nbsp;&nbsp;
        {/* <label>
          <input
            type="radio"
            name="sentiment"
            value="neutral"
            onChange={handleOptionChange}
          />
          Neutral
        </label> */}
        &nbsp;&nbsp;
        <label>
          <input
            type="radio"
            name="sentiment"
            value="bearish"
            onChange={handleOptionChange}
          />
          &nbsp; Bearish
        </label>
      </div>

      <button onClick={handleSubmit}>Submit</button>

      {/* Submission Success Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Feedback Submitted</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>
            <strong>Sentiment:</strong>{' '}
            {selectedOption ? selectedOption.charAt(0).toUpperCase() + selectedOption.slice(1) : 'N/A'}
          </p>
          <p>Thank you for your feedback!</p>
        </Modal.Body>
        <Modal.Footer>
        <Button variant="success" onClick={() => setShowModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default SentimentFeedbackForm;