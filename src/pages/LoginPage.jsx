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
  CircularProgress,
} from "@mui/material";
import UBSLogo from "../img/logos/UBS2.jpg";
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import { sendOTP, verifyOTP } from "../services/authService";
import useAuth from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [emailError, setEmailError] = useState(false);
  const [emailErrorMessage, setEmailErrorMessage] = useState("");
  const [otpError, setOtpError] = useState(false);
  const [otpErrorMessage, setOtpErrorMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSendOtp = async () => {
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      setEmailError(true);
      setEmailErrorMessage("Please enter a valid email address.");
      return;
    }

    setEmailError(false);
    setEmailErrorMessage("");
    setLoading(true);

    try {
      const result = await sendOTP(email);

      if (result.success) {
        setOtpSent(true);
        console.log("OTP sent successfully");
      } else {
        setEmailError(true);
        setEmailErrorMessage(result.message);
      }
    } catch (error) {
      setEmailError(true);
      setEmailErrorMessage("Failed to send OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!otp || otp.length !== 6) {
      setOtpError(true);
      setOtpErrorMessage("Please enter a valid 6-digit OTP.");
      return;
    }

    setOtpError(false);
    setOtpErrorMessage("");
    setLoading(true);

    try {
      const result = await verifyOTP(otp);

      if (result.success) {
        // Login successful
        login(result.data.user, result.data.access_token);

        // Redirect based on user role
        if (result.data.user.role === "client") {
          navigate("/Client");
        } else if (result.data.user.role === "relationship_manager") {
          navigate("/RM");
        } else {
          navigate("/DashboardPage");
        }
      } else {
        setOtpError(true);
        setOtpErrorMessage(result.message);
      }
    } catch (error) {
      setOtpError(true);
      setOtpErrorMessage("Failed to verify OTP. Please try again.");
    } finally {
      setLoading(false);
    }
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
                disabled={otpSent || loading}
              />
            </FormControl>
            {!otpSent ? (
              <Button
                type="button"
                variant="contained"
                onClick={handleSendOtp}
                color="error"
                disabled={loading}
                sx={{
                  height: "46px",
                  width: "150px",
                  "&:hover": { backgroundColor: "darkred" },
                  mt: 1
                }}
                endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowForwardIosIcon />}
              >
                {loading ? "Sending..." : "Send OTP"}
              </Button>
            ) : (
              <>
                <FormControl>
                  <FormLabel htmlFor="otp">OTP</FormLabel>
                  <TextField
                    error={otpError}
                    helperText={otpErrorMessage}
                    id="otp"
                    name="otp"
                    placeholder="Enter 6-digit OTP"
                    type="text"
                    fullWidth
                    variant="outlined"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    disabled={loading}
                    inputProps={{ maxLength: 6 }}
                  />
                </FormControl>
                <Button
                  type="button"
                  fullWidth
                  variant="contained"
                  onClick={handleLogin}
                  disabled={loading || otp.length !== 6}
                  color="error"
                  sx={{ "&:hover": { backgroundColor: "darkred" } }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : "Login"}
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
