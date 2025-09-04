import React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";

const Client = ({ client }) => {
    const navigate = useNavigate();
    const handleOpen = () => {
        const id = client.id ?? client.username;
        navigate(`/client/${encodeURIComponent(id)}`);
    };

    return (
        <Card
            variant="outlined"
            sx={{
                width: 320,
                position: "relative",
                borderRadius: 2,
                bgcolor: (t) => t.palette.grey[100],
            }}
        >
            <CardContent sx={{ pt: 2.5, pl: 2.5 }}>
                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                        mb: 1,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    {client.name}
                </Typography>

                <Typography
                    variant="body2"
                    sx={{
                        color: "text.secondary",
                        mb: 0.5,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    Email: {client.email}
                </Typography>
                <Typography
                    variant="body2"
                    sx={{
                        color: "text.secondary",
                        mb: 0.5,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    Current holdings: {client.holdings}
                </Typography>

                {/* New Overall P/L line */}
                {client.overallPL && (
                    <Typography
                        variant="body2"
                        sx={{
                            color: "text.secondary",
                            mb: 0.5,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                        }}
                    >
                        Overall P/L: {client.overallPL}
                    </Typography>
                )}

                <Typography
                    variant="body2"
                    sx={{
                        color: "text.secondary",
                        mb: 0.5,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    Risk: {client.risk} • Cap: {client.cap}
                </Typography>
                <Typography
                    variant="body2"
                    sx={{
                        color: "text.secondary",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    Sectors: {client.sectors.join(", ")}
                </Typography>

                <Button
                    variant="contained"
                    onClick={handleOpen}
                    color="black"
                    sx={{
                        mt: 1.5, 
                        "&:hover": {
                            bgcolor: "#6b6b6bff",
                            boxShadow: "none",
                        },
                    }}
                >
                    View More Info
                </Button>
            </CardContent>
        </Card>
    );
};

export default Client;
