import React from "react";
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';

const Filter = ({ onFilterChange }) => {
  const [filter, setFilter] = React.useState('all');

  const handleChange = (event) => {
    const value = event.target.value;
    setFilter(value);
    onFilterChange(value);
  };

  return (
    <FormControl fullWidth variant="outlined">
      <InputLabel id="filter-select-label">Filter by Date</InputLabel>
      <Select
        labelId="filter-select-label"
        value={filter}
        onChange={handleChange}
        label="Filter by Date"
        sx={{
          backgroundColor: 'white',
        }}
      >
        <MenuItem value="all">All Time</MenuItem>
        <MenuItem value="24">Last 24 Hours</MenuItem>
        <MenuItem value="48">Last 48 Hours</MenuItem>
        <MenuItem value="7d">Last 7 Days</MenuItem>
      </Select>
    </FormControl>
  );
};

export default Filter;