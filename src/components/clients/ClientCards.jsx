import React from "react";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import Pagination from "@mui/material/Pagination";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Chip from "@mui/material/Chip";
import Client from "./Client";

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

const initialClients = [
    { id: 1, name: "Michael Chen", email: "michael.chen@email.com", username: "mchen_client", holdings: "$124,500", overallPL: "$124,500", risk: "Moderate", cap: "Large-cap", sectors: ["Information Technology", "Financials"] },
    { id: 2, name: "Emma Wilson", email: "emma.wilson@email.com", username: "ewilson_client", holdings: "$86,300", overallPL: "$84,900", risk: "Conservative", cap: "Large-cap", sectors: ["Health Care", "Consumer Staples"] },
    { id: 3, name: "David Rodriguez", email: "david.rodriguez@email.com", username: "drodriguez_client", holdings: "$210,050", overallPL: "$212,300", risk: "Aggressive", cap: "Mid-cap", sectors: ["Industrials", "Materials"] },
    { id: 4, name: "Lisa Thompson", email: "lisa.thompson@email.com", username: "lthompson_client", holdings: "$58,900", overallPL: "$58,900", risk: "Moderate", cap: "Small-cap", sectors: ["Communication Services", "Consumer Discretionary"] },
    { id: 5, name: "James Anderson", email: "james.anderson@email.com", username: "janderson_client", holdings: "$142,780", overallPL: "$140,200", risk: "Conservative", cap: "Large-cap", sectors: ["Utilities", "Energy"] },
    { id: 6, name: "Jennifer Martinez", email: "jennifer.martinez@email.com", username: "jmartinez_client", holdings: "$97,220", overallPL: "$97,220", risk: "Moderate", cap: "Mid-cap", sectors: ["Real Estate", "Financials"] },
    { id: 7, name: "Robert Taylor", email: "robert.taylor@email.com", username: "rtaylor_client", holdings: "$75,340", overallPL: "$76,000", risk: "Conservative", cap: "Large-cap", sectors: ["Information Technology"] },
    { id: 8, name: "Ashley Davis", email: "ashley.davis@email.com", username: "adavis_client", holdings: "$183,990", overallPL: "$183,990", risk: "Aggressive", cap: "Mid-cap", sectors: ["Health Care", "Industrials"] },
    { id: 9, name: "Christopher Brown", email: "christopher.brown@email.com", username: "cbrown_client", holdings: "$134,610", overallPL: "$132,400", risk: "Moderate", cap: "Large-cap", sectors: ["Materials", "Energy"] },
    { id: 10, name: "Amanda Garcia", email: "amanda.garcia@email.com", username: "agarcia_client", holdings: "$62,430", overallPL: "$62,430", risk: "Moderate", cap: "Small-cap", sectors: ["Consumer Discretionary"] },
    { id: 11, name: "Daniel Miller", email: "daniel.miller@email.com", username: "dmiller_client", holdings: "$155,275", overallPL: "$156,000", risk: "Conservative", cap: "Large-cap", sectors: ["Financials", "Real Estate"] },
    { id: 12, name: "Michelle Lee", email: "michelle.lee@email.com", username: "mlee_client", holdings: "$121,880", overallPL: "$121,880", risk: "Aggressive", cap: "Mid-cap", sectors: ["Information Technology", "Communication Services"] },
];

// === Auto dynamic pagination config ===
const CARD_WIDTH = 320;    
const GRID_GAP_SPACING = 2.5;  
const PX_PER_SPACING_UNIT = 8;    
const GAP_PX = GRID_GAP_SPACING * PX_PER_SPACING_UNIT; 
const ROWS_PER_PAGE = 2;       

