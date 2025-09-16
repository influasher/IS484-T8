import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Container } from '@mui/material';
import { Login } from '@mui/icons-material';
import LoginComponent from '../components/ui/LoginComponent';
import logo from '../img/logos/download.png';

const LoginPage = () => {
    return (
        <Box sx={{ display: "flex", minHeight: "100vh" }}>
            <Box
              sx={{
                flex: 1,
                padding: 4,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <img
                src={logo} // Use the imported image
                style={{
                  width: '100%', // Make the image take up the full width of the parent
                  height: '100%', // Make the image take up the full height of the parent
                  objectFit: 'contain', // Ensure the image scales properly without distortion
                }}
              />
            </Box>
            <Box sx={{ width: "25%", borderLeft: "1px solid #ddd", padding: 2 }}>
                <LoginComponent/>
            </Box>
        </Box>
    );
};

export default LoginPage;