#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/schgen/project_boards.py
python3 scripts/schgen/verify_cross_board.py --export
python3 -m scripts.schgen.build_board_docs
