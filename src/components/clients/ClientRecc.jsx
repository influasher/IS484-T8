import React from "react";
import { useParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Grid from "@mui/material/Grid";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import HealthAndSafetyIcon from "@mui/icons-material/HealthAndSafety";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import TextField from "@mui/material/TextField";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import ChipMUI from "@mui/material/Chip";
import Slider from "@mui/material/Slider";
import useFetch from "../../hooks/useFetch";
import recommendationService from "../../services/recommendationService";
import { putData } from "../../services/api";

const ALL_SECTORS = [
    "Information Technology",
    "Financials",
    "Health Care",
    "Consumer Staples",
    "Industrials",
    "Materials",
    "Communication Services",
    "Consumer Discretionary",
    "Utilities",
    "Energy",
    "Real Estate",
    "Automotive",
];

const RISK_LABELS = ["Zero", "Medium", "Moderate", "High", "Very High"];

const RISK_VALUES = {
    "Zero": 0,
    "Medium": 1,
    "Moderate": 2,
    "High": 3,
    "Very High": 4
};

// Reverse mapping for getting string from index
const getRiskLabelFromIndex = (index) => RISK_LABELS[index] || "Moderate";

const getActionColor = (action) => {
    return action === 'BUY' ? '#4caf50' : '#f44336';
};

const getRiskColor = (riskLevel) => {
    const colors = {
        'LOW': '#4caf50',
        'MODERATE': '#ff9800',
        'HIGH': '#f44336'
    };
    return colors[riskLevel] || '#9e9e9e';
};

const getHealthScoreColor = (score) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
};

// Enhanced recommendation card
const RecommendationCard = ({ recommendation }) => {
    const actionColor = getActionColor(recommendation.action);
    const riskColor = getRiskColor(recommendation.risk_level);

    return (
        <Paper
            variant="outlined"
            sx={{ borderRadius: 2, bgcolor: "white", px: 2, py: 2, width: "100%" }}
        >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, letterSpacing: 0.2 }}>
                    {recommendation.entity_name} ({recommendation.ticker})
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                        label={recommendation.action}
                        icon={recommendation.action === 'BUY' ? <TrendingUpIcon /> : <TrendingDownIcon />}
                        sx={{
                            bgcolor: actionColor,
                            color: 'white',
                            fontWeight: 600,
                            '& .MuiChip-icon': { color: 'white' }
                        }}
                    />
                    <Chip
                        label={recommendation.risk_level}
                        sx={{
                            bgcolor: riskColor,
                            color: 'white',
                            fontWeight: 500
                        }}
                    />
                </Box>
            </Box>

            <Typography variant="body2" sx={{ color: "text.secondary", mb: 0.5 }}>
                Sentiment Score: {recommendation.sentiment_score?.toFixed(1)}
                | Confidence: {(recommendation.recommendation_confidence * 100)?.toFixed(0)}%
            </Typography>

            {recommendation.suggested_amount && (
                <Typography variant="body2" sx={{ color: "text.secondary", mb: 0.5 }}>
                    Suggested Amount: ${recommendation.suggested_amount?.toLocaleString()}
                    {recommendation.suggested_allocation_percent &&
                        ` (${recommendation.suggested_allocation_percent?.toFixed(1)}%)`
                    }
                </Typography>
            )}

            {recommendation.current_price && (
                <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
                    Current Price: ${recommendation.current_price?.toFixed(2)}
                </Typography>
            )}

            <Typography variant="body2" sx={{ mb: 1.5, fontStyle: 'italic' }}>
                {recommendation.reasoning}
            </Typography>
        </Paper>
    );
};

