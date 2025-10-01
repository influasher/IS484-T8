import React from "react";
import { useParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import TextField from "@mui/material/TextField";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Slider from "@mui/material/Slider";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import ChipMUI from "@mui/material/Chip";
import useFetch from "../../hooks/useFetch";

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
];

const RISK_LABELS = ["Zero", "Medium", "Moderate", "High", "Very High"];
function riskValueToLabel(val) {
    if (typeof val !== "number") return "Zero";
    return RISK_LABELS[val] ?? "Zero";
}
function riskLabelToValue(label) {
    const idx = RISK_LABELS.indexOf(label);
    return idx !== -1 ? idx : 0; // default to 0 if not found
  }

// Small recommendation card
const PortfRecc = ({ name, sentiment, price }) => {
    return (
        <Paper
            variant="outlined"
            sx={{ borderRadius: 2, bgcolor: "white", px: 2, py: 1.75, width: "100%" }}
        >
            <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 0.5, letterSpacing: 0.2 }}>
                {name}
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 0.25 }}>
                Today&apos;s Sentiment Score: {sentiment}
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 1.25 }}>
                Price: {price}
            </Typography>
            <Button variant="contained" color="black" sx={{ textTransform: "none" }}>
                View More
            </Button>
        </Paper>
    );
};

