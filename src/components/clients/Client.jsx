import React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../routes";


const Client = ({ client }) => {
    const navigate = useNavigate();
    const handleOpen = () => {
        const id = client.id ?? client.username;
        navigate(`${ROUTES.RM_CLIENT}/${encodeURIComponent(id)}`);
    };

    // Use normalized fields from ClientCards.jsx
    const name = client.name ?? `${client.first_name ?? "NA"} ${client.last_name ?? "NA"}`;
    const email = client.email ?? "NA";
    const holdings = client.holdings ?? "NA";
    const overall_pl = client.overall_pl ?? "NA";
    const risk_cap = client.risk_cap ?? "NA";
    const sectors = Array.isArray(client.sectors) ? client.sectors : ["NA"];

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
                    {name}
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
                    Email: {email}
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
                    Current holdings: {holdings}
                </Typography>

                {/* Overall P/L line */}
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
                    Overall P/L: {overall_pl}
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
                    Risk Cap: {risk_cap}
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
                    Sectors: {sectors.join(", ")}
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
