#!/usr/bin/env python3
"""
HyperFlow Daemon - Backend service for Hyprland automation
Listens to Hyprland events and executes actions based on configured workflows
"""

import asyncio
import os
import subprocess
import json
import signal
import sys
from pathlib import Path


class HyperFlowDaemon:
    def __init__(self):
        # Get Hyprland socket paths
        instance_sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        
        if not instance_sig or not xdg_runtime_dir:
            print("Error: Hyprland environment variables not found")
            sys.exit(1)
            
        # Correct path according to Hyprland Wiki:
        # $XDG_RUNTIME_DIR/hypr/[HIS]/.socket2.sock for events
        # $XDG_RUNTIME_DIR/hypr/[HIS]/.socket.sock for commands
        hypr_base_path = Path(xdg_runtime_dir) / "hypr" / instance_sig
        self.event_socket_path = hypr_base_path / ".socket2.sock"
        self.command_socket_path = hypr_base_path / ".socket.sock"
        
        # Config path
        self.config_path = Path.home() / ".config/hyperflow/workflows.json"
        self.pid_file = Path.home() / ".config/hyperflow/hyperflow.pid"
        
        # Load rules
        self.rules = []
        self.load_rules()
        
        # Event debouncing tracking
        self.last_event_time = {}
        self.debounce_intervals = {}

    def load_rules(self):
        """Load workflow rules from JSON config file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.rules = json.load(f)
                print(f"Loaded {len(self.rules)} rules from {self.config_path}")
            else:
                print(f"Config file not found: {self.config_path}")
                self.rules = []
        except Exception as e:
            print(f"Error loading rules: {e}")
            self.rules = []

    def reload_handler(self, signum, frame):
        """Handle SIGHUP signal to reload rules"""
        print("Reloading rules...")
        self.load_rules()

    def cleanup_handler(self, signum, frame):
        """Handle termination signals to clean up"""
        print("Cleaning up...")
        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()
        sys.exit(0)

    def parse_event(self, event_str):
        """Parse Hyprland event string into structured data"""
        if '>>' not in event_str:
            return None, None
            
        event_type, event_data = event_str.split('>>', 1)
        data_parts = event_data.split(',')
        return event_type, data_parts

    def check_condition(self, condition, event_data, event_type):
        """Check if a condition matches the event data"""
        property_name = condition.get('property')
        operator = condition.get('operator')
        expected_value = condition.get('value')
        
        # Map property names to event data indices based on event type
        # Different event types have different data structures
        property_map = {
            # openwindow/closewindow: address, workspace, class, title
            'openwindow': {
                'address': 0,
                'workspace': 1,
                'class': 2,
                'title': 3
            },
            'closewindow': {
                'address': 0,
                'workspace': 1,
                'class': 2,
                'title': 3
            },
            # activewindow: class, title
            'activewindow': {
                'class': 0,
                'title': 1
            },
            # activewindowv2: address
            'activewindowv2': {
                'address': 0
            },
            # workspace: name
            'workspace': {
                'name': 0
            },
            # workspacev2: name, id
            'workspacev2': {
                'name': 0,
                'id': 1
            },
            # destroyworkspacev2: name, id
            'destroyworkspacev2': {
                'name': 0,
                'id': 1
            },
            # windowtitle: address
            'windowtitle': {
                'address': 0
            },
            # windowtitlev2: address, title
            'windowtitlev2': {
                'address': 0,
                'title': 1
            },
            # activelayout: keyboard, layout
            'activelayout': {
                'keyboard': 0,
                'layout': 1
            }
        }
        
        # Get property mapping for this event type
        event_property_map = property_map.get(event_type, {})
        
        if property_name not in event_property_map:
            return False
            
        index = event_property_map[property_name]
        if index >= len(event_data):
            return False
            
        actual_value = event_data[index]
        
        # Perform comparison based on operator
        if operator == 'equals':
            return actual_value == expected_value
        elif operator == 'contains':
            return expected_value in actual_value
        elif operator == 'startswith':
            return actual_value.startswith(expected_value)
        elif operator == 'endswith':
            return actual_value.endswith(expected_value)
        elif operator == 'greater':
            try:
                return float(actual_value) > float(expected_value)
            except ValueError:
                return False
        elif operator == 'less':
            try:
                return float(actual_value) < float(expected_value)
            except ValueError:
                return False
                
        return False

    def should_execute_rule(self, rule, event_type, event_data):
        """Determine if a rule should be executed based on event and conditions"""
        # Check if rule is enabled
        if not rule.get('enabled', True):
            return False
            
        # Check trigger type
        trigger = rule.get('trigger', {})
        if trigger.get('type') != event_type:
            return False
            
        # Check debounce
        rule_id = rule.get('id', '')
        debounce_ms = trigger.get('debounce', 0)
        if debounce_ms > 0:
            current_time = asyncio.get_event_loop().time()
            last_time = self.last_event_time.get(rule_id, 0)
            if current_time - last_time < debounce_ms / 1000:
                return False
            self.last_event_time[rule_id] = current_time
        
        # Check conditions
        conditions = rule.get('conditions', [])
        for condition in conditions:
            if not self.check_condition(condition, event_data, event_type):
                return False
                
        return True

    def execute_actions(self, rule):
        """Execute all actions defined in a rule"""
        actions = rule.get('actions', [])
        for action in actions:
            command = action.get('command')
            if command:
                try:
                    print(f"Executing: {command}")
                    subprocess.run(command, shell=True)
                except Exception as e:
                    print(f"Error executing command '{command}': {e}")

    def process_event(self, event_str):
        """Process an incoming event and check against all rules"""
        event_type, event_data = self.parse_event(event_str)
        if not event_type or not event_data:
            return
            
        print(f"Processing event: {event_type} with data {event_data}")
        
        # Check all rules
        for rule in self.rules:
            if self.should_execute_rule(rule, event_type, event_data):
                print(f"Rule '{rule.get('name', 'unnamed')}' matched. Executing actions.")
                self.execute_actions(rule)

    async def listen_to_events(self):
        """Listen to Hyprland event socket and process events"""
        try:
            reader, writer = await asyncio.open_unix_connection(str(self.event_socket_path))
            print("Connected to Hyprland event socket.")
        except Exception as e:
            print(f"Failed to connect to Hyprland event socket: {e}")
            return
            
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                event_str = line.decode().strip()
                self.process_event(event_str)
        except Exception as e:
            print(f"Error reading from socket: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def run(self):
        """Run the daemon"""
        # Setup signal handlers
        signal.signal(signal.SIGHUP, self.reload_handler)
        signal.signal(signal.SIGTERM, self.cleanup_handler)
        signal.signal(signal.SIGINT, self.cleanup_handler)
        
        # Create config directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Create default config if it doesn't exist
        if not self.config_path.exists():
            default_config = [
                {
                    "id": "wf_001",
                    "name": "Auto-move Spotify to workspace 5",
                    "enabled": True,
                    "trigger": {
                        "type": "openwindow",
                        "debounce": 100
                    },
                    "conditions": [
                        {
                            "property": "class",
                            "operator": "equals",
                            "value": "spotify"
                        }
                    ],
                    "actions": [
                        {
                            "command": "hyprctl dispatch movetoworkspace 5"
                        }
                    ]
                }
            ]
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config at {self.config_path}")
            self.load_rules()
        
        print("HyperFlow daemon started. Send SIGHUP to reload rules.")
        try:
            asyncio.run(self.listen_to_events())
        except KeyboardInterrupt:
            print("Received interrupt signal, shutting down...")
        finally:
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()


if __name__ == "__main__":
    daemon = HyperFlowDaemon()
    daemon.run()