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
  onSearchSubmit,
  placeholder = "Search…",
  elevation = 0,
  sticky = true,
}) => {
  const [query, setQuery] = React.useState("");
  const navigate = useNavigate();

  const handleHomeClick = (e) => {
    if (typeof onHomeClick === "function") return onHomeClick();
    navigate("/");
  };

  const handleProfileClick = (e) => {
    if (typeof onProfileClick === "function") return onProfileClick();
    navigate("/profile");
  };

  const handleSearchChange = (newValue) => {
    setQuery(newValue);
  };

  const handleClear = () => {
    setQuery(""); // resets the search field
  };

  // const handleSearchSubmit = (submittedValue) => {
  //   // 👇 your search logic here
  //   console.log("Searching for:", submittedValue);

  //   // Example: call an API
  //   fetch(`/api/search?q=${encodeURIComponent(submittedValue)}`)
  //     .then((res) => res.json())
  //     .then((data) => {
  //       console.log("Search results:", data);
  //     })
  //     .catch((err) => {
  //       console.error("Search error:", err);
  //     });
  // };

  return (
    <AppBar
      position={sticky ? "sticky" : "static"}
      color="transparent"
      elevation={elevation}
      sx={{
        zIndex: (t) => t.zIndex.modal + 1,
        bgcolor: (theme) => theme.palette.grey[300],
        borderBottom: 1.5,
        borderColor: "divider",
        boxShadow: (theme) => `0 1px 4px ${theme.palette.grey[400]}33`,
      }}
    >
      <Toolbar disableGutters sx={{ minHeight: 64 , mx: 3 }}>
        <Searchbar
          value={query}
          onChange={handleSearchChange}
          onSubmit={onSearchSubmit}
          onClear={handleClear}
          placeholder={placeholder}
        />

        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, ml: "auto" }}>
          <Tooltip title="Home">
            <IconButton aria-label="Go to Home" onClick={handleHomeClick} size="large">
              <HomeRoundedIcon sx={{ color: "black" }}/>
            </IconButton>
          </Tooltip>
          <Tooltip title="Profile">
            <IconButton aria-label="Open profile" onClick={handleProfileClick} size="large">
              <AccountCircleRoundedIcon sx={{ color: "black" }}/>
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default NavBar;