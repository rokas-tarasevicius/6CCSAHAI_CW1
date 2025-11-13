# Frontend Tests

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Test Structure

### Score Change Indicator Tests

Located in `src/components/__tests__/ScorePanel.test.tsx`:

- ✅ Displays trophy score correctly
- ✅ Calculates and displays level correctly
- ✅ Hides score change indicator when undefined
- ✅ Hides score change indicator when change is 0
- ✅ Shows positive score change with up arrow (↑)
- ✅ Shows negative score change with down arrow (↓)
- ✅ Applies correct CSS classes (positive/negative)
- ✅ Displays remaining points until next level
- ✅ Handles score updates correctly
- ✅ Shows absolute value of negative changes

### Score Change Utility Tests

Located in `src/utils/__tests__/scoreChange.test.ts`:

- ✅ Calculates positive changes correctly
- ✅ Calculates negative changes correctly
- ✅ Returns 0 when scores are equal
- ✅ Determines when to show score change indicator
- ✅ Determines if change is positive or negative

## Test Coverage

The tests verify:
1. Score change calculation logic
2. Score change indicator visibility
3. Arrow direction (up/down) based on change
4. CSS class application (positive/negative)
5. Edge cases (undefined, zero, negative values)

