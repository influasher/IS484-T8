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
import LogoutIcon from '@mui/icons-material/Logout';

function CustomIcon(props) {
  return <SvgIcon {...props} component={UBSLogo} inheritViewBox />;
}

const NavBar = ({ role, elevation = 0, sticky = true }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  // Map paths to tab index
  const paths = [
    ROUTES.ENTITIES,
    ROUTES.NEWS,
    ROUTES.DASHBOARD,
    ROUTES.CLIENT_HOME,
    ROUTES.RM_HOME,
  ];

  const handleChange = (event, newValue) => {
    navigate(paths[newValue]);
  };

  const handleHomeClick = () => {
    const redirectMap = {
      RM: ROUTES.RM_HOME,
      Client: ROUTES.CLIENT_HOME,
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
        sx={{ alignItems: "center", justifyContent: "start" }}
      >
        {/* Home icon */}
        <IconButton
          onClick={handleHomeClick}
          sx={{
            p: 0,
            "&:hover": {
              backgroundColor: "transparent", // remove hover background
            },
          }}
        >
          <CustomIcon sx={{ fontSize: 80 }} />
        </IconButton>
        <Tabs
          value={paths.indexOf(location.pathname)}
          onChange={handleChange}
          sx={{
            height: "64px",
            minHeight: "64px",
            "& .MuiTab-root": {
              minHeight: "64px",
              color: "grey", // unselected tab text
              "&.Mui-selected": {
                color: "black", // selected tab text
              },
            },
            "& .MuiTabs-indicator": {
              backgroundColor: "red", // indicator color
            },
          }}
        >
          <Tab label="Entities" />
          <Tab label="News" />
          <Tab label="Dashboard" />
          <Tab label="Client" />
          <Tab label="RM" />
        </Tabs>

        {/* Logout button */}
        <Button
          onClick={handleLogout}
          startIcon={<LogoutIcon />}
          sx={{
            color: "grey",
            "&:hover": {
              backgroundColor: "transparent",
              color: "red",
            },
          }}
        >
          Logout
        </Button>
      </Stack>
    </AppBar>
  );
};

export default NavBar;