const ClientRecc = () => {
    const { id: routeId } = useParams();
    const userUrl = `/user/${routeId}`;
    const url = `/user/${routeId}/preferences`;
    const { data: userData, loading: userLoading, error: userError } = useFetch(userUrl);
    const { data, loading, error } = useFetch(url);

    // Display state (what the page shows)
    const [dispName, setDispName] = React.useState("");
    const [dispEmail, setDispEmail] = React.useState("");
    const [dispOverallPL, setDispOverallPL] = React.useState(0);
    const [dispRisk, setDispRisk] = React.useState(0);
    const [dispStopLoss, setDispStopLoss] = React.useState(0);
    const [dispSectors, setDispSectors] = React.useState([]);

    // Editor modal state (pre-filled form values)
    const [openEdit, setOpenEdit] = React.useState(false);
    const [formFirstName, setFormFirstName] = React.useState("");
    const [formLastName, setFormLastName] = React.useState("");
    const [formEmail, setFormEmail] = React.useState(dispEmail);
    const [formSectors, setFormSectors] = React.useState(dispSectors);
    const [formStopLossTolerance, setFormStopLossTolerance] = React.useState(dispStopLoss);
    const [formRiskThreshold, setFormRiskThreshold] = React.useState(dispRisk);

    // Update state when data arrives
    React.useEffect(() => {
        if (data) {
            console.log("Fetched preferences data:", data);
            setDispOverallPL(data.data.overall_pl || "");
            setDispRisk(data.data.risk_cap || 0);
            setDispStopLoss(data.data.stop_loss_tolerance || 0);
            setDispSectors(data.data.sectors || []);
        }
    }, [data]);
    
    React.useEffect(() => {
        if (userData) {
            setDispName(`${userData.data.first_name} ${userData.data.last_name}`|| "");
            setDispEmail(userData.data.email || "");
            setFormFirstName(userData.data.first_name || "");
            setFormLastName(userData.data.last_name || "");
        }
    }, [userData]);


    const handleOpenEdit = () => {
        // preload form with current display values
        setFormFirstName(formFirstName);
        setFormLastName(formLastName);
        setFormEmail(dispEmail);
        setFormSectors(dispSectors);
        setFormStopLossTolerance(dispStopLoss);
        setFormRiskThreshold(riskLabelToValue(dispRisk));
        setOpenEdit(true);
    };

    const handleCloseEdit = () => {
        setOpenEdit(false);
    };

    const handleSaveEdit = async (e) => {
        if (e) e.preventDefault();
    
        const payload = {
            first_name: formFirstName.trim(),
            last_name: formLastName.trim(),
            email: formEmail.trim(),
            risk_cap: riskValueToLabel(formRiskThreshold),
            sectors: formSectors,
            stop_loss_tolerance: formStopLossTolerance,
            updated_at: new Date().toISOString(),
        };

        try {
            // need to change the following to a hostable url instead of localhost
            const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
            const res = await fetch(`${API_BASE_URL}/user/${routeId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) throw new Error("Failed to update client");
            const result = await res.json();
            console.log("Update result:", result);

            // apply form values back to display state
            setDispName(`${formFirstName.trim()} ${formLastName.trim()}`|| "");
            setDispEmail(formEmail.trim());
            setDispRisk(riskValueToLabel(formRiskThreshold));
            setDispSectors(formSectors);
            handleCloseEdit();
        } catch (err) {
            alert("Error updating client: " + err.message);
        }
    };

    const handleDeleteSectorChipInForm = (sector) => {
        setFormSectors((prev) => prev.filter((s) => s !== sector));
    };

    const recommendations = [
        { name: "APPL", sentiment: 23.8, price: 109.5 },
        { name: "HSBC", sentiment: 23.8, price: 109.5 },
        { name: "XOM", sentiment: 23.8, price: 109.5 },
    ];

    return (
        <Box
            sx={{
                minHeight: "100vh",
                bgcolor: (t) => t.palette.grey[100],
                p: { xs: 1.5, sm: 2.5, md: 3 },
            }}
        >
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
                    {dispName}
                </Typography>

                {/* Right: info box aligned right */}
                {data && (
                    <Box sx={{ ml: "auto" }}>
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
                                maxWidth: { xs: "100%", md: 720 },
                                justifyContent: "flex-end",
                            }}
                        >
                            {/* Risk badge */}
                            <Chip
                                label={`Risk Rating: ${dispRisk}`}
                                sx={{
                                    bgcolor: "#222",
                                    color: "#fff",
                                    borderRadius: 2,
                                    "& .MuiChip-label": { px: 0.75 },
                                }}
                            />

                            <Typography variant="body2" sx={{ color: "text.secondary" }}>
                                Sector
                            </Typography>

                            {/* Selected sectors (read-only here) */}
                            <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap", mr: 0.5 }}>
                                {dispSectors.map((s) => (
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

                            {/* Edit button opens modal */}
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
                        </Paper>
                    </Box>
                 )}
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
                            sx={{
                                bgcolor: "#212121",
                                color: "#fff",
                                textTransform: "none",
                                borderRadius: 2,
                                px: 2,
                                "&:hover": { bgcolor: "#111" },
                            }}
                            startIcon={<DownloadOutlinedIcon />}
                        >
                            Generate Report
                        </Button>
                    </Box>
                </Box>

                <Box sx={{ display: "grid", gap: 2.25 }}>
                    {recommendations.map((r) => (
                        <PortfRecc key={r.name} name={r.name} sentiment={r.sentiment} price={r.price} />
                    ))}
                </Box>
            </Paper>

            {/* Edit Client Modal (re-uses the same patterns as your ClientCards dialog) */}
            <Dialog
                open={openEdit}
                onClose={handleCloseEdit}
                PaperProps={{
                    sx: {
                        borderRadius: 3,
                        bgcolor: "white",
                        width: "100%",
                        maxWidth: 560,
                    },
                }}
            >
                <DialogTitle sx={{ fontWeight: 700 }}>Edit Client</DialogTitle>
                <DialogContent dividers>
                    <Box
                        component="form"
                        onSubmit={handleSaveEdit}
                        sx={{ mt: 1.5, display: "grid", gap: 2 }}
                    >
                        <TextField
                            label="First Name"
                            type="text"
                            fullWidth
                            required
                            value={formFirstName}
                            onChange={(e) => setFormFirstName(e.target.value)}
                        />
                        <TextField
                            label="Last Name"
                            type="text"
                            fullWidth
                            required
                            value={formLastName}
                            onChange={(e) => setFormLastName(e.target.value)}
                        />

                        <TextField
                            label="Email"
                            type="email"
                            fullWidth
                            required
                            value={formEmail}
                            onChange={(e) => setFormEmail(e.target.value)}
                        />

                        <FormControl fullWidth>
                            <InputLabel id="sectors-label">Sectors</InputLabel>
                            <Select
                                labelId="sectors-label"
                                label="Sectors"
                                multiple
                                value={formSectors}
                                onChange={(e) => setFormSectors(e.target.value)}
                                MenuProps={{
                                    disablePortal: true,
                                    anchorOrigin: { vertical: "bottom", horizontal: "left" },
                                    transformOrigin: { vertical: "top", horizontal: "left" },
                                    PaperProps: {
                                        sx: {
                                            maxHeight: 200, // short so chips remain visible
                                            mt: 1,
                                        },
                                    },
                                    MenuListProps: { dense: true },
                                }}
                                renderValue={(selected) => (
                                    <Box
                                        sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}
                                        onMouseDown={(e) => {
                                            // prevent opening the select when clicking the chip's X
                                            e.stopPropagation();
                                        }}
                                    >
                                        {selected.map((value) => (
                                            <ChipMUI
                                                key={value}
                                                label={value}
                                                onDelete={(evt) => {
                                                    evt.stopPropagation();
                                                    handleDeleteSectorChipInForm(value);
                                                }}
                                                onMouseDown={(e) => {
                                                    e.stopPropagation();
                                                    e.preventDefault();
                                                }}
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
                            label="Stop Loss Tolerance"
                            type="number"
                            fullWidth
                            required
                            value={formStopLossTolerance}
                            onChange={(e) => setFormStopLossTolerance(e.target.value)}
                        />
                        <Box sx={{ px: 0, py: 1, mx: 1.5 }}>
                            <Typography variant="body1" sx={{ mb: 1, fontWeight: 500 }}>
                                Risk Threshold
                            </Typography>
                            <Slider
                                value={typeof formRiskThreshold === "number" ? formRiskThreshold : 0}
                                min={0}
                                max={4}
                                step={1}
                                // show 1dp
                                precision={1}
                                marks={[
                                    { value: 0, label: "Zero" },
                                    { value: 1, label: "Medium" },
                                    { value: 2, label: "Moderate" },
                                    { value: 3, label: "High" },
                                    { value: 4, label: "Very High" },
                                ]}
                                valueLabelDisplay="auto"
                                valueLabelFormat={(value) => RISK_LABELS[value] || value}
                                onChange={(_, val) => setFormRiskThreshold(Number(val))}
                                sx={{ mx: 1, width: "calc(100% - 20px)" }}
                            />
                        </Box>

                        {/* Hidden submit to allow Enter key save */}
                        <button type="submit" style={{ display: "none" }} />
                    </Box>
                </DialogContent>
                <DialogActions sx={{ px: 3, py: 2 }}>
                    <Button onClick={handleCloseEdit} variant="text">
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSaveEdit}
                        variant="contained"
                        color="black"
                        sx={{ "&:hover": { bgcolor: "#6b6b6bff" } }}
                    >
                        Save
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ClientRecc;
