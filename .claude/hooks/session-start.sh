#!/bin/bash
set -euo pipefail

# Only run in Claude Code remote environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# SessionStart hook for Claude skills repository
# Add dependency installation commands below as the repo evolves

echo "SessionStart hook completed successfully"
