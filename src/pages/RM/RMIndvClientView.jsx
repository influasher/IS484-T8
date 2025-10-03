import React from "react";
import { useParams } from "react-router-dom";
import ClientRecc from "../../components/clients/ClientRecc";
import ClientPortfolio from "../../components/clients/ClientPortfolio";
import { apiClient } from "../../services/api";
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
} from "@mui/material";

const RMIndvClientView = () => {
  const { clientId } = useParams();

  // Add-Transaction modal state
  const [openAdd, setOpenAdd] = React.useState(false);
  const [formSource, setFormSource] = React.useState("");
  const [formType, setFormType] = React.useState("");
  const [formCurrency, setFormCurrency] = React.useState("");
  const [formAmount, setFormAmount] = React.useState("");
  const [formDesc, setFormDesc] = React.useState("");

  const handleOpenAdd = () => setOpenAdd(true);
  const handleCloseAdd = () => {
    setOpenAdd(false);
    setFormSource("");
    setFormType("");
    setFormCurrency("");
    setFormAmount("");
    setFormDesc("");
  };

  const handleSubmitAdd = async (e) => {
    e.preventDefault();

    const payload = {
      client_id: clientId,
      source: formSource.trim(),
      type: formType,
      currency: formCurrency,
      amount: parseFloat(formAmount),
      description: formDesc.trim(),
    };

    try {
      const res = await apiClient.post("/transactions/create", payload);

      alert("Transaction added successfully!");
      handleCloseAdd();
      // Optionally refresh the transaction list
    } catch (err) {
      alert("Error adding transaction: " + (err.response?.data?.message || err.message));
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
        <ClientPortfolio/>
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
                  <TextField
                      label="Source"
                      type="text"
                      fullWidth
                      required
                      value={formSource}
                      onChange={(e) => setFormSource(e.target.value)}
                      placeholder="e.g., AAPL, Bank Transfer"
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
                          {/* <MenuItem value="Capital Gains">Capital Gains</MenuItem> */}
                          {/* <MenuItem value="Interest">Interest</MenuItem> */}
                      </Select>
                  </FormControl>
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
                  <TextField
                      label="Amount"
                      type="number"
                      fullWidth
                      required
                      value={formAmount}
                      onChange={(e) => setFormAmount(e.target.value)}
                      placeholder="e.g., 1000.00"
                      inputProps={{ step: "0.01" }}
                  />
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
