#!/bin/bash

# Stock Analyzer Bot - Run Script
# This script activates virtual environment and runs the bot

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  Stock Analyzer Bot${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"

# Get directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    
    echo -e "${YELLOW}Installing dependencies...${NC}"
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure it.${NC}"
    exit 1
fi

# Run the bot
echo -e "${GREEN}Starting bot...${NC}"
echo ""

# Check for arguments
if [ "$1" == "--manual" ]; then
    python main.py --manual
elif [ "$1" == "--test" ]; then
    python main.py --test
else
    python main.py
fi

# Deactivate virtual environment
deactivate
