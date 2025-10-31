#!/usr/bin/env python3
"""
HyperFlow: Hyprland Visual Automation Assistant
Main entry point
"""

import sys
import os
from pathlib import Path

# Add the hyperflow module to the path
sys.path.append(str(Path(__file__).parent))

def show_help():
    print("""
HyperFlow: Hyprland Visual Automation Assistant

Usage:
  python main.py [command]

Commands:
  daemon    Run the HyperFlow daemon
  editor    Launch the HyperFlow GUI editor
  cli       Use the command-line interface
  
For CLI usage:
  python main.py cli [subcommand]
  
Subcommands for CLI:
  start     Start the HyperFlow daemon
  stop      Stop the HyperFlow daemon
  restart   Restart the HyperFlow daemon
  status    Show daemon status
  reload    Reload daemon configuration
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == "daemon":
        # Run the daemon
        from hyperflow.daemon import HyperFlowDaemon
        daemon = HyperFlowDaemon()
        daemon.run()
        
    elif command == "editor":
        # Launch the GUI editor
        from hyperflow.editor import main as editor_main
        editor_main()
        
    elif command == "cli":
        # Use the CLI interface
        from hyperflow.cli import main as cli_main
        # Pass the remaining arguments to the CLI
        sys.argv = sys.argv[1:]  # Shift arguments
        cli_main()
        
    else:
        show_help()

if __name__ == "__main__":
    main()
