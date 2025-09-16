import * as React from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import logo from '../../../../img/logos/logo.png';

const items = [
  {
    // icon: <SettingsSuggestRoundedIcon sx={{ color: 'text.secondary' }} />,
    title: 'SentiFiance',
    description:
      'AI-powered financial sentiment analysis for smarter decisions.',
  },
];

export default function Content() {
  return (
    <Stack
      sx={{ flexDirection: 'column', alignSelf: 'center', gap: 4, maxWidth: 450 }}
    >
      <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
      <img
          src={logo} // Use the imported image
          alt="Logo"
          style={{
            border: '2px solid #ddd', // Adds a border around the image
            borderRadius: '10px', // Rounds the image (use '50%' for a circular image)
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)', // Adds a drop shadow
            width: '60%', // Ensures the image scales properly
          }}
        />
      </Box>
      {items.map((item, index) => (
        <Stack key={index} direction="row" sx={{ gap: 2 }}>
          {item.icon}
          <div>
            <Typography gutterBottom sx={{ fontWeight: 'medium', fontSize: '1.25rem' }}>
              {item.title}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {item.description}
            </Typography>
          </div>
        </Stack>
      ))}
    </Stack>
  );
}