const ClientCards = () => {
    const [clients, setClients] = React.useState(initialClients);
    const [page, setPage] = React.useState(1);

    const gridRef = React.useRef(null);
    const [containerWidth, setContainerWidth] = React.useState(0);
    const [itemsPerPage, setItemsPerPage] = React.useState(ROWS_PER_PAGE); 

    React.useEffect(() => {
        if (!gridRef.current) return;

        const ro = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const w =
                    entry.contentBoxSize && entry.contentBoxSize[0]
                        ? entry.contentBoxSize[0].inlineSize
                        : entry.contentRect.width;
                setContainerWidth(w);
            }
        });
        ro.observe(gridRef.current);

        setContainerWidth(gridRef.current.getBoundingClientRect().width);

        return () => ro.disconnect();
    }, []);

    React.useEffect(() => {
        if (!containerWidth) return;

        const columns = Math.max(
            1,
            Math.floor((containerWidth + GAP_PX) / (CARD_WIDTH + GAP_PX))
        );

        const nextItemsPerPage = columns * ROWS_PER_PAGE;
        setItemsPerPage(nextItemsPerPage);

        const newPageCount = Math.max(1, Math.ceil(clients.length / nextItemsPerPage));
        setPage((prev) => Math.min(prev, newPageCount));
    }, [containerWidth, clients.length]);

    const pageCount = Math.max(1, Math.ceil(clients.length / itemsPerPage));
    const start = (page - 1) * itemsPerPage;
    const current = clients.slice(start, start + itemsPerPage);

    const [openAdd, setOpenAdd] = React.useState(false);
    const [formName, setFormName] = React.useState("");
    const [formEmail, setFormEmail] = React.useState("");
    const [formRiskThreshold, setFormRiskThreshold] = React.useState("");
    const [formSectors, setFormSectors] = React.useState([]);

    const handleOpenAdd = () => setOpenAdd(true);
    const handleCloseAdd = () => {
        setOpenAdd(false);
        setFormName("");
        setFormEmail("");
        setFormRiskThreshold("");
        setFormSectors([]);
    };

    const handleSubmitAdd = (e) => {
        e.preventDefault();
        const nextId = clients.reduce((max, c) => Math.max(max, c.id), 0) + 1;

        const newClient = {
            id: nextId,
            name: formName.trim(),
            email: formEmail.trim(),
            username: `${formName.trim().toLowerCase().replace(/\s+/g, "")}_client_${nextId}`,
            holdings: "$0.00",
            overallPL: "$0.00",
            risk: `Threshold ${formRiskThreshold || 0}%`,
            cap: "—",
            sectors: formSectors,
        };

        setClients((prev) => [newClient, ...prev]);
        setPage(1);
        handleCloseAdd();
    };

    // delete a single sector chip
    const handleDeleteSector = (sector) => {
        setFormSectors((prev) => prev.filter((s) => s !== sector));
    };

    return (
        <Box
            sx={{
                minHeight: "100vh",
                bgcolor: (t) => t.palette.grey[100],
                p: { xs: 1.5, sm: 2.5, md: 3 },
            }}
        >
            <Paper
                elevation={1}
                sx={{
                    position: "relative",
                    zIndex: (t) => t.zIndex.drawer + 1,
                    mx: "auto",
                    p: { xs: 2, sm: 3 },
                    borderRadius: 3,
                }}
            >
                <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <Typography variant="h5" sx={{ fontWeight: 700, mr: 1 }}>
                        Clients
                    </Typography>

                    <Box sx={{ ml: "auto" }}>
                        <Tooltip title="Add new client">
                            <IconButton aria-label="Add client" size="medium" onClick={handleOpenAdd}>
                                <AddRoundedIcon fontSize="inherit" sx={{ color: "black" }} />
                            </IconButton>
                        </Tooltip>
                    </Box>
                </Box>

                {/* Grid container observed for width */}
                <Grid container spacing={GRID_GAP_SPACING} ref={gridRef}>
                    {current.map((c) => (
                        <Grid key={c.id} item>
                            {/* Each Client card is fixed at 320px width internally */}
                            <Client client={c} />
                        </Grid>
                    ))}
                </Grid>

                <Box sx={{ display: "flex", justifyContent: "center", mt: 3 }}>
                    <Pagination
                        count={pageCount}
                        page={page}
                        onChange={(_, p) => setPage(p)}
                        shape="rounded"
                        siblingCount={1}
                        boundaryCount={1}
                        sx={{
                            "& .MuiPaginationItem-root.Mui-selected": {
                                backgroundColor: "#212121",
                                color: "#fff",
                            },
                        }}
                    />
                </Box>
            </Paper>

            {/* Add New Client Dialog */}
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
                <DialogTitle sx={{ fontWeight: 700 }}>Add New Client</DialogTitle>
                <DialogContent dividers>
                    <Box component="form" onSubmit={handleSubmitAdd} sx={{ mt: 1.5, display: "grid", gap: 2 }}>
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
                            value={formRiskThreshold}
                            onChange={(e) => setFormRiskThreshold(e.target.value)}
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
                                            maxHeight: 200,
                                            mt: 1,
                                        },
                                    },
                                    MenuListProps: { dense: true },
                                }}
                                renderValue={(selected) => (
                                    // Stop mouse down so clicking chip X doesn't open the menu
                                    <Box
                                        sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}
                                        onMouseDown={(e) => {
                                            e.stopPropagation();
                                        }}
                                    >
                                        {selected.map((value) => (
                                            <Chip
                                                key={value}
                                                label={value}
                                                onDelete={(evt) => {
                                                    evt.stopPropagation(); // prevent Select from toggling
                                                    handleDeleteSector(value);
                                                }}
                                                // also prevent opening when interacting with the chip area
                                                onMouseDown={(e) => {
                                                    e.stopPropagation();
                                                    // prevent focus/activation that might toggle
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
                    </Box>
                </DialogContent>
                <DialogActions sx={{ px: 3, py: 2 }}>
                    <Button onClick={handleCloseAdd} variant="text">
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmitAdd}
                        variant="contained"
                        color="black"
                        sx={{ "&:hover": { bgcolor: "#6b6b6bff" } }}
                    >
                        Submit
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ClientCards;
