import React from "react";
import { useParams } from "react-router-dom";
import ClientRecc from "../../components/clients/ClientRecc";
import ClientPortfolio from "../../components/clients/ClientPortfolio";
import { postData, getData } from '../../services/api';
import { Box,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  CircularProgress,
  Alert,
} from "@mui/material";

const RMIndvClientView = () => {
  const { id: clientId } = useParams();

  console.log('RMIndvClientView - clientId from params:', clientId);

  // Add-Transaction modal state
  const [openAdd, setOpenAdd] = React.useState(false);
  const [formType, setFormType] = React.useState("");
  const [formSource, setFormSource] = React.useState("");
  const [formQty, setFormQty] = React.useState("");
  const [formCurrency, setFormCurrency] = React.useState("");
  const [formAmount, setFormAmount] = React.useState("");
  const [formDesc, setFormDesc] = React.useState("");
  const [stockPrice, setStockPrice] = React.useState(null);
  const [loadingPrice, setLoadingPrice] = React.useState(false);
  const [priceError, setPriceError] = React.useState("");

  // Fetch stock price when source changes for Buy/Sell
  React.useEffect(() => {
    const fetchStockPrice = async () => {
      if ((formType === "Buy" || formType === "Sell") && formSource.trim()) {
        setLoadingPrice(true);
        setPriceError("");
        try {
          const response = await getData(`/entities/ticker/${formSource.trim()}/price`);
          if (response && response.data) {
            setStockPrice(response.data.price);
          } else {
            setPriceError("Unable to fetch stock price. Please check the ticker symbol.");
            setStockPrice(null);
          }
        } catch (error) {
          setPriceError("Unable to fetch stock price. Please check the ticker symbol.");
          setStockPrice(null);
        } finally {
          setLoadingPrice(false);
        }
      } else {
        setStockPrice(null);
        setPriceError("");
      }
    };

    // Debounce the API call
    const timeoutId = setTimeout(fetchStockPrice, 500);
    return () => clearTimeout(timeoutId);
  }, [formSource, formType]);

  // Calculate total amount
  const totalAmount = stockPrice && formQty ? (stockPrice * parseFloat(formQty)).toFixed(2) : "0.00";

  const handleOpenAdd = () => setOpenAdd(true);
  const handleCloseAdd = () => {
    setOpenAdd(false);
    setFormType("");
    setFormSource("");
    setFormQty("");
    setFormCurrency("");
    setFormAmount("");
    setFormDesc("");
    setStockPrice(null);
    setPriceError("");
  };

  const handleSubmitAdd = async (e) => {
    e.preventDefault();

    const payload = {
      client_id: clientId,
      datetime: new Date().toISOString(),
      type: formType.toUpperCase(),
      source: formSource.trim(),
      qty: formQty,
      currency: formCurrency,
      amount: parseFloat(formAmount) || 0,
      desc: formDesc.trim(),
    };

    try {
      console.log(payload);
      // TODO: fix postData to ensure /transactions is POST
      const jsonPayload = JSON.parse(JSON.stringify(payload));
      const response = await postData("/transactions/add_transaction", jsonPayload);

      if (response) {
        alert("Transaction added successfully!");
        handleCloseAdd();
        window.location.reload(); // Refresh to show new transaction
      } else {
        alert("Failed to add transaction. Please try again.");
      }
    } catch (err) {
      alert("Error adding transaction: " + (err?.message || "Unknown error"));
    }
  };

  return (
    <div>
      <ClientRecc />
      <Box
        sx={{
          minHeight: "100vh",
          bgcolor: (t) => t.palette.grey[100],
          p: { xs: 1.5, sm: 2.5, md: 3 },
        }}
      >
        <Paper
          elevation={1}
          sx={{ borderRadius: 3, bgcolor: "white", display: "flex", flexDirection: "column", alignItems: "center"}}
        >
        <ClientPortfolio clientId={clientId} />
        <Button onClick={handleOpenAdd} variant="contained" sx={{ m: 2 }} color="">
          Add new transaction
        </Button>
        </Paper>
        <Dialog
          open={openAdd}
          onClose={handleCloseAdd}
          PaperProps={{
              sx: {
                  borderRadius: 3,
                  bgcolor: "white",
                  width: "100%",
                  maxWidth: 520,
              },
          }}
      >
          <DialogTitle sx={{ fontWeight: 700 }}>Add New Transaction</DialogTitle>
          <DialogContent dividers>
              <Box component="form" onSubmit={handleSubmitAdd} sx={{ mt: 1.5, display: "grid", gap: 2 }}>
                  <TextField
                      label="Client ID"
                      type="text"
                      fullWidth
                      disabled
                      value={clientId || "N/A"}
                  />
                  <FormControl fullWidth required>
                      <InputLabel id="type-label">Type</InputLabel>
                      <Select
                          labelId="type-label"
                          label="Type"
                          value={formType}
                          onChange={(e) => setFormType(e.target.value)}
                      >
                          <MenuItem value="Deposit">Deposit</MenuItem>
                          <MenuItem value="Withdrawal">Withdrawal</MenuItem>
                          <MenuItem value="Buy">Buy</MenuItem>
                          <MenuItem value="Sell">Sell</MenuItem>
                          <MenuItem value="Dividend">Dividend</MenuItem>
                      </Select>
                  </FormControl>
                  <TextField
                      label="Source"
                      type="text"
                      fullWidth
                      required
                      value={formSource}
                      onChange={(e) => setFormSource(e.target.value)}
                      placeholder="e.g., AAPL, Bank Transfer"
                  />
                  {(formType === "Buy" || formType === "Sell") && (
                      <TextField
                          label="Quantity"
                          type="number"
                          fullWidth
                          required
                          value={formQty}
                          min={0}
                          onChange={(e) => setFormQty(e.target.value)}
                          placeholder="e.g., 1000.00"
                          inputProps={{ step: "0.01" }}
                      />
                  )}
                  {!(formType === "Buy" || formType === "Sell") && (
                  <FormControl fullWidth required>
                      <InputLabel id="currency-label">Currency</InputLabel>
                      <Select
                          labelId="currency-label"
                          label="Currency"
                          value={formCurrency}
                          onChange={(e) => setFormCurrency(e.target.value)}
                      >
                          <MenuItem value="USD">USD</MenuItem>
                          <MenuItem value="SGD">SGD</MenuItem>
                          <MenuItem value="EUR">EUR</MenuItem>
                          <MenuItem value="GBP">GBP</MenuItem>
                          <MenuItem value="JPY">JPY</MenuItem>
                      </Select>
                  </FormControl>
                  )}
                  {!(formType === "Buy" || formType === "Sell") && (
                  <TextField
                      label="Amount"
                      type="number"
                      fullWidth
                      required
                      value={formAmount}
                      min={0}
                      onChange={(e) => setFormAmount(e.target.value)}
                      placeholder="e.g., 1000.00"
                      inputProps={{ step: "0.01" }}
                  />
                  )}
                  {!(formType === "Buy" || formType === "Sell") && (
                  <TextField
                      label="Description"
                      type="text"
                      fullWidth
                      required
                      multiline
                      rows={3}
                      value={formDesc}
                      onChange={(e) => setFormDesc(e.target.value)}
                      placeholder="Transaction details"
                  />
                  )}
                  {(formType === "Buy" || formType === "Sell") && (
                      <Box sx={{ p: 2, bgcolor: "grey.50", borderRadius: 2 }}>
                          {loadingPrice && (
                              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                  <CircularProgress size={20} />
                                  <Typography variant="body2">Fetching stock price...</Typography>
                              </Box>
                          )}
                          {priceError && (
                              <Alert severity="error" sx={{ mb: 1 }}>
                                  {priceError}
                              </Alert>
                          )}
                          {stockPrice && !loadingPrice && (
                              <>
                                  <Typography variant="body2" sx={{ mb: 1 }}>
                                      <strong>Current Stock Price:</strong> ${stockPrice.toFixed(2)} USD
                                  </Typography>
                                  {formQty && (
                                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                          <strong>Total Amount:</strong> ${totalAmount} USD
                                      </Typography>
                                  )}
                              </>
                          )}
                      </Box>
                  )}
              </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, py: 2 }}>
              <Button onClick={handleCloseAdd} variant="text" color="red">
                  Cancel
              </Button>
              <Button
                  onClick={handleSubmitAdd}
                  variant="contained"
                  color="primary"
              >
                  Submit
              </Button>
          </DialogActions>
      </Dialog>
      </Box>
    </div>
  );
};

export default RMIndvClientView;
