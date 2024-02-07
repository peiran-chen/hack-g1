#!/bin/bash

# Install debugger if not present
python -m debugpy --help> /dev/null 2>&1||python -m pip install 'debugpy==1.8.0'

# Allow debug app
python -m debugpy --listen 0.0.0.0:5678 \
  -m streamlit run --server.headless true ./1_Commence_Estimates.py
