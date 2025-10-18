#!/bin/bash

# Province Backend Development Server
# This script provides a robust development environment with auto-restart

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PORT=8000
LOG_FILE="backend.log"
PID_FILE="backend.pid"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

# Function to check if port is in use
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to kill processes on port
kill_port() {
    print_status "Killing processes on port $PORT..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found! Please create it first:"
        print_error "python -m venv venv"
        print_error "source venv/bin/activate"
        print_error "pip install -r requirements.txt"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check if strands-agents is installed
    if ! python -c "import strands" 2>/dev/null; then
        print_warning "strands-agents not found, installing..."
        pip install strands-agents
    fi
    
    # Check if uvicorn is installed
    if ! python -c "import uvicorn" 2>/dev/null; then
        print_warning "uvicorn not found, installing..."
        pip install uvicorn
    fi
    
    print_success "Dependencies checked"
}

# Function to start the server
start_server() {
    print_status "Starting backend server on port $PORT..."
    
    # Set Python path
    export PYTHONPATH="/Users/anhlam/province/backend/src:$PYTHONPATH"
    
    # Start server with nohup for stability
    nohup python -m uvicorn province.main:app \
        --reload \
        --host 0.0.0.0 \
        --port $PORT \
        --log-level info \
        --access-log \
        > $LOG_FILE 2>&1 &
    
    # Save PID
    echo $! > $PID_FILE
    
    # Wait a moment and check if it started
    sleep 3
    
    if check_port; then
        print_success "Backend server started successfully on http://localhost:$PORT"
        print_status "Logs: tail -f $LOG_FILE"
        print_status "PID: $(cat $PID_FILE)"
        return 0
    else
        print_error "Failed to start backend server"
        print_error "Check logs: tail $LOG_FILE"
        return 1
    fi
}

# Function to stop the server
stop_server() {
    print_status "Stopping backend server..."
    
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            rm -f $PID_FILE
            print_success "Backend server stopped"
        else
            print_warning "Process $PID not running"
            rm -f $PID_FILE
        fi
    fi
    
    # Also kill any processes on the port
    kill_port
}

# Function to restart the server
restart_server() {
    print_status "Restarting backend server..."
    stop_server
    sleep 2
    start_server
}

# Function to show status
show_status() {
    if check_port; then
        print_success "Backend server is running on port $PORT"
        if [ -f $PID_FILE ]; then
            print_status "PID: $(cat $PID_FILE)"
        fi
        
        # Test health endpoint
        if curl -s http://localhost:$PORT/api/v1/health/ >/dev/null 2>&1; then
            print_success "Health check passed"
        else
            print_warning "Health check failed"
        fi
    else
        print_error "Backend server is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f $LOG_FILE ]; then
        tail -f $LOG_FILE
    else
        print_error "Log file not found: $LOG_FILE"
    fi
}

# Main script logic
case "${1:-start}" in
    start)
        activate_venv
        check_dependencies
        
        if check_port; then
            print_warning "Port $PORT is already in use"
            show_status
        else
            start_server
        fi
        ;;
    stop)
        stop_server
        ;;
    restart)
        activate_venv
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    clean)
        print_status "Cleaning up..."
        stop_server
        rm -f $LOG_FILE $PID_FILE
        print_success "Cleanup complete"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the backend server"
        echo "  stop    - Stop the backend server"
        echo "  restart - Restart the backend server"
        echo "  status  - Check server status"
        echo "  logs    - Show server logs (tail -f)"
        echo "  clean   - Stop server and clean up files"
        exit 1
        ;;
esac
