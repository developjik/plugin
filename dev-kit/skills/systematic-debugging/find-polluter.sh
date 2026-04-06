#!/usr/bin/env bash
# Bisection script to find which test creates unwanted files/state
# Usage: ./find-polluter.sh <file_or_dir_to_check> <test_file_extension> [test_command]
# Example: ./find-polluter.sh '.git' 'test.ts'
# Example: ./find-polluter.sh '.git' 'test.ts' 'yarn test'
#
# Exit codes:
#   0 - Polluter found (test identified successfully)
#   1 - No polluter found, or error (invalid arguments, no test files, bad path)

set -e

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
  echo "Usage: $0 <file_to_check> <test_file_extension> [test_command]"
  echo "Example: $0 '.git' 'test.ts'"
  echo "Example: $0 '.git' 'test.ts' 'yarn test'"
  exit 1
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"
TEST_CMD="${3:-npm test}"

# Validate pollution check path to prevent destructive operations
case "$POLLUTION_CHECK" in
  /*|..|.|'') echo "Error: invalid path: $POLLUTION_CHECK (must be a relative, non-root path)" >&2; exit 1 ;;
esac

echo "🔍 Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo "Test command: $TEST_CMD"
echo ""

# Get list of test files and count safely (handles filenames with spaces)
TOTAL=$(find . -type f -name "*$TEST_PATTERN*" | wc -l | tr -d ' ')

if [ "$TOTAL" -eq 0 ]; then
  echo "No test files found matching: $TEST_PATTERN"
  exit 1
fi

echo "Found $TOTAL test files"
echo ""

COUNT=0
while IFS= read -r TEST_FILE; do
  # Skip empty lines (can occur with trailing newlines)
  [ -z "$TEST_FILE" ] && continue

  COUNT=$((COUNT + 1))

  # Clean up target pollution from previous tests to avoid false skips
  rm -rf "$POLLUTION_CHECK" 2>/dev/null || true

  echo "[$COUNT/$TOTAL] Testing: $TEST_FILE"

  # Run the test
  $TEST_CMD "$TEST_FILE" > /dev/null 2>&1 || true

  # Check if pollution appeared
  if [ -e "$POLLUTION_CHECK" ]; then
    echo ""
    echo "🎯 FOUND POLLUTER!"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    echo ""
    echo "Pollution details:"
    ls -la "$POLLUTION_CHECK"
    echo ""
    echo "To investigate:"
    echo "  $TEST_CMD $TEST_FILE    # Run just this test"
    echo "  cat $TEST_FILE         # Review test code"
    exit 0
  fi
done < <(find . -type f -name "*$TEST_PATTERN*" | sort)

echo ""
echo "✅ No polluter found - all tests clean!"
exit 1
