import React, { useState } from "react";
import AppBar from "@mui/material/AppBar";
import IconButton from "@mui/material/IconButton";
import { useNavigate } from "react-router-dom";
import { ReactComponent as UBSLogo } from "../img/logos/ubs-transparent.svg";
import { SvgIcon, Button } from "@mui/material";
import { Tabs, Tab, Stack } from "@mui/material";
import { Link, useLocation } from "react-router-dom";
import { ROUTES } from "../routes";
import useAuth from "../hooks/useAuth";
import LogoutIcon from "@mui/icons-material/Logout";

function CustomIcon(props) {
  return <SvgIcon {...props} component={UBSLogo} inheritViewBox />;
}

const NavBar = ({ role, elevation = 0, sticky = true }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  // Build tabs dynamically
  const baseTabs = [
    { label: "Entities", path: ROUTES.ENTITIES },
    { label: "News", path: ROUTES.NEWS },
    { label: "Dashboard", path: ROUTES.DASHBOARD },
  ];

  const paths = baseTabs.map((t) => t.path);
  const currentIndex = paths.indexOf(location.pathname);

  const handleChange = (event, newValue) => {
    navigate(paths[newValue]);
  };

  const handleHomeClick = () => {
    const redirectMap = {
      relationship_manager: ROUTES.RM_HOME,
      client: ROUTES.CLIENT_HOME,
    };
    navigate(redirectMap[role] || ROUTES.LOGIN);
  };

  const handleLogout = async () => {
    await logout();
    navigate(ROUTES.LOGIN);
  };

  return (
    <AppBar
      position={sticky ? "sticky" : "static"}
      color="transparent"
      elevation={elevation}
      sx={{
        zIndex: (t) => t.zIndex.modal + 1,
        bgcolor: "white",
        borderBottom: 1.5,
        borderColor: "divider",
        boxShadow: (theme) => `0 1px 4px ${theme.palette.grey[400]}33`,
        px: 5,
        maxHeight: 80,
      }}
    >
      <Stack
        direction="row"
        spacing={2}
        sx={{ alignItems: "center", justifyContent: "space-between" }}
      >
        <Stack
          direction="row"
          spacing={2}
          sx={{ alignItems: "center", justifyContent: "start" }}
        >
          {/* Home icon */}
          <IconButton
            aria-label="home"
            onClick={handleHomeClick}
            sx={{
              p: 0,
              "&:hover": { backgroundColor: "transparent" },
            }}
          >
            <CustomIcon sx={{ fontSize: 80 }} />
          </IconButton>

          <Tabs
            value={currentIndex === -1 ? false : currentIndex}
            onChange={handleChange}
            sx={{
              height: "64px",
              minHeight: "64px",
              "& .MuiTab-root": {
                minHeight: "64px",
                color: "grey",
                "&.Mui-selected": { color: "black" },
              },
              "& .MuiTabs-indicator": { backgroundColor: "red" },
            }}
          >
            {baseTabs.map((tab, idx) => (
              <Tab key={idx} label={tab.label} aria-label={tab.label}/>
            ))}
          </Tabs>
        </Stack>

        {/* Logout button */}
        <Button
          aria-label="logout"
          variant="outlined"
          onClick={handleLogout}
          startIcon={<LogoutIcon />}
          color="error"
        >
          Logout
        </Button>
      </Stack>
    </AppBar>
  );
};

export default NavBar;
