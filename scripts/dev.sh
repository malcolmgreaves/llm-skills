#!/usr/bin/env bash
cco auto \
    --add-dir "${UV_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/uv}" \
    --add-dir "${UV_TOOL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/uv/tools}" \
    --add-dir "${UV_CREDENTIALS_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/uv/credentials}" \
    --add-dir "${UV_PROJECT_ENVIRONMENT:-$PWD}" \
    --add-dir "${UV_PYTHON_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/uv/python}" \
    --add-dir "${UV_TOOL_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}" \
    --add-dir "${UV_PYTHON_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
