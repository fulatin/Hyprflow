# HyperFlow: Hyprland Visual Automation Assistant

HyperFlow is a visual automation assistant for Hyprland, designed to make window manager automation accessible to everyone. With a simple GUI editor and powerful daemon, you can create complex automation workflows without writing scripts.

## Features

- **Visual Rule Editor**: Create automation rules with a drag-and-drop GUI
- **Real-time Event Processing**: Respond to Hyprland events instantly
- **Flexible Triggers**: Support for various Hyprland events (window open/close, workspace changes, etc.)
- **Conditional Logic**: Apply conditions to fine-tune when actions should execute
- **Extensible Actions**: Execute any shell command, including `hyprctl` commands
- **Hot-reload Configuration**: Reload rules without restarting the daemon
- **Automatic Configuration Monitoring**: Daemon automatically detects changes to workflow.json and reloads configuration
- **Double-click Rule Editing**: Double-click any rule in the editor to quickly edit it

## Installation

1. Clone the repository:
   ```
   git clone https://your-repo-url/hyperflow.git
   cd hyperflow
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

HyperFlow has three main components accessible through the main entry point:

### Running the Daemon

The daemon listens to Hyprland events and executes your automation rules:

```
python main.py daemon
```

### Launching the GUI Editor

Create and edit automation rules with the visual editor:

```
python main.py editor
```

### Using the CLI

Manage the daemon with the command-line interface:

```
python main.py cli [subcommand]
```

Subcommands for CLI:
- `start`: Start the HyperFlow daemon
- `stop`: Stop the HyperFlow daemon
- `restart`: Restart the HyperFlow daemon
- `status`: Show daemon status
- `reload`: Reload daemon configuration

## How It Works

HyperFlow connects to Hyprland's IPC sockets to provide automation capabilities:

1. **Event Listening**: Connects to Hyprland's `.socket2.sock` to receive real-time events
2. **Rule Matching**: Compares events against your configured rules
3. **Action Execution**: Executes commands via `subprocess` when rules match

## Configuration

Rules are stored in `~/.config/hyperflow/workflows.json`. Each rule consists of:

- **Trigger**: What event activates the rule (e.g., `openwindow`)
- **Conditions**: Additional criteria that must be met (e.g., window class equals "spotify")
- **Actions**: Commands to execute when the rule matches (e.g., `hyprctl dispatch movetoworkspace 5`)

Example rule:
```json
{
  "id": "wf_001",
  "name": "Auto-move Spotify to workspace 5",
  "enabled": true,
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
```

Additional example for workspace events:
```json
{
  "id": "wf_002",
  "name": "Set dark theme when switching to Code workspace",
  "enabled": true,
  "trigger": {
    "type": "workspace"
  },
  "conditions": [
    {
      "property": "name",
      "operator": "equals",
      "value": "Code"
    }
  ],
  "actions": [
    {
      "command": "gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'"
    }
  ]
}
```

Advanced example with window title matching:
```json
{
  "id": "wf_003",
  "name": "Auto-floating for file dialogs",
  "enabled": true,
  "trigger": {
    "type": "openwindow"
  },
  "conditions": [
    {
      "property": "title",
      "operator": "contains",
      "value": "Save"
    }
  ],
  "actions": [
    {
      "command": "hyprctl dispatch togglefloating active"
    }
  ]
}
```

### Supported Event Types

HyperFlow supports the following Hyprland event types with their respective properties:

1. `openwindow`/`closewindow`: 
   - `address`: Window address
   - `workspace`: Workspace identifier
   - `class`: Window class
   - `title`: Window title

2. `activewindow`: 
   - `class`: Active window class
   - `title`: Active window title

3. `activewindowv2`: 
   - `address`: Active window address

4. `workspace`: 
   - `name`: Workspace name

5. `workspacev2`: 
   - `name`: Workspace name
   - `id`: Workspace ID

6. `destroyworkspacev2`: 
   - `name`: Workspace name
   - `id`: Workspace ID

7. `windowtitle`: 
   - `address`: Window address

8. `windowtitlev2`: 
   - `address`: Window address
   - `title`: Window title

9. `activelayout`: 
   - `keyboard`: Keyboard identifier
   - `layout`: Layout name

### Supported Condition Operators

- `equals`: Property value equals specified value
- `contains`: Property value contains specified value
- `startswith`: Property value starts with specified value
- `endswith`: Property value ends with specified value
- `greater`: Property value is greater than specified value (numeric)
- `less`: Property value is less than specified value (numeric)

## Auto-start with Hyprland

To automatically start HyperFlow when Hyprland launches, add this to your `hyprland.conf`:

```
exec-once = cd /path/to/hyperflow && source venv/bin/activate && python main.py daemon
```

## Technical Details

### System Architecture

HyperFlow consists of two main components:

1. **HyperFlow Daemon**: A lightweight background service that:
   - Connects to Hyprland's event socket
   - Loads and monitors workflow rules
   - Matches events against rules
   - Executes corresponding actions

2. **HyperFlow Editor**: A GUI application that:
   - Provides visual rule creation and editing
   - Saves rules in JSON format
   - Communicates with the daemon to reload configurations

### Event Debouncing

To prevent performance issues with high-frequency events (like `activewindow`), HyperFlow supports event debouncing. This ensures rules don't trigger too frequently for rapid events.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License