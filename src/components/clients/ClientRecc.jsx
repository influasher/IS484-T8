import React from "react";
import { useParams } from "react-router-dom";
import { apiClient } from "../../services/api";
import { Box, Paper, Typography, Chip, IconButton, Button, CircularProgress, Alert, Grid, Dialog, DialogTitle, 
DialogContent, DialogActions, TextField, FormControl, InputLabel, Select, MenuItem, Slider } from "@mui/material";
import { DownloadOutlined as DownloadOutlinedIcon, EditRounded as EditRoundedIcon, TrendingUp as TrendingUpIcon, 
TrendingDown as TrendingDownIcon, HealthAndSafety as HealthAndSafetyIcon } from "@mui/icons-material";
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
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

// Sector color mapping
const SECTOR_COLORS = {
    "Information Technology": "#2196F3",
    "Financials": "#FF9800",
    "Health Care": "#4CAF50",
    "Consumer Staples": "#9C27B0",
    "Industrials": "#795548",
    "Materials": "#607D8B",
    "Communication Services": "#E91E63",
    "Consumer Discretionary": "#00BCD4",
    "Utilities": "#FFEB3B",
    "Energy": "#F44336",
    "Real Estate": "#8BC34A",
    "Automotive": "#3F51B5",
    "Technology": "#2196F3",
    "Finance": "#FF9800",
    "Healthcare": "#4CAF50",
};

const getSectorColor = (sectors) => {
    if (!sectors || sectors.length === 0) return '#9e9e9e';
    // Return the color of the first sector if available
    return SECTOR_COLORS[sectors[0]] || '#9e9e9e';
};

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

// Bubble Chart Component
const RecommendationBubbleChart = ({ recommendations, onBubbleClick, selectedRecommendation }) => {
    // Transform recommendations into bubble chart data
    const chartData = recommendations.map((rec) => ({
        x: rec.sentiment_score || 0,
        y: rec.recommendation_confidence * 100 || 50,
        z: (rec.recommendation_confidence * 100) * 5, // Size based on confidence
        name: rec.ticker,
        fullName: rec.entity_name,
        sector: rec.sector,
        action: rec.action,
        entity_id: rec.entity_id,
        isSelected: selectedRecommendation === rec.entity_id,
    }));

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <Paper sx={{ p: 1.5}}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {data.fullName} ({data.name})
                    </Typography>
                    <Typography variant="caption" display="block">
                        Sentiment: {data.x.toFixed(1)}
                    </Typography>
                    <Typography variant="caption" display="block">
                        Confidence: {data.y.toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" display="block">
                        Sector: {data.sector && data.sector.length > 0 ? data.sector.join(', ') : 'N/A'}
                    </Typography>
                    <Typography variant="caption" display="block" sx={{ color: getActionColor(data.action) }}>
                        Action: {data.action}
                    </Typography>
                </Paper>
            );
        }
        return null;
    };

    return (
        <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <XAxis
                    type="number"
                    dataKey="x"
                    name="Sentiment Score"
                    domain={[-100, 100]}
                    label={{ value: 'Sentiment Score', position: 'insideBottom', offset: -10 }}
                />
                <YAxis
                    type="number"
                    dataKey="y"
                    name="Confidence"
                    domain={[0, 100]}
                    label={{ value: 'Confidence (%)', angle: -90, position: 'insideLeft' }}
                />
                <ZAxis type="number" dataKey="z" range={[100, 1000]} />
                <Tooltip content={<CustomTooltip />} />
                <Scatter
                    data={chartData}
                    onClick={(data) => onBubbleClick(data.entity_id)}
                    style={{ cursor: 'pointer' }}
                >
                    {chartData.map((entry, index) => (
                        <Cell
                            key={`cell-${index}`}
                            fill={getSectorColor(entry.sector)}
                            opacity={entry.isSelected ? 1 : 0.7}
                            stroke={entry.isSelected ? '#000' : 'none'}
                            strokeWidth={entry.isSelected ? 3 : 0}
                        />
                    ))}
                </Scatter>
            </ScatterChart>
        </ResponsiveContainer>
    );
};

