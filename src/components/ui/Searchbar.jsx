import React from 'react';
import Paper from "@mui/material/Paper";
import InputBase from "@mui/material/InputBase";
import Divider from "@mui/material/Divider";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

export const Searchbar = ({
  value,
  onChange = () => {},
  onSubmit,
  placeholder = "Search…",
  disabled,
  width = 300,
  autoFocus = false,
  sx,
}) => {
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && typeof onSubmit === "function") {
      onSubmit(value);
    }
  };

  const handleChange = (e) => {
    const value = e.target.value;
    onChange(value);
  };

  return (
    <Paper
      elevation={0}
      role="search"
      sx={{
        width,
        px: 1.5,
        py: 0.5,
        display: "flex",
        alignItems: "center",
        gap: 1,
        borderRadius: "9999px",
        bgcolor: "white",
        border: 1,
        borderColor: "divider",
        "&:focus-within": {
          boxShadow: (theme) => `0 0 0 3px ${theme.palette.primary.main}33`,
        },
      }}
    >
      <SearchRoundedIcon sx={{ fontSize: 22, opacity: 0.7 }} />
      <InputBase
        autoFocus={autoFocus}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        inputProps={{ "aria-label": placeholder }}
        disabled={disabled}
        sx={{ flex: 1 }}
      />
      {onSubmit && (
        <>
          <Divider orientation="vertical" flexItem />
          <IconButton
            size="small"
            aria-label="Submit search"
            onClick={() => onSubmit(value)}
          >
            <SearchRoundedIcon />
          </IconButton>
        </>
      )}
    </Paper>
  );
};

export default Searchbar;