import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Container } from '@mui/material';

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [otp, setOtp] = useState('');
    const [otpSent, setOtpSent] = useState(false);

    const handleSendOtp = () => {
        // Handle sending email and password to backend and sending OTP
        console.log('Email:', email);
        console.log('Password:', password);
        // Simulate OTP sent
        setOtpSent(true);
        console.log('OTP sent to user');
    };

    const handleLogin = () => {
        // Handle login with OTP
        console.log('Email:', email);
        console.log('Password:', password);
        console.log('OTP:', otp);
    };

    return (
        <Container maxWidth="sm">
            <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="center"
                minHeight="100vh"
            >
                <Typography variant="h4" gutterBottom>
                    Login
                </Typography>
                <TextField
                    label="Email"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                <TextField
                    label="Password"
                    type="password"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                {!otpSent ? (
                    <Button
                        variant="contained"
                        color="primary"
                        fullWidth
                        onClick={handleSendOtp}
                        sx={{ mt: 2 }}
                    >
                        Send OTP
                    </Button>
                ) : (
                    <>
                        <TextField
                            label="OTP"
                            variant="outlined"
                            fullWidth
                            margin="normal"
                            value={otp}
                            onChange={(e) => setOtp(e.target.value)}
                        />
                        <Button
                            variant="contained"
                            color="primary"
                            fullWidth
                            onClick={handleLogin}
                            sx={{ mt: 2 }}
                        >
                            Login
                        </Button>
                    </>
                )}
            </Box>
        </Container>
    );
};

export default LoginPage;