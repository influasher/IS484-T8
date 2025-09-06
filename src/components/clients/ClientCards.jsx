import React, { useMemo, useCallback } from "react";
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
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import ClearRoundedIcon from "@mui/icons-material/ClearRounded";
import Client from "./Client";
import useFetch from "../../hooks/useFetch";
import useDebounce from "../../hooks/useDebounce";
import Searchbar from "../ui/Searchbar";

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
        // Add full name and search-friendly fields
        full_name: `${u?.first_name || ''} ${u?.last_name || ''}`.trim() || u?.username || "NA",
        first_name: u?.first_name ?? "",
        last_name: u?.last_name ?? "",
    };
}

function useClients(searchTerm = "", page = 1, perPage = 20) {
    // Include pagination parameters in the URL
    const url = React.useMemo(() => {
        const params = new URLSearchParams({
            role: 'client',
            page: page.toString(),
            per_page: perPage.toString()
        });
        
        if (searchTerm.trim()) {
            params.set('q', searchTerm.trim());
        }
        
        return `/users/search?${params.toString()}`;
    }, [searchTerm, page, perPage]);
    
    const { data, loading, error } = useFetch(url);

    // The API returns data in structure: { data: { users: [...], pagination: {...} } }
    const usersList = data?.data?.users || [];
    const pagination = data?.data?.pagination || {};
    const clients = React.useMemo(() => usersList.map(normalize), [usersList]);

    return { clients, pagination, loading, error };
}

// Remove the searchClients function since we're using the backend search via URL
// The search will be handled by the useFetch hook with the search parameter

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
    // Search state - using proper debouncing with custom hook
    const [inputValue, setInputValue] = React.useState("");
    const [currentPage, setCurrentPage] = React.useState(1);
    
    // Debounce the search input
    const debouncedSearchTerm = useDebounce(inputValue, 150); // 150ms debounce for faster response
    
    const clientsPerPage = 20; // Server-side pagination
    
    // Use server-side pagination with the debounced search term
    const { 
        clients, 
        pagination, 
        loading: fetchLoading, 
        error: fetchError 
    } = useClients(debouncedSearchTerm, currentPage, clientsPerPage);

    // Reset to first page when search term changes
    React.useEffect(() => {
        if (debouncedSearchTerm !== inputValue) {
            setCurrentPage(1);
        }
    }, [debouncedSearchTerm, inputValue]);

    // Handle input change - this updates immediately for UI responsiveness
    const handleSearchChange = useCallback((term) => {
        setInputValue(term);
    }, []);

    // Server-side pagination handler
    const handlePageChange = (event, page) => {
        setCurrentPage(page);
        window.scrollTo({ top: 0, behavior: 'smooth' }); // Scroll to top on page change
    };

    // For display, we use the clients directly from the API (already paginated)
    const displayClients = clients;

    // Use server pagination info
    const pageCount = pagination.pages || 1;
    const totalClients = pagination.total || 0;

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
        // TODO: Implement API call to add new client
        // For now, just close the dialog
        handleCloseAdd();
        console.log("Add client functionality needs backend API implementation");
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
                    
                    {/* Updated search results indicator */}
                    {debouncedSearchTerm && (
                        <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                            {totalClients} total result{totalClients !== 1 ? 's' : ''} for "{debouncedSearchTerm}"
                            {totalClients > clientsPerPage && ` (showing page ${currentPage} of ${pageCount})`}
                        </Typography>
                    )}

                    <Box sx={{ ml: "auto" }}>
                        <Tooltip title="Add new client">
                            <IconButton aria-label="Add client" size="medium" onClick={handleOpenAdd}>
                                <AddRoundedIcon fontSize="inherit" sx={{ color: "black" }} />
                            </IconButton>
                        </Tooltip>
                    </Box>
                </Box>

                {/* Search Bar with debouncing */}
                <Box sx={{ mb: 3 }}>
                    <Searchbar
                        value={inputValue}
                        onChange={handleSearchChange}
                        placeholder="Search clients by name, username, or email..."
                        width="100%"
                        sx={{ width: "100%" }}
                    />
                </Box>

                {fetchLoading && (
                    <Typography variant="body2" sx={{ mb: 2 }}>
                        {debouncedSearchTerm ? 'Searching clients...' : 'Loading clients...'}
                    </Typography>
                )}

                {fetchError && (
                    <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                        {String(fetchError)}
                    </Typography>
                )}

                {/* No results message */}
                {!fetchLoading && debouncedSearchTerm && totalClients === 0 && (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Typography variant="h6" color="text.secondary">
                            No clients found
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Try adjusting your search terms
                        </Typography>
                    </Box>
                )}

                {/* Use displayClients directly (already paginated by server) */}
                <Grid container spacing={GRID_GAP_SPACING}>
                    {displayClients.map((c) => (
                        <Grid key={`${c.id}-${c.username}-${c.email}`} item>
                            <Client client={c} />
                        </Grid>
                    ))}
                </Grid>

                {/* Server-side pagination */}
                {!fetchLoading && totalClients > 0 && pageCount > 1 && (
                    <Box sx={{ display: "flex", justifyContent: "center", mt: 3 }}>
                        <Pagination
                            count={pageCount}
                            page={currentPage}
                            onChange={handlePageChange}
                            shape="rounded"
                            siblingCount={1}
                            boundaryCount={1}
                            showFirstButton
                            showLastButton
                            sx={{
                                "& .MuiPaginationItem-root.Mui-selected": {
                                    backgroundColor: "#212121",
                                    color: "#fff",
                                },
                            }}
                        />
                        
                        {/* Pagination info */}
                        <Typography 
                            variant="body2" 
                            sx={{ 
                                ml: 2, 
                                alignSelf: 'center', 
                                color: 'text.secondary' 
                            }}
                        >
                            {((currentPage - 1) * clientsPerPage) + 1}-{Math.min(currentPage * clientsPerPage, totalClients)} of {totalClients}
                        </Typography>
                    </Box>
                )}
            </Paper>

            {/* Keep your existing Add Client Dialog unchanged */}
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