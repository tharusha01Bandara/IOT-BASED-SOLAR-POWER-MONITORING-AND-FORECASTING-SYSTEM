#!/bin/bash
# Setup cron job for automated model retraining
# Usage: ./setup_cron.sh [device_id] [time]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}Setting up Cron Job for Model Retraining${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Default values
DEVICE_ID=${1:-tracker01}
SCHEDULE_TIME=${2:-18:30}
DAYS=7

# Get project root directory (parent of tools/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
TOOLS_DIR="$PROJECT_ROOT/tools"
WORKER_SCRIPT="$TOOLS_DIR/retrain_worker.py"

# Detect Python executable (prefer venv)
if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXE="$PROJECT_ROOT/venv/bin/python"
elif [ -f "$PROJECT_ROOT/venv/bin/python3" ]; then
    PYTHON_EXE="$PROJECT_ROOT/venv/bin/python3"
elif command -v python3 &> /dev/null; then
    PYTHON_EXE=$(which python3)
elif command -v python &> /dev/null; then
    PYTHON_EXE=$(which python)
else
    echo -e "${RED}ERROR: Python not found${NC}"
    echo "Please install Python or activate your virtual environment"
    exit 1
fi

# Log file location
LOG_DIR="/var/log"
if [ ! -w "$LOG_DIR" ]; then
    LOG_DIR="$PROJECT_ROOT/logs"
    mkdir -p "$LOG_DIR"
fi
LOG_FILE="$LOG_DIR/solar_retrain.log"

echo -e "${GREEN}Configuration:${NC}"
echo "  Device ID: $DEVICE_ID"
echo "  Schedule: Daily at $SCHEDULE_TIME"
echo "  Training Days: $DAYS"
echo "  Project Root: $PROJECT_ROOT"
echo "  Python: $PYTHON_EXE"
echo "  Log File: $LOG_FILE"
echo ""

# Verify files exist
if [ ! -f "$WORKER_SCRIPT" ]; then
    echo -e "${RED}ERROR: Worker script not found: $WORKER_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Worker script found${NC}"

# Test Python
if ! $PYTHON_EXE -c "import sys; sys.exit(0)" 2>/dev/null; then
    echo -e "${RED}ERROR: Python executable test failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python executable verified${NC}"
echo ""

# Parse time (HH:MM to cron format)
HOUR=$(echo $SCHEDULE_TIME | cut -d: -f1)
MINUTE=$(echo $SCHEDULE_TIME | cut -d: -f2)

# Remove leading zeros for cron
HOUR=$(echo $HOUR | sed 's/^0*//')
MINUTE=$(echo $MINUTE | sed 's/^0*//')

# Build cron command
CRON_COMMAND="$MINUTE $HOUR * * * cd \"$TOOLS_DIR\" && \"$PYTHON_EXE\" retrain_worker.py --device $DEVICE_ID --days $DAYS >> \"$LOG_FILE\" 2>&1"

echo -e "${YELLOW}Cron Job to be Added:${NC}"
echo "$CRON_COMMAND"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "retrain_worker.py"; then
    echo -e "${YELLOW}WARNING: Existing retraining cron job found${NC}"
    echo ""
    echo "Current cron jobs for retraining:"
    crontab -l 2>/dev/null | grep "retrain_worker.py"
    echo ""
    read -p "Do you want to replace it? (yes/no): " REPLACE
    if [ "$REPLACE" != "yes" ]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi
    
    # Remove old cron job
    echo "Removing old cron job..."
    crontab -l 2>/dev/null | grep -v "retrain_worker.py" | crontab -
fi

# Add new cron job
echo "Adding cron job..."
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Cron job added successfully${NC}"
else
    echo -e "${RED}ERROR: Failed to add cron job${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Verify cron job
echo -e "${CYAN}Current cron jobs:${NC}"
crontab -l | grep "retrain_worker.py"
echo ""

# Test run option
echo -e "${YELLOW}Do you want to run a test now? (yes/no)${NC}"
read -p "This will execute the retraining script immediately: " TEST_RUN

if [ "$TEST_RUN" = "yes" ]; then
    echo ""
    echo -e "${GREEN}Running test...${NC}"
    echo "Output will be saved to: $LOG_FILE"
    echo ""
    
    cd "$TOOLS_DIR"
    $PYTHON_EXE retrain_worker.py --device $DEVICE_ID --days $DAYS --verbose
    
    echo ""
    echo -e "${GREEN}✓ Test completed${NC}"
    echo "Check log file for details: $LOG_FILE"
fi

echo ""
echo -e "${CYAN}Useful Commands:${NC}"
echo "  View cron jobs:  crontab -l"
echo "  Edit cron jobs:  crontab -e"
echo "  View logs:       tail -f $LOG_FILE"
echo "  Remove job:      crontab -e (then delete the line)"
echo ""
echo -e "${GREEN}The retraining job will run daily at $SCHEDULE_TIME${NC}"
echo ""
