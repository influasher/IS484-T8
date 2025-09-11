import React from "react";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  Typography,
} from "@mui/material";

function EntityProfile({ data, loading, error }) {
  if (!data || typeof data !== "object") return <Typography>No data available</Typography>;

  console.log("Entity Profile Data:", data);
  data = data.data;

  const profiles = [
    { label: "Symbol", value: data.ticker },
    { label: "Name", value: data.name },
    { label: "Asset Type", value: data.AssetType ?? "-" },
    { label: "Description", value: data.summary ?? "-" },
    { label: "Exchange", value: data.Exchange },
    { label: "Currency", value: data.Currency },
    { label: "Sector", value: data.Sector ?? "-" },
    { label: "Industry", value: data.Industry ?? "-" },
    { label: "Official Site", value: data.OfficialSite ?? "-" },
  ];
  console.log("company profile"+profiles);

  return (
    <Box sx={{ marginBottom: 3 }}>
      <TableContainer component={Paper} elevation={0}>
        <Table size="small">
          <TableBody>
            {profiles.map((profile, i) => (
              <TableRow key={i}>
                <TableCell sx={{ fontWeight: "bold", width: "40%" }}>
                  {profile.label}
                </TableCell>
                <TableCell>{profile.value}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default EntityProfile;
