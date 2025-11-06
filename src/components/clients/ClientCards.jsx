import React from "react";
import { apiClient } from "../../services/api";
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
    Alert,
    FormHelperText,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import Client from "./Client";
import useFetch from "../../hooks/useFetch";
import { useForm, Controller } from "react-hook-form";

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
    if (typeof val !== "number") return "Moderate";
    return RISK_LABELS[val] ?? "Moderate";
}

// Risk profile templates with smart defaults
const RISK_PROFILE_TEMPLATES = {
    0: { // Zero
        maxSinglePosition: 5,
        maxSectorAllocation: 20,
        minCashReserve: 25,
        stopLossTolerance: -5,
        description: "Zero risk approach with minimal exposure and high cash reserves"
    },
    1: { // Medium
        maxSinglePosition: 10,
        maxSectorAllocation: 30,
        minCashReserve: 15,
        stopLossTolerance: -7,
        description: "Medium risk with modest position sizes"
    },
    2: { // Moderate
        maxSinglePosition: 15,
        maxSectorAllocation: 40,
        minCashReserve: 10,
        stopLossTolerance: -10,
        description: "Balanced approach suitable for most clients"
    },
    3: { // High
        maxSinglePosition: 20,
        maxSectorAllocation: 50,
        minCashReserve: 5,
        stopLossTolerance: -12,
        description: "Higher risk tolerance with larger positions"
    },
    4: { // Very High
        maxSinglePosition: 25,
        maxSectorAllocation: 60,
        minCashReserve: 2,
        stopLossTolerance: -15,
        description: "Very high risk tolerance for aggressive growth"
    }
};

