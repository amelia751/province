#!/usr/bin/env python3
"""
Backend Server Monitor
Monitors the backend server and automatically restarts it if it crashes.
"""

import os
import sys
import time
import signal
import subprocess
import requests
from datetime import datetime
from pathlib import Path

class BackendMonitor:
    def __init__(self):
        self.port = 8000
        self.health_url = f"http://localhost:{self.port}/api/v1/health/"
        self.process = None
        self.restart_count = 0
        self.max_restarts = 10
        self.check_interval = 30  # seconds
        self.startup_wait = 10    # seconds to wait after startup
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def is_server_healthy(self):
        """Check if the server is responding to health checks."""
        try:
            response = requests.get(self.health_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def start_server(self):
        """Start the backend server."""
        self.log("Starting backend server...")
        
        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{Path.cwd()}/src:{env.get('PYTHONPATH', '')}"
        
        # Start the server
        cmd = [
            sys.executable, "-m", "uvicorn", "province.main:app",
            "--reload", "--host", "0.0.0.0", "--port", str(self.port)
        ]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.log(f"Server started with PID {self.process.pid}")
            
            # Wait for startup
            time.sleep(self.startup_wait)
            
            # Check if it's healthy
            if self.is_server_healthy():
                self.log("✅ Server is healthy and responding")
                return True
            else:
                self.log("❌ Server started but not responding to health checks")
                return False
                
        except Exception as e:
            self.log(f"❌ Failed to start server: {e}", "ERROR")
            return False
    
    def stop_server(self):
        """Stop the backend server."""
        if self.process:
            self.log("Stopping backend server...")
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                self.log("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                self.log("⚠️ Server didn't stop gracefully, killing...")
                self.process.kill()
                self.process.wait()
                self.log("✅ Server killed")
            except Exception as e:
                self.log(f"❌ Error stopping server: {e}", "ERROR")
            finally:
                self.process = None
    
    def restart_server(self):
        """Restart the backend server."""
        self.restart_count += 1
        
        if self.restart_count > self.max_restarts:
            self.log(f"❌ Maximum restart attempts ({self.max_restarts}) reached. Exiting.", "ERROR")
            return False
        
        self.log(f"🔄 Restarting server (attempt {self.restart_count}/{self.max_restarts})")
        
        self.stop_server()
        time.sleep(2)  # Brief pause before restart
        
        return self.start_server()
    
    def monitor(self):
        """Main monitoring loop."""
        self.log("🚀 Starting backend monitor...")
        
        # Initial startup
        if not self.start_server():
            self.log("❌ Failed to start server initially. Exiting.", "ERROR")
            return
        
        # Reset restart count after successful startup
        self.restart_count = 0
        
        try:
            while True:
                time.sleep(self.check_interval)
                
                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    self.log("❌ Server process has died", "ERROR")
                    if not self.restart_server():
                        break
                    continue
                
                # Check if server is healthy
                if not self.is_server_healthy():
                    self.log("❌ Server health check failed", "ERROR")
                    if not self.restart_server():
                        break
                    continue
                
                # Reset restart count on successful health check
                if self.restart_count > 0:
                    self.log("✅ Server recovered, resetting restart count")
                    self.restart_count = 0
                
                self.log("✅ Server is healthy")
                
        except KeyboardInterrupt:
            self.log("🛑 Monitor interrupted by user")
        except Exception as e:
            self.log(f"❌ Monitor error: {e}", "ERROR")
        finally:
            self.stop_server()
            self.log("👋 Monitor stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.log(f"🛑 Received signal {signum}, shutting down...")
        self.stop_server()
        sys.exit(0)

def main():
    monitor = BackendMonitor()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, monitor.signal_handler)
    signal.signal(signal.SIGTERM, monitor.signal_handler)
    
    # Start monitoring
    monitor.monitor()

if __name__ == "__main__":
    main()