const ClientRecc = () => {
    const { id: clientId } = useParams();

    // Fetch client data and preferences
    const { data: clientData, loading: clientLoading } = useFetch(`/user/${clientId}`);
    const { data: preferencesData, loading: preferencesLoading } = useFetch(`/user/${clientId}/preferences`);
    const { data: recommendationsData, loading: recommendationsLoading } = useFetch(`/recommendations/client/${clientId}`);
    const { data: healthData, loading: healthLoading } = useFetch(`/recommendations/client/${clientId}/health`);

    // PDF generation state
    const [isGeneratingPDF, setIsGeneratingPDF] = React.useState(false);
    const [pdfError, setPdfError] = React.useState("");

    // Extract data from API responses
    const client = clientData?.data || {};
    const preferences = preferencesData?.data || {};
    const clientRecommendations = recommendationsData?.recommendations || [];
    const portfolioHealth = healthData?.health_data || {};


    const handleGeneratePDF = async () => {
        setIsGeneratingPDF(true);
        setPdfError("");

        try {
            await recommendationService.generateClientPDFReport(clientId, client.name);
        } catch (error) {
            setPdfError(error.message);
        } finally {
            setIsGeneratingPDF(false);
        }
    };

    const isLoading = clientLoading || preferencesLoading || recommendationsLoading || healthLoading;

    // Edit modal state
    const [openEdit, setOpenEdit] = React.useState(false);
    const [formData, setFormData] = React.useState({
        name: '',
        email: '',
        risk_cap: '',
        sectors: [],
        stop_loss_tolerance: -10,
        max_single_position_percent: 15,
        max_sector_allocation_percent: 40,
        min_cash_reserve_percent: 10
    });
    const [updateError, setUpdateError] = React.useState('');
    const [isUpdating, setIsUpdating] = React.useState(false);

    const handleOpenEdit = () => {
        // Pre-fill form with current client and preferences data
        setFormData({
            name: clientName,
            email: client.email || '',
            risk_cap: preferences.risk_cap || '',
            sectors: preferences.sectors || [],
            stop_loss_tolerance: preferences.stop_loss_tolerance || -10,
            max_single_position_percent: preferences.max_single_position_percent || 15,
            max_sector_allocation_percent: preferences.max_sector_allocation_percent || 40,
            min_cash_reserve_percent: preferences.min_cash_reserve_percent || 10
        });
        setUpdateError('');
        setOpenEdit(true);
    };

    const handleCloseEdit = () => {
        setOpenEdit(false);
        setUpdateError('');
    };

    const handleSaveEdit = async (e) => {
        if (e) e.preventDefault();
        setIsUpdating(true);
        setUpdateError('');

        try {
            // Update client preferences using our API service (includes JWT token)
            const response = await putData(`/user/${clientId}/preferences`, {
                risk_cap: formData.risk_cap,
                sectors: formData.sectors,
                stop_loss_tolerance: formData.stop_loss_tolerance,
                max_single_position_percent: formData.max_single_position_percent,
                max_sector_allocation_percent: formData.max_sector_allocation_percent,
                min_cash_reserve_percent: formData.min_cash_reserve_percent
            });

            if (!response) {
                throw new Error('Failed to update client preferences');
            }

            // Close modal and optionally refresh
            handleCloseEdit();
            window.location.reload(); // Simple approach to refresh data

        } catch (error) {
            setUpdateError(error.message || 'Failed to update client preferences');
        } finally {
            setIsUpdating(false);
        }
    };

    const handleDeleteSectorChip = (sector) => {
        setFormData(prev => ({
            ...prev,
            sectors: prev.sectors.filter(s => s !== sector)
        }));
    };


    // Show loading state
    if (isLoading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
                <CircularProgress />
            </Box>
        );
    }

    // Show error state if client not found
    if (!client.id) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    Client not found or you don't have permission to view this client.
                </Alert>
            </Box>
        );
    }

    const clientName = client.name || `${client.first_name || ''} ${client.last_name || ''}`.trim() || 'Unknown Client';

    return (
        <Box
            sx={{
                minHeight: "100vh",
                bgcolor: (t) => t.palette.grey[100],
                p: { xs: 1.5, sm: 2.5, md: 3 },
            }}
        >
            {pdfError && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setPdfError("")}>
                    {pdfError}
                </Alert>
            )}

            {/* Header row */}
            <Box
                sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    flexWrap: "wrap",
                    mb: 2,
                }}
            >
                {/* Left: Client name */}
                <Typography variant="h4" sx={{ fontWeight: 800, mr: 1, color: "black" }}>
                    {clientName}
                </Typography>

                {/* Right: info boxes aligned right */}
                <Box sx={{ ml: "auto", display: "flex", gap: 1.5, alignItems: "center", flexWrap: "wrap" }}>
                    {/* Portfolio Health Score */}
                    {portfolioHealth.overall_health_score && (
                        <Chip
                            icon={<HealthAndSafetyIcon />}
                            label={`Health Score: ${portfolioHealth.overall_health_score.toFixed(0)}/100`}
                            sx={{
                                bgcolor: recommendationService.getHealthScoreColor(portfolioHealth.overall_health_score),
                                color: "#fff",
                                borderRadius: 2,
                                "& .MuiChip-label": { px: 0.75 },
                                "& .MuiChip-icon": { color: "#fff" },
                            }}
                        />
                    )}

                    {/* Risk Profile */}
                    {preferences.risk_cap && (
                        <Chip
                            label={`Risk Profile: ${preferences.risk_cap}`}
                            sx={{
                                bgcolor: "#222",
                                color: "#fff",
                                borderRadius: 2,
                                "& .MuiChip-label": { px: 0.75 },
                            }}
                        />
                    )}

                    {/* Selected sectors - only show if there are valid sectors */}
                    {(preferences.sectors || []).filter(s => typeof s === 'string' && ALL_SECTORS.includes(s)).length > 0 && (
                        <Paper
                            elevation={0}
                            sx={{
                                bgcolor: "white",
                                borderRadius: 5,
                                px: 2,
                                py: 1,
                                display: "flex",
                                alignItems: "center",
                                gap: 1.25,
                                flexWrap: "wrap",
                            }}
                        >
                            <Typography variant="body2" sx={{ color: "text.secondary" }}>
                                Sectors
                            </Typography>
                            <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap" }}>
                                {(preferences.sectors || [])
                                    .filter(s => typeof s === 'string' && ALL_SECTORS.includes(s))
                                    .map((s) => (
                                        <Chip
                                            key={s}
                                            label={s}
                                            sx={{
                                                bgcolor: "#222",
                                                color: "#fff",
                                                borderRadius: 2,
                                            }}
                                        />
                                    ))}
                            </Box>
                        </Paper>
                    )}

                    {/* Edit button */}
                    <IconButton
                        aria-label="Edit client"
                        onClick={handleOpenEdit}
                        size="small"
                        sx={{
                            bgcolor: "#f3f4f6",
                            border: "1px solid",
                            borderColor: (t) => t.palette.grey[300],
                            "&:hover": { bgcolor: "#e5e7eb" },
                        }}
                    >
                        <EditRoundedIcon fontSize="small" />
                    </IconButton>
                </Box>
            </Box>
           

            {/* Big white recommendations card */}
            <Paper elevation={1} sx={{ borderRadius: 3, p: { xs: 2, sm: 3 }, bgcolor: "white" }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 2, gap: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        Today&apos;s Top Recommendations
                    </Typography>

                    <Box sx={{ ml: "auto" }}>
                        <Button
                            variant="contained"
                            onClick={handleGeneratePDF}
                            disabled={isGeneratingPDF}
                            sx={{
                                bgcolor: "#212121",
                                color: "#fff",
                                textTransform: "none",
                                borderRadius: 2,
                                px: 2,
                                "&:hover": { bgcolor: "#111" },
                            }}
                            startIcon={isGeneratingPDF ? <CircularProgress size={16} color="inherit" /> : <DownloadOutlinedIcon />}
                        >
                            {isGeneratingPDF ? "Generating..." : "Generate Report"}
                        </Button>
                    </Box>
                </Box>

                {/* Recommendations List */}
                {clientRecommendations.length === 0 ? (
                    <Alert severity="info">
                        No recommendations available for this client at the moment.
                    </Alert>
                ) : (
                    <Box sx={{ display: "grid", gap: 2.25 }}>
                        {clientRecommendations.map((rec, index) => (
                            <RecommendationCard key={`${rec.entity_id}-${index}`} recommendation={rec} />
                        ))}
                    </Box>
                )}
            </Paper>

            {/* Edit Client Modal */}
            <Dialog
                open={openEdit}
                onClose={handleCloseEdit}
                maxWidth="md"
                fullWidth
                PaperProps={{
                    sx: {
                        borderRadius: 3,
                        bgcolor: "white",
                    },
                }}
            >
                <DialogTitle sx={{ fontWeight: 700 }}>Edit Client Preferences</DialogTitle>
                <DialogContent dividers>
                    {updateError && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {updateError}
                        </Alert>
                    )}

                    <Box component="form" onSubmit={handleSaveEdit} sx={{ mt: 1.5, display: "grid", gap: 2 }}>
                        {/* Basic Information */}
                        <Typography variant="h6" sx={{ fontWeight: 600, mt: 1 }}>
                            Basic Information
                        </Typography>

                        <TextField
                            label="Client Name"
                            fullWidth
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            disabled
                            helperText="Client name cannot be changed from this view"
                        />

                        <TextField
                            label="Email"
                            type="email"
                            fullWidth
                            value={formData.email}
                            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                            disabled
                            helperText="Email cannot be changed from this view"
                        />

                        {/* Risk Management */}
                        <Typography variant="h6" sx={{ fontWeight: 600, mt: 2 }}>
                            Risk Management
                        </Typography>

                        <Box sx={{ px: 0, py: 1, mx: 1.5 }}>
                            <Typography variant="body1" sx={{ mb: 1, fontWeight: 500 }}>
                                Risk Profile
                            </Typography>
                            <Slider
                                value={RISK_VALUES[formData.risk_cap] !== undefined ? RISK_VALUES[formData.risk_cap] : 2}
                                min={0}
                                max={4}
                                step={1}
                                marks={[
                                    { value: 0, label: "Zero" },
                                    { value: 1, label: "Medium" },
                                    { value: 2, label: "Moderate" },
                                    { value: 3, label: "High" },
                                    { value: 4, label: "Very High" },
                                ]}
                                valueLabelDisplay="auto"
                                valueLabelFormat={(value) => getRiskLabelFromIndex(value)}
                                onChange={(_, val) => {
                                    const newRiskCap = getRiskLabelFromIndex(val);
                                    // Get risk profile defaults for dynamic updates
                                    const riskDefaults = {
                                        'Zero': { max_single: 5.0, max_sector: 20.0, min_cash: 25.0 },
                                        'Medium': { max_single: 10.0, max_sector: 30.0, min_cash: 15.0 },
                                        'Moderate': { max_single: 15.0, max_sector: 40.0, min_cash: 10.0 },
                                        'High': { max_single: 20.0, max_sector: 50.0, min_cash: 5.0 },
                                        'Very High': { max_single: 25.0, max_sector: 60.0, min_cash: 2.0 }
                                    };
                                    const defaults = riskDefaults[newRiskCap] || riskDefaults['Moderate'];

                                    setFormData(prev => ({
                                        ...prev,
                                        risk_cap: newRiskCap,
                                        max_single_position_percent: defaults.max_single,
                                        max_sector_allocation_percent: defaults.max_sector,
                                        min_cash_reserve_percent: defaults.min_cash
                                    }));
                                }}
                                sx={{ mx: 1, width: "calc(100% - 20px)" }}
                            />
                        </Box>

                        <TextField
                            label="Stop Loss Tolerance (%)"
                            type="number"
                            fullWidth
                            value={formData.stop_loss_tolerance}
                            onChange={(e) => setFormData(prev => ({ ...prev, stop_loss_tolerance: parseFloat(e.target.value) }))}
                            helperText="Maximum loss percentage before selling (e.g., -10 for 10% loss)"
                            inputProps={{ step: 0.1, max: 0 }}
                        />

                        {/* Investment Preferences */}
                        <Typography variant="h6" sx={{ fontWeight: 600, mt: 2 }}>
                            Investment Preferences
                        </Typography>

                        <FormControl fullWidth>
                            <InputLabel>Preferred Sectors</InputLabel>
                            <Select
                                multiple
                                value={formData.sectors}
                                label="Preferred Sectors"
                                onChange={(e) => setFormData(prev => ({ ...prev, sectors: e.target.value }))}
                                renderValue={(selected) => (
                                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                                        {selected.map((value) => (
                                            <ChipMUI
                                                key={value}
                                                label={value}
                                                onDelete={() => handleDeleteSectorChip(value)}
                                                sx={{ borderRadius: 1.5 }}
                                            />
                                        ))}
                                    </Box>
                                )}
                            >
                                {ALL_SECTORS.map((sector) => (
                                    <MenuItem key={sector} value={sector}>
                                        {sector}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        <TextField
                            label="Stop Loss Tolerance (%)"
                            type="number"
                            fullWidth
                            required
                            value={formData.stop_loss_tolerance}
                            onChange={(e) => setFormData(prev => ({ ...prev, stop_loss_tolerance: parseFloat(e.target.value) }))}
                            helperText="Maximum acceptable loss percentage before stop loss triggers"
                            inputProps={{ step: 0.1, min: -50, max: 0 }}
                        />

                        {/* Position Limits */}
                        <Typography variant="h6" sx={{ fontWeight: 600, mt: 2 }}>
                            Position Limits
                        </Typography>

                        <TextField
                            label="Maximum Single Position (%)"
                            type="number"
                            fullWidth
                            value={formData.max_single_position_percent}
                            onChange={(e) => setFormData(prev => ({ ...prev, max_single_position_percent: parseFloat(e.target.value) }))}
                            helperText="Maximum percentage of portfolio in any single stock"
                            inputProps={{ step: 0.1, min: 1, max: 50 }}
                        />

                        <TextField
                            label="Maximum Sector Allocation (%)"
                            type="number"
                            fullWidth
                            value={formData.max_sector_allocation_percent}
                            onChange={(e) => setFormData(prev => ({ ...prev, max_sector_allocation_percent: parseFloat(e.target.value) }))}
                            helperText="Maximum percentage of portfolio in any single sector"
                            inputProps={{ step: 0.1, min: 5, max: 100 }}
                        />

                        <TextField
                            label="Minimum Cash Reserve (%)"
                            type="number"
                            fullWidth
                            value={formData.min_cash_reserve_percent}
                            onChange={(e) => setFormData(prev => ({ ...prev, min_cash_reserve_percent: parseFloat(e.target.value) }))}
                            helperText="Minimum percentage of portfolio to keep as cash"
                            inputProps={{ step: 0.1, min: 0, max: 50 }}
                        />
                    </Box>
                </DialogContent>
                <DialogActions sx={{ px: 3, py: 2 }}>
                    <Button onClick={handleCloseEdit} variant="text" disabled={isUpdating}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSaveEdit}
                        variant="contained"
                        color="black"
                        disabled={isUpdating}
                        sx={{ "&:hover": { bgcolor: "#6b6b6bff" } }}
                    >
                        {isUpdating ? "Saving..." : "Save Changes"}
                    </Button>
                </DialogActions>
            </Dialog>

        </Box>
    );
};

export default ClientRecc;
