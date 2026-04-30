import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
from logger import Logger
import pandas as pd
from stats import plot_all_algorithms_comparison, calculate_metrics

all_stats = {}

root = "D:/Projects/MCTOR/simpynoc/simulation_results/20260122_110917"

# maps = [
#     # "vopd_onmap",
#     # "vopd_xyadb",
#     # "vopd_mapgraph",
#     # "vopd_nmap",
#     # "vopd_lmap",
#     # "vopd_rmap",
#     # "vopd_ga",
#     # "vopd_sa",
#     # "vopd_castnet",
#     # "vopd_ilp",
#     # "vopd_mapgtom"
#     "XY", "NEGATIVE_FIRST", "WEST_FIRST", "NORTH_LEAST"
# ]

# for m in maps:
#     print(f"Analyzing statistics for mapping: {m}...")
#     df = pd.read_csv(f"{root}/metrics_{m}.csv")
#     df['mapping'] = m.replace("vopd_", "").upper()
#     all_stats[m] = df

# combined_df = pd.concat(all_stats.values(), ignore_index=True)

# combined_df.boxplot(column='latency_mean', by='mapping', figsize=(12, 6), grid=True, showfliers=True)
# plt.title('')
# plt.suptitle('')
# plt.xlabel('Mapping Algorithm')
# plt.ylabel('Mean Latency (cycles)')
# plt.tight_layout()
# plt.savefig(f"{root}/boxplot_latency_comparison.png")
# plt.show()

# combined_df.boxplot(column='throughput', by='mapping', figsize=(12, 6), grid=True, showfliers=True)
# plt.title('')
# plt.suptitle('')
# plt.xlabel('Mapping Algorithm')
# plt.ylabel('Throughput (packets/cycle)')
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.show()

# folder = "20260217_235437"
# metrics_folder = f"simpynoc/simulation_results/{folder}_v3"
# mappings = [
#     f"simpynoc/simulation_results/{folder}/stats_vopd_onmap.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_xyadb.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_mapgraph.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_nmap.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_lmap.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_rmap.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_ga.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_sa.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_castnet.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_ilp.csv",
#     f"simpynoc/simulation_results/{folder}/stats_vopd_mapgtom.csv"
# ]
# os.makedirs(metrics_folder, exist_ok=True)
# for m in mappings:
#     m_name = m.replace(".csv", "").split("/")[-1].replace("metrics_", "").replace("stats_", "").replace("logs_", "")
#     print(f"Analyzing statistics for mapping: {m_name}...")
#     # all_stats[m_name] = calculate_metrics(m)
#     all_stats[m_name] = pd.read_csv(m)

# comparison_file = plot_all_algorithms_comparison(all_stats, metrics_folder=metrics_folder, context=None)

routing_algorithms = ["XY", "NEGATIVE_FIRST", "WEST_FIRST", "NORTH_LAST"]#, "ODD_EVEN"]

# metrics_folder = "simpynoc/simulation_results/20260122_110917" # Exp1
# metrics_folder = "simpynoc/simulation_results/20260217_235437" # Exp2
metrics_folder = "simpynoc/simulation_results/20260319_202625" # Exp2

mappings = {
    "EV": f"{metrics_folder}/stats_EV.csv",
    "DR": f"{metrics_folder}/stats_DR.csv",
    "DS": f"{metrics_folder}/stats_DS.csv",
    "HR": f"{metrics_folder}/stats_HR.csv",
    "HS": f"{metrics_folder}/stats_HS.csv"
    # "vopd_onmap": f"{metrics_folder}/stats_vopd_onmap.csv",
    # "vopd_xyadb": f"{metrics_folder}/stats_vopd_xyadb.csv",
    # "vopd_mapgraph": f"{metrics_folder}/stats_vopd_mapgraph.csv",
    # "vopd_nmap": f"{metrics_folder}/stats_vopd_nmap.csv",
    # "vopd_lmap": f"{metrics_folder}/stats_vopd_lmap.csv",
    # "vopd_rmap": f"{metrics_folder}/stats_vopd_rmap.csv",
    # "vopd_ga": f"{metrics_folder}/stats_vopd_ga.csv",
    # "vopd_sa": f"{metrics_folder}/stats_vopd_sa.csv",
    # "vopd_castnet": f"{metrics_folder}/stats_vopd_castnet.csv",
    # "vopd_ilp": f"{metrics_folder}/stats_vopd_ilp.csv",
    # "vopd_mapgtom": f"{metrics_folder}/stats_vopd_mapgtom.csv"
}

for name, metrics_file in mappings.items():
    # metrics_file = f"{metrics_folder}/metrics_{r}.csv"
    # Analyze statistics (without displaying individual plots yet)
    try:
        print(f"Analyzing statistics for {name}...")
        df = pd.read_csv(metrics_file)
        if isinstance(df, pd.DataFrame):
            all_stats[name] = df
        else:
            print(f"Warning: {name} did not return a DataFrame, skipping.")
    except Exception as e:
        print(f"Error analyzing statistics for {name}: {e}")

# Create and display comparison plots after all simulations complete
if all_stats:
    Logger().get_logger().info("Creating comparison plots for all routing algorithms...")
    try:
        comparison_file = plot_all_algorithms_comparison(all_stats, metrics_folder=f"{metrics_folder}_new", context=None)
        Logger().get_logger().info(f"Comparison plot saved to {comparison_file}")
        
        # Display summary table
        Logger().get_logger().info(f"\n{'='*80}")
        Logger().get_logger().info("FINAL STATISTICS SUMMARY")
        Logger().get_logger().info(f"{'='*80}\n")
        for algo, stats in all_stats.items():
            Logger().get_logger().info(f"\n{algo}:")
            Logger().get_logger().info(f"  Throughput:   {stats['throughput'].min():.4f} - {stats['throughput'].max():.4f}")
            Logger().get_logger().info(f"  Latency:      {stats['latency_mean'].min():.2f} - {stats['latency_mean'].max():.2f} cycles")
            Logger().get_logger().info(f"  Extra Delay:  {stats['extra_delay'].min():.2f} - {stats['extra_delay'].max():.2f} cycles")
            Logger().get_logger().info(f"  Packet Loss:  {stats['packet_loss'].sum():.0f} total")
        Logger().get_logger().info(f"{'='*80}\n")
        
        # Show all comparison plots
        plt.show()
    except Exception as e:
        Logger().get_logger().warning(f"Error creating comparison plots: {e}")

# num_tasks, graph = load_application_graph("embedded_app_graphs/vopd.app")

# Logger().get_logger().info("Loading tasks mapping...")
# rows, columns, mapping = load_tasks_mapping("simpynoc/maps/vopd_castnet.map")
# mesh_size = (rows, columns)
# context = {
#     "simulation_steps": 10000,
#     "input_traffic_rate": get_linear_list(num_steps=20, init_pct=0.0, end_pct=20.0),
#     "mesh_size": mesh_size,
#     "max_flits_per_node": 10,
#     "routing_algorithms": ["XY"]
# }

# mesh_network = Network(context=context, routing_algorithm="XY")
# mesh_network.start()

# mesh_network.inject_traffic_mapped_tasks(graph, mapping)