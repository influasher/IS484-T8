import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Box,
  Divider,
} from "@mui/material";
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

function FeedbackModal({ open, onClose, selectedOption }) {
  const sentiment = selectedOption
    ? selectedOption.charAt(0).toUpperCase() + selectedOption.slice(1)
    : "N/A";

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xs"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 1,
          p: 1,
          boxShadow: "0 6px 24px rgba(0,0,0,0.12)",
        },
      }}
    >
      <DialogTitle
        sx={{
          textAlign: "center",
          fontWeight: 700,
          fontSize: "1.3rem",
          color: "success.main",
        }}
      >
        <CheckCircleIcon sx={{ fontSize: 48, mb: 1, color: "#4caf50" }} />
      </DialogTitle>

      <DialogContent sx={{ textAlign: "center", pb: 0 }}>
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          Feedback Submitted
        </Typography>
        <Typography variant="body1" sx={{ mb: 1.5 }}>
            You voted this news article as {sentiment}. Thank you for helping improve our models!
        </Typography>
      </DialogContent>

      <DialogActions sx={{ justifyContent: "flex-end", pr: 3, pb: 2 }}>
        <Button
          onClick={onClose}
          variant="contained"
          sx={{
            textTransform: "none",
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default FeedbackModal;
