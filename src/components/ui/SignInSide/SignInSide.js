import * as React from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import Stack from '@mui/material/Stack';
import { ThemeProvider, createTheme } from '@mui/material/styles'; // Replacement for AppTheme
import Button from '@mui/material/Button'; // Replacement for ColorModeSelect
import SignInCard from './components/SignInCard';
import Content from './components/Content';
import loginBg from '../../../img/loginBg.jpg';
import UBS2 from '../../../img/logos/UBS2.jpg';

const theme = createTheme(); // Default Material-UI theme

export default function SignInSide(props) {
  return (
    <ThemeProvider theme={theme}> {/* Replacing AppTheme */}
      <CssBaseline enableColorScheme />
      <Button
        sx={{ position: 'fixed', top: '1rem', right: '1rem' }} // Replacing ColorModeSelect
        variant="contained"
      >
        Toggle Theme
      </Button>
      <Stack
        direction="column"
        component="main"
        sx={[
          {
            justifyContent: 'center',
            height: 'calc((1 - var(--template-frame-height, 0)) * 100%)',
            marginTop: 'max(40px - var(--template-frame-height, 0px), 0px)',
            minHeight: '100%',
          },
          (theme) => ({
            '&::before': {
              content: '""',
              display: 'block',
              position: 'absolute',
              zIndex: -1,
              inset: 0,
              backgroundImage: `url(${UBS2})`,
              backgroundRepeat: 'no-repeat',
              backgroundSize: 'cover', // Ensures the image covers the entire background
              backgroundPosition: 'center', // Centers the image
              filter: 'blur(4px)', // Adds a soft blur effect
              ...theme.applyStyles?.('dark', {
                backgroundImage: `url(${UBS2})`,
              }),
            },
          }),
        ]}
      >
        <Stack
          direction={{ xs: 'column-reverse', md: 'row' }}
          sx={{
            justifyContent: 'center',
            gap: { xs: 6, sm: 12 },
            p: 2,
            mx: 'auto',
          }}
        >
          <Content />
          <SignInCard />
        </Stack>
      </Stack>
    </ThemeProvider>
  );
}