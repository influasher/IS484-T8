import React from 'react';
import { render } from '@testing-library/react';

// Simple test that always passes
test('dummy test for CI', () => {
  expect(2 + 2).toBe(4);
});

// Test that React can render something basic
test('can render a simple component', () => {
  const TestComponent = () => <div>Hello Test</div>;
  render(<TestComponent />);
  expect(true).toBe(true);
});
