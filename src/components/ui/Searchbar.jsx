import React from 'react';
import Paper from "@mui/material/Paper";
import InputBase from "@mui/material/InputBase";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

export const Searchbar = ({
  value,
  onChange = () => {},
  onSubmit,
  placeholder = "Search…",
  disabled,
  width = 300,
  onClear,
  autoFocus=false,
  sx,
}) => {
  const inputRef = React.useRef(null);
  const isSubmitFn = typeof onSubmit === "function";
  
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && isSubmitFn) {
      e.preventDefault();
      onSubmit(value);
    }
    if (e.key === "Escape") {
      e.preventDefault();
      handleClear();
    }
  };

  const handleChange = (e) => {
    onChange(e.target.value);
  };

  const handleSubmit = (e) => {
    if (!isSubmitFn) return;
    e.preventDefault();
    onSubmit(value);
  };

  const handleClear = () => {
    if (onClear) onClear();
    else onChange("");
  };

  return (
    <Paper
      component="form"
      elevation={0}
      onSubmit={handleSubmit}
      role="search"
      sx={{
        width,
        px: 1.5,
        py: 0.3,
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
        inputRef={inputRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        autoFocus={autoFocus}
        placeholder={placeholder}
        inputProps={{ "aria-label": placeholder }}
        disabled={disabled}
        sx={{ flex: 1 }}
      />

      {/* Clear button (always visible) */}
      <Tooltip title="Clear (Esc)">
        <IconButton
          size="small"
          aria-label="Clear search"
          onClick={handleClear}
          disabled={disabled}
        >
          <CloseRoundedIcon />
        </IconButton>
      </Tooltip>

      {/* Submit button (optional; rendered only if onSubmit provided) */}
      {isSubmitFn && (
        <>
          <Divider orientation="vertical" flexItem />
          <Tooltip title="Search (Enter)">
            <span>
              <IconButton
                size="small"
                aria-label="Submit search"
                type="submit"
                disabled={disabled}
              >
                <SearchRoundedIcon />
              </IconButton>
            </span>
          </Tooltip>
        </>
      )}
    </Paper>
  );
};

export default Searchbar;