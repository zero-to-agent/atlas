#!/usr/bin/env bash
# .claude/hooks/lint-check.sh
# Runs ruff check on the file Claude just edited.
# Reads PostToolUse JSON from stdin, extracts the file path.

set -euo pipefail

# Parse the file path from the hook input JSON
FILE_PATH=$(jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)

# Only lint Python files
if [[ -z "$FILE_PATH" || "$FILE_PATH" != *.py ]]; then
    exit 0
fi

# Run ruff with a timeout to prevent hangs
LINT_OUTPUT=$(timeout 10 ruff check "$FILE_PATH" 2>&1) || true
EXIT_CODE=${PIPESTATUS[0]:-$?}

if [[ $EXIT_CODE -ne 0 && -n "$LINT_OUTPUT" ]]; then
    # Return lint errors as JSON so Claude sees them in context
    jq -n --arg output "$LINT_OUTPUT" --arg file "$FILE_PATH" '{
        hookSpecificOutput: {
            hookEventName: "PostToolUse",
            message: ("Lint errors in " + $file + ":\n" + $output)
        }
    }'
fi