// Enhanced recommendation card
const RecommendationCard = ({ recommendation, isHighlighted }) => {
    const actionColor = getActionColor(recommendation.action);
    const riskColor = getRiskColor(recommendation.risk_level);

    return (
        <Paper
            variant="outlined"
            id={`rec-${recommendation.entity_id}`}
            sx={{
                borderRadius: 2,
                bgcolor: isHighlighted ? "#fffde7" : "white",
                px: 2,
                py: 2,
                width: "100%",
                border: isHighlighted ? "2px solid #fbc02d" : "1px solid rgba(0, 0, 0, 0.12)",
                transition: "all 0.3s ease",
            }}
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

    // Bubble chart selection state
    const [selectedRecommendation, setSelectedRecommendation] = React.useState(null);

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

    // Handle bubble chart click
    const handleBubbleClick = (entityId) => {
        setSelectedRecommendation(entityId);
        // Scroll to the recommendation card
        const element = document.getElementById(`rec-${entityId}`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
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

            {/* Header with Generate Report button */}
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

            {/* Two column layout: Bubble Chart (top/left) and Recommendations (bottom/right) */}
            <Box sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", md: "1fr 1.2fr" },
                gap: 3
            }}>
                {/* Bubble Chart */}
                <Paper elevation={1} sx={{ borderRadius: 3, p: { xs: 2, sm: 3 }, bgcolor: "white" }}>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                        Recommendation Landscape
                    </Typography>
                    <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
                        Click on a bubble to highlight the recommendation. Size = Confidence, Color = Sector
                    </Typography>
                    {clientRecommendations.length === 0 ? (
                        <Alert severity="info">
                            No data to display
                        </Alert>
                    ) : (
                        <>
                            <RecommendationBubbleChart
                                recommendations={clientRecommendations}
                                onBubbleClick={handleBubbleClick}
                                selectedRecommendation={selectedRecommendation}
                            />
                            {/* Sector Legend */}
                            <Box sx={{ mt: 2, pt: 2, borderTop: "1px solid #e0e0e0" }}>
                                <Typography variant="caption" sx={{ fontWeight: 600, mb: 1, display: "block" }}>
                                    Sector Legend:
                                </Typography>
                                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                                    {[...new Set(clientRecommendations
                                        .filter(rec => rec.sector && rec.sector.length > 0)
                                        .flatMap(rec => rec.sector)
                                    )].map((sector) => (
                                        <Box
                                            key={sector}
                                            sx={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: 0.5,
                                            }}
                                        >
                                            <Box
                                                sx={{
                                                    width: 12,
                                                    height: 12,
                                                    borderRadius: "50%",
                                                    bgcolor: SECTOR_COLORS[sector] || "#9e9e9e",
                                                }}
                                            />
                                            <Typography variant="caption" sx={{ fontSize: "0.7rem" }}>
                                                {sector}
                                            </Typography>
                                        </Box>
                                    ))}
                                </Box>
                            </Box>
                        </>
                    )}

                </Paper>

                {/* Recommendations List */}
                <Paper elevation={1} sx={{ borderRadius: 3, p: { xs: 2, sm: 3 }, bgcolor: "white" }}>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                        Recommendations
                    </Typography>
                    {clientRecommendations.length === 0 ? (
                        <Alert severity="info">
                            No recommendations available for this client at the moment.
                        </Alert>
                    ) : (
                        <Box sx={{ display: "grid", gap: 2.25, maxHeight: "600px", overflowY: "auto", pr: 1 }}>
                            {clientRecommendations.map((rec, index) => (
                                <RecommendationCard
                                    key={`${rec.entity_id}-${index}`}
                                    recommendation={rec}
                                    isHighlighted={selectedRecommendation === rec.entity_id}
                                />
                            ))}
                        </Box>
                    )}
                </Paper>
            </Box>

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
