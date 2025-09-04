import React from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';

const Sort = ({ onSortChange }) => {
  const [sortOrder, setSortOrder] = React.useState('desc');

  const handleChange = (event) => {
    const value = event.target.value;
    setSortOrder(value);
    onSortChange(value);
  };

  return (
    <FormControl fullWidth variant="outlined">
      <InputLabel id="sort-select-label">Sort by</InputLabel>
      <Select
        labelId="sort-select-label"
        value={sortOrder}
        onChange={handleChange}
        label="Sort by"
        sx={{
          backgroundColor: 'white',
        }}
      >
        <MenuItem value="asc">Ascending</MenuItem>
        <MenuItem value="desc">Descending</MenuItem>
      </Select>
    </FormControl>
  );
};

export default Sort;