import React, { useState } from 'react';
import { FaDownload } from 'react-icons/fa'; // Import download icon
import { postDataBlob } from '../../services/api';
import DownloadIcon from '@mui/icons-material/Download';
import { Button } from '@mui/material';


const ReportButton = ({ EntityName }) => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [showPopup, setShowPopup] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    setStatus('Generating report...');
    setShowPopup(true); // Show the popup while generating the report

    try {
      // Send the entity name to backend for PDF generation
      const response = await postDataBlob(`/pdf/generate-pdf`, JSON.stringify({ entity_name: EntityName }));

      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${EntityName}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setStatus('Report generated successfully!');
    } catch (err) {
      console.error("Error generating report:", err);
      setStatus('Error generating report.');
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
        variant="outlined" 
        startIcon={<DownloadIcon />}
        onClick={generateReport}
        loading={loading}
        loadingPosition="start"
      >
        Download
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
    backgroundColor: '#007BFF', // Button color
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

export default ReportButton;
