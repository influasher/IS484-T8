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
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import ChipMUI from "@mui/material/Chip";

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

const MOCK_CLIENTS = [
    {
        id: 1,
        name: "Michael Chen",
        email: "michael.chen@email.com",
        riskRating: 10,
        sectors: ["Information Technology", "Financials"],
    },
    {
        id: 2,
        name: "Emma Wilson",
        email: "emma.wilson@email.com",
        riskRating: 6,
        sectors: ["Health Care", "Consumer Staples"],
    },
];

function getClientById(id) {
    const n = Number(id);
    return (
        MOCK_CLIENTS.find((c) => c.id === n) || {
            id,
            name: `Client #${id}`,
            email: `client${id}@email.com`,
            riskRating: 5,
            sectors: ["Information Technology"],
        }
    );
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
    const initial = React.useMemo(() => getClientById(routeId), [routeId]);

    // Display state (what the page shows)
    const [dispName, setDispName] = React.useState(initial.name);
    const [dispEmail, setDispEmail] = React.useState(initial.email);
    const [dispRisk, setDispRisk] = React.useState(initial.riskRating);
    const [dispSectors, setDispSectors] = React.useState(initial.sectors || []);

    // Editor modal state (pre-filled form values)
    const [openEdit, setOpenEdit] = React.useState(false);
    const [formName, setFormName] = React.useState(dispName);
    const [formEmail, setFormEmail] = React.useState(dispEmail);
    const [formRisk, setFormRisk] = React.useState(String(dispRisk));
    const [formSectors, setFormSectors] = React.useState(dispSectors);

    const handleOpenEdit = () => {
        // preload form with current display values
        setFormName(dispName);
        setFormEmail(dispEmail);
        setFormRisk(String(dispRisk));
        setFormSectors(dispSectors);
        setOpenEdit(true);
    };

    const handleCloseEdit = () => {
        setOpenEdit(false);
    };

    const handleSaveEdit = (e) => {
        if (e) e.preventDefault();
        // apply form values back to display state
        setDispName(formName.trim());
        setDispEmail(formEmail.trim());
        setDispRisk(Number(formRisk) || 0);
        setDispSectors(formSectors);
        setOpenEdit(false);
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
                            label="Name"
                            type="text"
                            fullWidth
                            required
                            value={formName}
                            onChange={(e) => setFormName(e.target.value)}
                        />

                        <TextField
                            label="Email"
                            type="email"
                            fullWidth
                            required
                            value={formEmail}
                            onChange={(e) => setFormEmail(e.target.value)}
                        />

                        <TextField
                            label="Risk Threshold (%)"
                            type="number"
                            fullWidth
                            inputProps={{ min: 0, step: 1 }}
                            value={formRisk}
                            onChange={(e) => setFormRisk(e.target.value)}
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
