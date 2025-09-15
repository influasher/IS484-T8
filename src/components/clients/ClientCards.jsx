import React from "react";
import {
    Box,
    Paper,
    Grid,
    Typography,
    IconButton,
    Tooltip,
    Pagination,
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
    Chip,
    Slider,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import Client from "./Client";
import useFetch from "../../hooks/useFetch";

// ---------- constants ----------
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

const CARD_WIDTH = 320;
const GRID_GAP_SPACING = 2.5;
const PX_PER_SPACING_UNIT = 8;
const GAP_PX = GRID_GAP_SPACING * PX_PER_SPACING_UNIT;
const ROWS_PER_PAGE = 2;

// --------------------------------

const RISK_LABELS = ["Zero", "Medium", "Moderate", "High", "Very High"];
function riskValueToLabel(val) {
    if (typeof val !== "number") return "Zero";
    return RISK_LABELS[val] ?? "Zero";
}

function normalize(u) {
    const sectors = Array.isArray(u?.sectors) && u.sectors.length > 0 ? u.sectors : ["NA"];
    return {
        id: u?.id ?? "NA",
        name: (u?.first_name && u?.last_name) ? `${u.first_name} ${u.last_name}` : "NA",
        email: u?.email ?? "NA",
        username: u?.username ?? "NA",
        holdings: u?.holdings ?? "NA",
        overall_pl: u?.overall_pl ?? "NA",
        risk_cap: u?.risk_cap ?? "NA",
        sectors,
    };
}

function useClients() {
    // fetch all clients
    const { data, loading, status } = useFetch("/user/clients");

    const list = Array.isArray(data) ? data : Array.isArray(data?.data) ? data.data : [];
    const clients = React.useMemo(() => list.map(normalize), [list]);

    return { clients, loading, status };
}

const ClientCards = () => {
    const { clients: fetchedClients, loading, status } = useClients();

    const [clients, setClients] = React.useState([]);

    React.useEffect(() => {
        if (
            clients.length !== fetchedClients.length ||
            (clients[0]?.id !== fetchedClients[0]?.id) ||
            (clients[clients.length - 1]?.id !== fetchedClients[fetchedClients.length - 1]?.id)
        ) {
            setClients(fetchedClients);
        }
    }, [fetchedClients]);

    const [page, setPage] = React.useState(1);
    const gridRef = React.useRef(null);
    const [containerWidth, setContainerWidth] = React.useState(0);
    const [itemsPerPage, setItemsPerPage] = React.useState(ROWS_PER_PAGE);

    // Resize observer to compute columns
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

    // Add-Client modal state
    const [openAdd, setOpenAdd] = React.useState(false);
    const [formFirstName, setFormFirstName] = React.useState("");
    const [formLastName, setFormLastName] = React.useState("");
    // const [formUsername, setFormUsername] = React.useState("");
    const [formStopLossTolerance, setFormStopLossTolerance] = React.useState(0);
    const [formEmail, setFormEmail] = React.useState("");
    const [formRiskThreshold, setFormRiskThreshold] = React.useState("");
    const [formSectors, setFormSectors] = React.useState([]);

    const handleOpenAdd = () => setOpenAdd(true);
    const handleCloseAdd = () => {
        setOpenAdd(false);
        setFormFirstName("");
        setFormLastName("");
        // setFormUsername("");
        setFormStopLossTolerance(0);
        setFormEmail("");
        setFormRiskThreshold(0);
        setFormSectors([]);
    };

    const handleSubmitAdd = async (e) => {
        e.preventDefault();

        const payload = {
            // generate random id
            id: crypto.randomUUID(),
            // username: formUsername.trim(),
            // for now auto generate the username
            username: formFirstName.trim().toLowerCase() + "." + formLastName.trim().toLowerCase() + Math.floor(Math.random() * 1000),
            first_name: formFirstName.trim(),
            last_name: formLastName.trim(),
            email: formEmail.trim(),
            // risk_cap: riskValueToLabel(formRiskThreshold),
            // sectors: formSectors,
            // stop_loss_tolerance: formStopLossTolerance === "yes"? true : false,
            role: "client",
            rm_id: null,
            created_at: new Date().toISOString(),
        };

        try {
            const res = await fetch("/user/create-clients", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) throw new Error("Failed to add client");

            const result = await res.json();
            // Optionally, normalize result.data if needed
            const newClient = normalize(result.data);

            setClients((prev) => [newClient, ...prev]);
            setPage(1);
            handleCloseAdd();
        } catch (err) {
            alert("Error adding client: " + err.message);
        }
    };

    const handleDeleteSector = (sector) => {
        setFormSectors((prev) => prev.filter((s) => s !== sector));
    };

    return (
        <Box
            sx={{
                minHeight: "100vh",
                bgcolor: (t) => t.palette.grey[100],
                px: { xs: 3, sm: 5, md: 7 },
                py: { xs: 1.5, sm: 2.5, md: 3 },
            }}
        >
            <Paper
                elevation={1}
                sx={{
                    position: "relative",
                    zIndex: (t) => t.zIndex.drawer + 1,
                    mx: "auto",
                    px: { xs: 3, sm: 5, md: 7 },
                    py: { xs: 2, sm: 3 },
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

                {loading && (
                    <Typography variant="body2" sx={{ mb: 2 }}>
                        Loading clients…
                    </Typography>
                )}
                {status && (status !== 200) && !loading && (
                    <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                        Failed to load clients: {status}
                    </Typography>
                )}

                <Grid container spacing={GRID_GAP_SPACING} ref={gridRef}>
                    {current.map((c) => (
                        <Grid key={`${c.id}-${c.username}-${c.email}`} item>
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
                        {/* <TextField
                            label="Username"
                            type="text"
                            fullWidth
                            required
                            value={formUsername}
                            onChange={(e) => setFormUsername(e.target.value)}
                        /> */}
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
                                    PaperProps: { sx: { maxHeight: 200, mt: 1 } },
                                    MenuListProps: { dense: true },
                                }}
                                renderValue={(selected) => (
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
                                                    evt.stopPropagation();
                                                    handleDeleteSector(value);
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
                            defaultValue={0}
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
