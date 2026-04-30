import sys
import argparse
from pathlib import Path
from clock import get_cycle
from network import Network
from logger import Logger
from metrics import MetricsCollector
from stats import calculate_metrics, plot_all_algorithms_comparison
from config import load_config
import matplotlib.pyplot as plt
from utils import (
    get_linear_list,
    load_application_graph,
    load_tasks_mapping
)

if __name__ == "__main__":
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='NoC Simulator')
    parser.add_argument('--config', type=str, help='Configuration file (JSON)', default=None)
    args = parser.parse_args()
    
    # Load configuration
    cfg = load_config(args.config)
    
    Logger().get_logger().info("Loading the Application Graph...")
    num_tasks, graph = load_application_graph(cfg["application_file"])

    Logger().get_logger().info("Loading tasks mapping...")
    rows, columns, mapping = load_tasks_mapping(cfg["mapping_file"])

    app_name = Path(cfg["application_file"]).stem
    m_name = Path(cfg["mapping_file"]).stem

    # Merge the Application Graphs with the mapping
    # if not graph:
    #     Logger().get_logger().critical("Application graph is empty. Please check the .app file format.")
    #     raise ValueError("Application graph is empty. Please check the .app file format.")
    # if not mapping:
    #     Logger().get_logger().critical("Tasks mapping is empty. Please check the .map file format.")
    #     raise ValueError("Tasks mapping is empty. Please check the .map file format.")
    
    # if rows <= 0 or columns <= 0:
    #     Logger().get_logger().critical("ROWS and COLUMNS must be positive integers.")
    #     raise ValueError("ROWS and COLUMNS must be positive integers.")
    
    # Create the context for the simulation
    context = {
        "simulation_steps": cfg["simulation_steps"],
        "input_traffic_rate": get_linear_list(num_steps=cfg["traffic_steps"], init_pct=cfg["traffic_start"], end_pct=cfg["traffic_end"]),
        "mesh_size": cfg["mesh_size"],
        "max_flits_per_node": cfg["max_flits_per_node"],
        "routing_algorithms": cfg["routing_algorithms"],
        "arbiter_strategy": cfg.get("arbiter_strategy", "ROUND_ROBIN"),
        "topology": cfg.get("topology", "MESH"),
        "injection_strategy": cfg.get("injection_strategy", "LINEAR")
    }

    all_stats = {}  # Store statistics for all routing algorithms

    for r in cfg["routing_algorithms"]:
        Logger().get_logger().info(f"Running simulation with routing algorithm: {r}")
        Logger().get_logger().info("Initializing Mesh Network Simulation...")
        Logger().get_logger().info(f"Configuration: {context}")
        Logger().get_logger().info(f"Using Mapping: {cfg['mapping_file']} with mesh size {context['mesh_size']}")
        Logger().get_logger().info(f"Routing Algorithm: {r}")
        
        mesh_network = Network(context=context, routing_algorithm=r)
        mesh_network.start()
        
        Logger().get_logger().info("Simulation started! Injecting flits...")

        try:
            total_progress = len(context["input_traffic_rate"])
            # Run simulation for each input traffic rate
            for p, traffic in enumerate(context["input_traffic_rate"]):
                
                Logger().get_logger().info(f">>> ({p+1}/{total_progress}) Injecting flits ({round(traffic*100, 2)}%)")
                
                mesh_network.begin_processing()

                flits_injected, cycles_taken = mesh_network.run(injection_rate=traffic, max_flits_per_node=context["max_flits_per_node"], total_cycles=context["simulation_steps"], graph=graph, mapping=mapping)

                Logger().get_logger().info(f"<<< ({p+1}/{total_progress}) Traffic finished in {cycles_taken} cycles")
                MetricsCollector().push_metric({
                    'source': 'simulation',
                    "type": 'simulation_finished',
                    "execution_id": traffic,
                    "weight": get_cycle()
                })
                mesh_network.stop_processing()
        
        finally:
            mesh_network.stop()
            metrics_file = MetricsCollector().save_logs_to_csv(suffix=f"{app_name}_{r.lower()}")
            
            # Analyze statistics (without displaying individual plots yet)
            try:
                Logger().get_logger().info(f"Analyzing statistics for {app_name} mapping...")
                all_stats[r] = calculate_metrics(metrics_file)  # Store for later comparison
                            
            except Exception as e:
                Logger().get_logger().warning(f"Error analyzing statistics for {app_name}: {e}")
            
            del mesh_network
    
    # Create and display comparison plots after all simulations complete
    if all_stats:
        Logger().get_logger().info("Creating comparison plots for all routing algorithms...")
        try:
            fig, comparison_file = plot_all_algorithms_comparison(all_stats, MetricsCollector().get_metrics_folder(), MetricsCollector().simulation_id, context)
            Logger().get_logger().info(f"Comparison plot saved to {comparison_file}")
            
            # Display summary table
            Logger().get_logger().info(f"\n{'='*80}")
            Logger().get_logger().info("FINAL STATISTICS SUMMARY")
            Logger().get_logger().info(f"{'='*80}\n")
            for label, stats in all_stats.items():
                Logger().get_logger().info(f"\n{label}:")
                Logger().get_logger().info(f"  Throughput:   {stats['throughput'].min():.4f} - {stats['throughput'].max():.4f}")
                Logger().get_logger().info(f"  Latency:      {stats['latency_mean'].min():.2f} - {stats['latency_mean'].max():.2f} cycles")
                Logger().get_logger().info(f"  Extra Delay:  {stats['extra_delay'].min():.2f} - {stats['extra_delay'].max():.2f} cycles")
                Logger().get_logger().info(f"  Packet Loss:  {stats['packet_loss'].sum():.0f} total")
            Logger().get_logger().info(f"{'='*80}\n")
            
        except Exception as e:
            Logger().get_logger().warning(f"Error creating comparison plots: {e}")
    sys.exit(0)