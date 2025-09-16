import { Chip } from "@mui/material";
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";

// Function to determine Chip styles
const getChipStyles = (value) => {
  if (value > 0)
    return { color: "#2e7d32", backgroundColor: "rgba(46, 125, 50, 0.1)" }; // light green
  if (value < 0)
    return { color: "#d32f2f", backgroundColor: "rgba(211, 47, 47, 0.1)" }; // light red
  return { color: "#616161", backgroundColor: "rgba(97, 97, 97, 0.1)" }; // neutral gray
};

// Reusable CustomChip
const CustomChip = ({ value, showArrow = false, labelOverride }) => {
  const styles = getChipStyles(value);
  console.log(styles.color)

  // Determine icon based on value
  const icon =
    showArrow && value !== 0
      ? value > 0
        ? <ArrowDropUpIcon fontSize="large" sx={{ mr: 0.3 }} style={{ color: styles.color }}/>
        : <ArrowDropDownIcon fontSize="large" sx={{ mr: 0.3 }} style={{ color: styles.color }}/>
      : null;

  const label = labelOverride || `${value.toFixed(2)}%`;

  return (
    <Chip
      icon={icon}
      label={label}
      sx={{
        fontSize: 16,
        fontWeight: 600,
        borderRadius: 1,
        ...styles,
        '& .MuiChip-label': {
          paddingLeft: 0,
          paddingRight: 1.2,
        },
        '& .MuiChip-icon': {
          margin: 0, // removes default margin
        },
      }}
    />
  );
};

export default CustomChip;
