import json
from pathlib import Path

def load_config(config_file=None):
    """Load configuration from JSON file or use defaults"""
    
    project_root = Path(__file__).resolve().parent.parent
    defaults = {
        "mesh_size": (6, 6),
        "simulation_steps": 500,
        "max_flits_per_node": 1000,
        "traffic_steps": 20,
        "traffic_start": 0.0,
        "traffic_end": 0.05,
        "application_file": str(project_root / "embedded_app_graphs" / "mpeg4.app"),
        "mapping_file": str(project_root / "simpynoc" / "maps" / "mpeg4_mapping.map"),
        "routing_algorithms": ["XY", "NEGATIVE_FIRST", "WEST_FIRST", "NORTH_LEAST"],
        "arbiter_strategy": "ROUND_ROBIN",
        "topology": "MESH",
        "injection_strategy": "LINEAR"
    }
    
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                loaded = json.load(f)
            # Convert tuple strings back to tuples if needed
            if isinstance(loaded.get("mesh_size"), list):
                loaded["mesh_size"] = tuple(loaded["mesh_size"])
            for key, value in defaults.items():
                loaded.setdefault(key, value)
            return loaded
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            return defaults
    
    return defaults

def save_config(config, output_file="simulation_config.json"):
    """Save configuration to JSON file"""
    try:
        # Convert tuples to lists for JSON serialization
        config_copy = config.copy()
        if isinstance(config_copy.get("mesh_size"), tuple):
            config_copy["mesh_size"] = list(config_copy["mesh_size"])
        
        with open(output_file, 'w') as f:
            json.dump(config_copy, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
