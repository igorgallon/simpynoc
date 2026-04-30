# NoC Simulator with Tkinter GUI

## Setup

No additional dependencies needed! Tkinter comes with Python.

## Usage

### Option 1: Using the GUI (Recommended)

1. **Start the Tkinter GUI:**
```bash
cd simpynoc/scr
python gui.py
```

2. **Configure your simulation parameters** using the GUI tabs:
   - **Network Tab**: Set mesh size (rows/columns)
   - **Simulation Tab**: Set simulation steps and buffer size
   - **Traffic Tab**: Configure traffic range and number of steps
   - **Routing & Files Tab**: Select routing algorithms and input files
   - **Summary Tab**: View and verify all configuration parameters

3. **Save or Run**:
   - Click **"Save Configuration"** to save without running
   - Click **"Load Configuration"** to load a previously saved config
   - Click **"Run Simulation"** to save config and get instructions

4. **Run the saved configuration:**
```bash
python main.py --config simulation_config.json
```

### Option 2: Command Line with Config File

1. Create a `simulation_config.json` file:
```json
{
  "mesh_size": [8, 8],
  "simulation_steps": 1000,
  "max_flits_per_node": 1500,
  "traffic_steps": 30,
  "traffic_start": 0.0,
  "traffic_end": 0.15,
  "application_file": "embedded_app_graphs/mpeg4.app",
  "mapping_file": "simpynoc/mpeg4_mapping.map",
  "routing_algorithms": ["XY", "NEGATIVE_FIRST"]
}
```

2. Run with the config:
```bash
python main.py --config simulation_config.json
```

### Option 3: Default (No GUI)

Run with default parameters:
```bash
python main.py
```

## GUI Features

### 🌐 Network Tab
- Mesh size configuration (2x2 to 16x16)
- Real-time display of selected dimensions

### ⚙️ Simulation Tab
- Simulation steps (100 to 10,000 cycles)
- Max flits per node buffer (100 to 5,000)
- Real-time value display

### 📈 Traffic Tab
- Number of traffic injection steps (5 to 100)
- Traffic range start and end (0% to 150%)
- Real-time percentage display

### 🛣️ Routing & Files Tab
- Checkboxes for 4 routing algorithms
- Application file dropdown
- Mapping file text input with browse button

### 📋 Summary Tab
- Complete configuration preview
- Refresh button to update summary

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mesh_size` | Network dimensions (rows, cols) | [6, 6] |
| `simulation_steps` | Total cycles to simulate | 500 |
| `max_flits_per_node` | Max flits buffered per node | 1000 |
| `traffic_steps` | Number of traffic rate steps | 20 |
| `traffic_start` | Starting traffic rate (%) | 0% |
| `traffic_end` | Ending traffic rate (%) | 5% |
| `application_file` | Path to .app file | embedded_app_graphs/mpeg4.app |
| `mapping_file` | Path to .map file | simpynoc/mpeg4_mapping.map |
| `routing_algorithms` | List of routing algorithms to test | All 4 algorithms |

## Output

After simulation completes:
- Individual analysis plots saved per algorithm
- Comparison plot showing all algorithms
- Configuration displayed on plots
- Statistics summary in console

All results are saved to `simpynoc/simulation_results/<timestamp>/`

## Keyboard Shortcuts

- **Tab**: Navigate between fields
- **Enter**: Submit/Confirm
- **Escape**: Close dialog
