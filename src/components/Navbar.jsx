import * as React from "react";
import Searchbar from "./ui/Searchbar";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import AccountCircleRoundedIcon from "@mui/icons-material/AccountCircleRounded";
import { useNavigate } from "react-router-dom";

const NavBar = ({
  searchValue,
  onSearchChange,
  onSearchSubmit,
  placeholder = "Search…",
  elevation = 0,
  sticky = true,
}) => {
  const navigate = useNavigate();
  const handleHomeClick = (e) => {
    navigate('/');
  };

  const handleProfileClick = (e) => {
    navigate('/profile');
  };

  return (
    <AppBar
      position={sticky ? "sticky" : "static"}
      color="transparent"
      elevation={elevation}
      sx={{
        bgcolor: (theme) => theme.palette.grey[200],
        borderBottom: 1,
        borderColor: "divider",
      }}
    >
      <Toolbar disableGutters sx={{ minHeight: 64 , mx: 3 }}>
        <Searchbar
          value={searchValue}
          onChange={onSearchChange}
          onSubmit={onSearchSubmit}
          placeholder={placeholder}
        />

        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, ml: "auto", pr: 0.5 }}>
          <Tooltip title="Home">
            <IconButton aria-label="Go to Home" onClick={handleHomeClick} size="large">
              <HomeRoundedIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Profile">
            <IconButton aria-label="Open profile" onClick={handleProfileClick} size="large">
              <AccountCircleRoundedIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default NavBar;