function normalize(u) {
    const sectors = Array.isArray(u?.sectors) && u.sectors.length > 0 ? u.sectors : ["NA"];
    return {
        id: u?.id ?? "NA",
        name: (u?.first_name && u?.last_name) ? `${u.first_name} ${u.last_name}` : "NA",
        email: u?.email ?? "NA",
        username: u?.username ?? "NA",
        holding: u?.holding ?? "NA",
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
    const [submitError, setSubmitError] = React.useState("");

    // React Hook Form setup
    const {
        control,
        handleSubmit,
        reset,
        setValue,
        formState: { errors, isSubmitting },
        watch,
    } = useForm({
        defaultValues: {
            firstName: "",
            lastName: "",
            email: "",
            sectors: [],
            stopLossTolerance: -10,
            riskThreshold: 2, // Default to "Moderate"
            maxSinglePosition: 15,
            maxSectorAllocation: 40,
            minCashReserve: 10,
        },
    });

    const watchRiskThreshold = watch("riskThreshold");

    // Apply risk profile template when risk threshold changes
    React.useEffect(() => {
        if (watchRiskThreshold !== undefined && RISK_PROFILE_TEMPLATES[watchRiskThreshold]) {
            const template = RISK_PROFILE_TEMPLATES[watchRiskThreshold];
            setValue("maxSinglePosition", template.maxSinglePosition);
            setValue("maxSectorAllocation", template.maxSectorAllocation);
            setValue("minCashReserve", template.minCashReserve);
            setValue("stopLossTolerance", template.stopLossTolerance);
        }
    }, [watchRiskThreshold, setValue]);

    const handleOpenAdd = () => {
        setOpenAdd(true);
        setSubmitError("");
    };

    const handleCloseAdd = () => {
        setOpenAdd(false);
        setSubmitError("");
        reset(); // Resets all form fields to defaultValues
    };

    const handleSubmitAdd = async (data) => {
        setSubmitError("");

        const payload = {
            id: crypto.randomUUID(),
            username: data.firstName.trim().toLowerCase() + "." + data.lastName.trim().toLowerCase() + Math.floor(Math.random() * 1000),
            first_name: data.firstName.trim(),
            last_name: data.lastName.trim(),
            email: data.email.trim(),
            risk_cap: riskValueToLabel(data.riskThreshold),
            sectors: data.sectors,
            stop_loss_tolerance: data.stopLossTolerance,
            max_single_position_percent: data.maxSinglePosition,
            max_sector_allocation_percent: data.maxSectorAllocation,
            min_cash_reserve_percent: data.minCashReserve,
            role: "CLIENT",
            rm_id: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        };

        try {
            const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";
            const res = await fetch(`${API_BASE_URL}/api/user/create-clients`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.message || "Failed to add client");
            }

            const result = await res.json();
            const newClient = normalize(result.data);


            setClients((prev) => [newClient, ...prev]);
            setPage(1);
            handleCloseAdd();
        } catch (err) {
            setSubmitError(err.message);
        }
    };


    return (
        <Box
            sx={{
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
                sx={{
                    zIndex: (theme) => theme.zIndex.modal + 2,
                    '& .MuiDialog-container': {
                        alignItems: 'center',
                        justifyContent: 'center',
                    },
                }}
                PaperProps={{
                    sx: {
                        borderRadius: 3,
                        bgcolor: "white",
                        width: "100%",
                        maxWidth: 600,
                        m: 2,
                    },
                }}
            >
                <DialogTitle sx={{ fontWeight: 700 }}>Add New Client</DialogTitle>
                <DialogContent dividers>
                    {submitError && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {submitError}
                        </Alert>
                    )}
                    <Box component="form" onSubmit={handleSubmit(handleSubmitAdd)} sx={{ mt: 1.5, display: "grid", gap: 2 }}>
                        {/* Basic Information */}
                        <Typography variant="h6" sx={{ fontWeight: 600, mt: 1 }}>
                            Basic Information
                        </Typography>

                        <Controller
                            name="firstName"
                            control={control}
                            rules={{
                                required: "First name is required",
                                minLength: { value: 2, message: "First name must be at least 2 characters" }
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="First Name"
                                    fullWidth
                                    error={!!errors.firstName}
                                    helperText={errors.firstName?.message}
                                />
                            )}
                        />

                        <Controller
                            name="lastName"
                            control={control}
                            rules={{
                                required: "Last name is required",
                                minLength: { value: 2, message: "Last name must be at least 2 characters" }
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="Last Name"
                                    fullWidth
                                    error={!!errors.lastName}
                                    helperText={errors.lastName?.message}
                                />
                            )}
                        />

                        <Controller
                            name="email"
                            control={control}
                            rules={{
                                required: "Email is required",
                                pattern: {
                                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                    message: "Invalid email address"
                                }
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="Email"
                                    type="email"
                                    fullWidth
                                    error={!!errors.email}
                                    helperText={errors.email?.message}
                                />
                            )}
                        />

                        {/* Investment Preferences */}
                        <Typography variant="h6" sx={{ fontWeight: 600, mt: 2 }}>
                            Investment Preferences
                        </Typography>

                        <Controller
                            name="sectors"
                            control={control}
                            render={({ field }) => (
                                <FormControl fullWidth>
                                    <InputLabel id="sectors-label">Preferred Sectors</InputLabel>
                                    <Select
                                        {...field}
                                        labelId="sectors-label"
                                        label="Preferred Sectors"
                                        multiple
                                        MenuProps={{
                                            disablePortal: true,
                                            anchorOrigin: { vertical: "bottom", horizontal: "left" },
                                            transformOrigin: { vertical: "top", horizontal: "left" },
                                            PaperProps: { sx: { maxHeight: 200, mt: 1 } },
                                            MenuListProps: { dense: true },
                                        }}
                                        renderValue={(selected) => (
                                            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                                                {selected.map((value) => (
                                                    <Chip
                                                        key={value}
                                                        label={value}
                                                        onDelete={() => {
                                                            field.onChange(field.value.filter(s => s !== value));
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
                                    <FormHelperText>Select sectors the client is interested in</FormHelperText>
                                </FormControl>
                            )}
                        />

                        {/* Risk Management */}
                        <Typography variant="h6" sx={{ fontWeight: 600, mt: 2 }}>
                            Risk Management
                        </Typography>

                        <Controller
                            name="riskThreshold"
                            control={control}
                            render={({ field }) => (
                                <Box sx={{ px: 2, py: 1 }}>
                                    <Typography variant="body1" sx={{ mb: 1, fontWeight: 500 }}>
                                        Risk Profile: {RISK_LABELS[watchRiskThreshold]}
                                    </Typography>
                                    {RISK_PROFILE_TEMPLATES[watchRiskThreshold] && (
                                        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary', fontStyle: 'italic' }}>
                                            {RISK_PROFILE_TEMPLATES[watchRiskThreshold].description}
                                        </Typography>
                                    )}
                                    <Slider
                                        {...field}
                                        min={0}
                                        max={4}
                                        step={1}
                                        marks={[
                                            { value: 0, label: "Conservative" },
                                            { value: 1, label: "Low" },
                                            { value: 2, label: "Moderate" },
                                            { value: 3, label: "High" },
                                            { value: 4, label: "Aggressive" },
                                        ]}
                                        valueLabelDisplay="auto"
                                        valueLabelFormat={(value) => RISK_LABELS[value] || value}
                                        sx={{ mx: 1, width: "calc(100% - 20px)" }}
                                    />
                                    <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'primary.main' }}>
                                        Changing risk profile will auto-populate position limits below
                                    </Typography>
                                </Box>
                            )}
                        />

                        <Controller
                            name="stopLossTolerance"
                            control={control}
                            rules={{
                                required: "Stop loss tolerance is required",
                                min: { value: -50, message: "Stop loss cannot be less than -50%" },
                                max: { value: 0, message: "Stop loss tolerance should be negative or zero" }
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="Stop Loss Tolerance (%)"
                                    type="number"
                                    fullWidth
                                    error={!!errors.stopLossTolerance}
                                    helperText={errors.stopLossTolerance?.message || "Maximum loss percentage before selling (e.g., -10 for 10% loss)"}
                                    inputProps={{ step: 0.1 }}
                                />
                            )}
                        />

                        {/* Position Limits */}
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, mb: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                Position Limits
                            </Typography>
                            <Box
                                sx={{
                                    ml: 1,
                                    px: 1,
                                    py: 0.5,
                                    bgcolor: 'primary.main',
                                    color: 'white',
                                    borderRadius: 1,
                                    fontSize: '0.75rem',
                                    fontWeight: 500
                                }}
                            >
                                Auto-filled from {RISK_LABELS[watchRiskThreshold]} template
                            </Box>
                        </Box>
                        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                            These values are automatically set based on your selected risk profile. You can still modify them if needed.
                        </Typography>

                        <Controller
                            name="maxSinglePosition"
                            control={control}
                            rules={{
                                required: "Maximum single position is required",
                                min: { value: 1, message: "Must be at least 1%" },
                                max: { value: 50, message: "Cannot exceed 50%" }
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="Maximum Single Position (%)"
                                    type="number"
                                    fullWidth
                                    error={!!errors.maxSinglePosition}
                                    helperText={errors.maxSinglePosition?.message || "Maximum percentage of portfolio in any single stock"}
                                    inputProps={{ step: 0.1, min: 1, max: 50 }}
                                />
                            )}
                        />

                        <Controller
                            name="maxSectorAllocation"
                            control={control}
                            rules={{
                                required: "Maximum sector allocation is required",
                                min: { value: 5, message: "Must be at least 5%" },
                                max: { value: 100, message: "Cannot exceed 100%" }
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="Maximum Sector Allocation (%)"
                                    type="number"
                                    fullWidth
                                    error={!!errors.maxSectorAllocation}
                                    helperText={errors.maxSectorAllocation?.message || "Maximum percentage of portfolio in any single sector"}
                                    inputProps={{ step: 0.1, min: 5, max: 100 }}
                                />
                            )}
                        />

                        <Controller
                            name="minCashReserve"
                            control={control}
                            rules={{
                                required: "Minimum cash reserve is required",
                                min: { value: 0, message: "Cannot be negative" },
                                max: { value: 50, message: "Cannot exceed 50%" }
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="Minimum Cash Reserve (%)"
                                    type="number"
                                    fullWidth
                                    error={!!errors.minCashReserve}
                                    helperText={errors.minCashReserve?.message || "Minimum percentage of portfolio to keep as cash"}
                                    inputProps={{ step: 0.1, min: 0, max: 50 }}
                                />
                            )}
                        />
                    </Box>
                </DialogContent>
                <DialogActions sx={{ px: 3, py: 2 }}>
                    <Button onClick={handleCloseAdd} variant="text" disabled={isSubmitting}>
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        onClick={handleSubmit(handleSubmitAdd)}
                        variant="contained"
                        color="black"
                        disabled={isSubmitting}
                        sx={{ "&:hover": { bgcolor: "#6b6b6bff" } }}
                    >
                        {isSubmitting ? "Creating..." : "Create Client"}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ClientCards;
