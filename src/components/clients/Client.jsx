import React, { useEffect, useState } from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../routes";
import { getData } from "../../services/api";

import { getData } from "../../services/api";

const Client = ({ client }) => {
  const navigate = useNavigate();
  const handleOpen = () => {
    const id = client.id ?? client.username;
    navigate(`${ROUTES.RM_CLIENT}/${encodeURIComponent(id)}`);
  };

  const name =
    client.name ?? `${client.first_name ?? "NA"} ${client.last_name ?? "NA"}`;
  const email = client.email ?? "NA";

  const [preferences, setPreferences] = useState(null);
  const [loadingPrefs, setLoadingPrefs] = useState(true);

  useEffect(() => {
    if (!client.id) return;
    setLoadingPrefs(true);

    getData(`/user/${client.id}/preferences`)
      .then((data) => {
        if (data?.data) {
          setPreferences(data.data);
        } else {
          throw new Error("No data returned");
        }
        setLoadingPrefs(false);
      })
      .catch(() => {
        // fallback object with NA values
        setPreferences({
          holding: "NA",
          overall_pl: "NA",
          risk_cap: "NA",
          stop_loss_tolerance: "NA",
          sectors: "NA",
        });
        setLoadingPrefs(false);
      });
  }, [client.id]);

  const prefs = preferences || {
    holding: "NA",
    overall_pl: "NA",
    risk_cap: "NA",
    stop_loss_tolerance: "NA",
    sectors: "NA",
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

        {loadingPrefs ? (
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 0.5 }}>
            Loading preferences…
          </Typography>
        ) : (
          <>
            <Typography
              variant="body2"
              sx={{ color: "text.secondary", mb: 0.5 }}
            >
              Current holdings: {typeof prefs.holding === 'number' ? `$${prefs.holding.toLocaleString()}` : "NA"}
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: "text.secondary", mb: 0.5 }}
            >
              Overall P/L: {typeof prefs.overall_pl === 'number' ? `$${prefs.overall_pl.toLocaleString()}` : "NA"}
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: "text.secondary", mb: 0.5 }}
            >
              Risk Cap: {prefs.risk_cap ?? "NA"}
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: "text.secondary", mb: 0.5 }}
            >
              Stop Loss Tolerance: {typeof prefs.stop_loss_tolerance === 'number' ? `${prefs.stop_loss_tolerance}%` : "NA"}
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              Sectors:{" "}
              {Array.isArray(prefs.sectors) ? prefs.sectors.join(", ") : "NA"}
            </Typography>
          </>
        )}

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
