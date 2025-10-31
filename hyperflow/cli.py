#!/usr/bin/env python3
"""
HyperFlow CLI - Command line interface for managing HyperFlow daemon
"""

import argparse
import subprocess
import sys
import os
import signal
import psutil
import time
from pathlib import Path


def get_pid_file():
    """Get the path to the PID file"""
    return Path.home() / ".config/hyperflow/hyperflow.pid"


def find_daemon_process():
    """Find running HyperFlow daemon process"""
    # First try to read from PID file
    pid_file = get_pid_file()
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            # Verify the process is actually running and is a HyperFlow daemon
            proc = psutil.Process(pid)
            if 'hyperflow' in ' '.join(proc.cmdline()) and 'daemon.py' in ' '.join(proc.cmdline()):
                return pid
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied, FileNotFoundError):
            # PID file is invalid or process is not running
            if pid_file.exists():
                pid_file.unlink()
    
    # Fallback: search for the process
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'hyperflow' in proc.info['cmdline'] and 'daemon.py' in proc.info['cmdline']:
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None


def start_daemon():
    """Start the HyperFlow daemon"""
    pid = find_daemon_process()
    if pid:
        print(f"HyperFlow daemon is already running (PID: {pid})")
        return
    
    # Find daemon script
    daemon_script = Path(__file__).parent / 'daemon.py'
    if not daemon_script.exists():
        print("Error: daemon.py not found")
        return
    
    # Start daemon
    try:
        process = subprocess.Popen([
            sys.executable, str(daemon_script)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Write PID to file
        pid_file = get_pid_file()
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        print(f"Started HyperFlow daemon (PID: {process.pid})")
    except Exception as e:
        print(f"Error starting daemon: {e}")


def stop_daemon():
    """Stop the HyperFlow daemon"""
    pid = find_daemon_process()
    if not pid:
        print("HyperFlow daemon is not running")
        return
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to HyperFlow daemon (PID: {pid})")
        
        # Wait a bit for graceful shutdown
        time.sleep(1)
        
        # Check if still running
        if psutil.pid_exists(pid):
            os.kill(pid, signal.SIGKILL)
            print(f"Sent SIGKILL to HyperFlow daemon (PID: {pid})")
        
        # Remove PID file
        pid_file = get_pid_file()
        if pid_file.exists():
            pid_file.unlink()
    except ProcessLookupError:
        print("HyperFlow daemon is not running")
        # Remove stale PID file
        pid_file = get_pid_file()
        if pid_file.exists():
            pid_file.unlink()
    except Exception as e:
        print(f"Error stopping daemon: {e}")


def restart_daemon():
    """Restart the HyperFlow daemon"""
    stop_daemon()
    time.sleep(1)
    start_daemon()


def status_daemon():
    """Show status of the HyperFlow daemon"""
    pid = find_daemon_process()
    if pid:
        print(f"HyperFlow daemon is running (PID: {pid})")
    else:
        print("HyperFlow daemon is not running")


def reload_daemon():
    """Reload the HyperFlow daemon configuration"""
    pid = find_daemon_process()
    if not pid:
        print("HyperFlow daemon is not running")
        return
    
    try:
        os.kill(pid, signal.SIGHUP)
        print(f"Sent SIGHUP to HyperFlow daemon (PID: {pid}) to reload configuration")
    except ProcessLookupError:
        print("HyperFlow daemon is not running")
    except Exception as e:
        print(f"Error reloading daemon: {e}")


def main():
    parser = argparse.ArgumentParser(description="HyperFlow CLI - Manage Hyprland automation")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command
    subparsers.add_parser('start', help='Start the HyperFlow daemon')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop the HyperFlow daemon')
    
    # Restart command
    subparsers.add_parser('restart', help='Restart the HyperFlow daemon')
    
    # Status command
    subparsers.add_parser('status', help='Show daemon status')
    
    # Reload command
    subparsers.add_parser('reload', help='Reload daemon configuration')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        start_daemon()
    elif args.command == 'stop':
        stop_daemon()
    elif args.command == 'restart':
        restart_daemon()
    elif args.command == 'status':
        status_daemon()
    elif args.command == 'reload':
        reload_daemon()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()