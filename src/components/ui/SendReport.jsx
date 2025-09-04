import React, { useState } from 'react';
import { FaEnvelope } from 'react-icons/fa'; // Import email icon
import { postData } from '../../services/api';
import EmailIcon from '@mui/icons-material/Email';
import { Button } from '@mui/material';

const SendPDF = ({ EntityName }) => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [showPopup, setShowPopup] = useState(false);

  const sendEmail = async () => {
    setLoading(true);
    setStatus('Sending email...');  
    setShowPopup(true);
    
    try {
      const response = await postData(`/send_pdf/send_pdf_email`, JSON.stringify({ entity_name: EntityName }));

      if (response.data.success) {
        setStatus('Email sent successfully!');
        setShowPopup(true); // Show the popup when email is sent
      } else {
        setStatus('Failed to send email.');
      }
    } catch (error) {
      setStatus('Error sending email.');
    } finally {
      setLoading(false);
    }
  };

  const closePopup = () => {
    setShowPopup(false);
  };

  return (
    <>
      <Button 
        variant="contained" 
        startIcon={<EmailIcon />}
        onClick={sendEmail}
        loading={loading}
        loadingPosition="start"
      >
        Send PDF
      </Button>
      
      {/* Conditional rendering of the popup */}
      {showPopup && (
        <div style={styles.popupOverlay}>
          <div style={styles.popup}>
            <p>{status}</p>
            <button onClick={closePopup} style={styles.closeButton}>Close</button>
          </div>
        </div>
      )}
    </>
  );
};

const styles = {
  button: {
    borderRadius: '50%',
    padding: '10px',
    backgroundColor: '#28a745', // Button color (green for email)
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
    transition: 'background-color 0.3s',
  },
  popupOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999, // Ensure the popup is above all other content
  },
  popup: {
    backgroundColor: '#fff',
    padding: '20px',
    borderRadius: '8px',
    width: '300px',
    textAlign: 'center',
  },
  closeButton: {
    marginTop: '10px',
    padding: '5px 10px',
    backgroundColor: '#007BFF',
    border: 'none',
    color: 'white',
    borderRadius: '5px',
    cursor: 'pointer',
  },
};

export default SendPDF;
