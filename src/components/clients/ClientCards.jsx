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
import useFetch from "../../hooks/useFetch";

function normalize(u) {
    const sectors = Array.isArray(u?.sectors) && u.sectors.length > 0 ? u.sectors : ["NA"];
    return {
        id: u?.id ?? "NA",
        name: u?.username ?? "NA", // map backend username -> UI name for now
        email: u?.email ?? "NA",
        username: u?.username ?? "NA",
        holdings: u?.holdings ?? "NA",
        overallPL: u?.overallPL ?? "NA",
        risk: u?.risk ?? "NA",
        cap: u?.cap ?? "NA",
        sectors,
    };
}

function useClients() {
    const { data, loading, error } = useFetch("/user/clients");

    const list = Array.isArray(data) ? data : Array.isArray(data?.data) ? data.data : [];
    const clients = React.useMemo(() => list.map(normalize), [list]);

    return { clients, loading, error };
}

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

const ClientCards = () => {
    const { clients: fetchedClients, loading, error } = useClients();

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
        const nextId =
            clients.reduce((max, c) => Math.max(max, Number(c.id) || 0), 0) + 1;

        const newClient = {
            id: nextId,
            name: formName.trim() || "NA",
            email: formEmail.trim() || "NA",
            username:
                formName.trim()
                    ? `${formName.trim().toLowerCase().replace(/\s+/g, "")}_client_${nextId}`
                    : "NA",
            holdings: "NA",
            overallPL: "NA",
            risk: formRiskThreshold ? `Threshold ${formRiskThreshold}%` : "NA",
            cap: "NA",
            sectors: formSectors.length ? formSectors : ["NA"],
        };

        setClients((prev) => [newClient, ...prev]);
        setPage(1);
        handleCloseAdd();
    };

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

                {loading && (
                    <Typography variant="body2" sx={{ mb: 2 }}>
                        Loading clients…
                    </Typography>
                )}
                {error && (
                    <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                        {String(error)}
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
