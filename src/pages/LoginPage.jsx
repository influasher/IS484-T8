import React, { useState } from "react";
import {
  Stack,
  Card,
  Typography,
  TextField,
  Button,
  Box,
  FormControl,
  FormLabel,
} from "@mui/material";
import UBSLogo from "../img/logos/UBS2.jpg";
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [emailError, setEmailError] = useState(false);
  const [emailErrorMessage, setEmailErrorMessage] = useState("");
  const [passwordError, setPasswordError] = useState(false);
  const [passwordErrorMessage, setPasswordErrorMessage] = useState("");

  const handleSendOtp = () => {
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      setEmailError(true);
      setEmailErrorMessage("Please enter a valid email address.");
      return;
    }
    setEmailError(false);
    setEmailErrorMessage("");
    console.log(`Sending OTP to ${email}`);
    setOtpSent(true);
  };

  const handleLogin = () => {
    if (!otp || otp.length !== 6) {
      console.log("Invalid OTP");
      return;
    }
    console.log(
      `Logging in with Email: ${email}, Password: ${password}, OTP: ${otp}`
    );
  };
  return (
    <Stack direction="row" sx={{ height: "100vh" }}>
      {/* Left side with image */}
      <Box
        sx={{
          flex: 2,
          backgroundImage: `url(${UBSLogo})`, // replace with your image path
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />

      {/* Right side with login form */}
      <Stack
        flex={1}
        justifyContent="center"
        alignItems="center"
        sx={{ m: 4, p: 4 }}
      >
        <Stack direction="column" spacing={7} sx={{ width: "100%" }}>
          <Stack direction="column" spacing={1} sx={{ width: "100%" }}>
            <Typography
              component="h1"
              variant="h4"
              sx={{ width: "100%", fontSize: "clamp(2rem, 10vw, 2.15rem)" }}
            >
              Sign in
            </Typography>

            <Typography variant="subtitle1" sx={{ width: "100%" }}>
              Welcome to SentiFinance — AI-powered sentiment analysis for
              smarter financial decisions.
            </Typography>
          </Stack>

          <Box
            component="form"
            noValidate
            sx={{
              display: "flex",
              flexDirection: "column",
              width: "100%",
              gap: 2,
            }}
          >
            <FormControl>
              <FormLabel htmlFor="email">Email</FormLabel>
              <TextField
                error={emailError}
                helperText={emailErrorMessage}
                id="email"
                type="email"
                name="email"
                placeholder="your@email.com"
                autoComplete="email"
                autoFocus
                required
                fullWidth
                variant="outlined"
                color={emailError ? "error" : "primary"}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </FormControl>
            <FormControl>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <FormLabel htmlFor="password">Password</FormLabel>
              </Box>
              <TextField
                error={passwordError}
                helperText={passwordErrorMessage}
                name="password"
                placeholder="•••••••••"
                type="password"
                id="password"
                autoComplete="current-password"
                required
                fullWidth
                variant="outlined"
                color={passwordError ? "error" : "primary"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </FormControl>
            {!otpSent ? (
              <Button
                type="button"
                variant="contained"
                onClick={handleSendOtp}
                color="error"
                sx={{ height: "46px", width: "150px",
                "&:hover": { backgroundColor: "darkred" }, mt: 1}}
                endIcon={<ArrowForwardIosIcon  />}
              >
                Send OTP
              </Button>
            ) : (
              <>
                <FormControl>
                  <FormLabel htmlFor="otp">OTP</FormLabel>
                  <TextField
                    id="otp"
                    name="otp"
                    placeholder="Enter OTP"
                    type="text"
                    fullWidth
                    variant="outlined"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                  />
                </FormControl>
                <Button
                  type="button"
                  fullWidth
                  variant="contained"
                  onClick={handleLogin}
                >
                  Login
                </Button>
              </>
            )}
          </Box>
        </Stack>
      </Stack>
    </Stack>
  );
};

export default LoginPage;
