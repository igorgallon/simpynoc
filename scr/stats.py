import json
import os
from tkinter import font
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import constants

REGRESSION_LINE_DEGREE = 3

###################################################
# Statistics Calculation Functions
###################################################

def get_throughput(df):
    '''
    Calculate throughput as the number of arrived flits divided by the total cycles taken for each execution_id.
    '''
    cycles = df[df['type'] == 'packet_arrived'].groupby('execution_id').max()['cycles'].reset_index(name='cycles')
    arrived_flit = df[df['type'] == 'packet_arrived'].groupby('execution_id').count()['packet_id'].reset_index(name='arrived_flits')
    stats = pd.merge(cycles, arrived_flit, on='execution_id')
    stats['throughput'] = stats['arrived_flits'] / stats['cycles']
    return stats[['execution_id', 'throughput']]


def get_average_latency(df):
    '''
    Calculate the average latency for each execution_id.
    '''
    df_injected = df[df['type'] == 'packet_sent'].copy()
    # Get the latency mean
    df_arrived = df[df['type'] == 'packet_arrived'].copy()

    df_diff_cycles = pd.merge(
        df_arrived[['packet_id', 'cycles', 'execution_id']],
        df_injected[['packet_id', 'cycles', 'execution_id']],
        on=['packet_id', 'execution_id'],
        suffixes=('_arrived', '_injected')
    )
    df_diff_cycles['cycles'] = df_diff_cycles['cycles_arrived'] - df_diff_cycles['cycles_injected']
    # Get the latency mean
    return df_diff_cycles.groupby(['execution_id']).agg({'cycles': 'mean'}).reset_index().rename(columns={'cycles': 'latency_mean'})


def get_mean_extra_delay(df):
    '''
    Calculate the mean extra delay for each execution_id.
    Extra delay is defined as the difference between the mean latency and the minimum latency for packets of
    the same execution_id.
    '''
    df_injected = df[df['type'] == 'packet_sent'].copy()
    df_arrived = df[df['type'] == 'packet_arrived'].copy()
    
    df_diff_cycles = pd.merge(
        df_arrived[['packet_id', 'cycles', 'execution_id']],
        df_injected[['packet_id', 'cycles', 'execution_id']],
        on=['packet_id', 'execution_id'],
        suffixes=('_arrived', '_injected')
    )
    # Get the latency for each packet
    df_diff_cycles['cycles'] = df_diff_cycles['cycles_arrived'] - df_diff_cycles['cycles_injected']
    # Get min and mean latency per execution_id
    latency_stats = df_diff_cycles.groupby('execution_id')['cycles'].agg(['min', 'mean']).reset_index()
    latency_stats['extra_delay'] = latency_stats['mean'] - latency_stats['min']
    return latency_stats[['execution_id', 'extra_delay']]


def get_packet_loss(df):
    '''
    Calculate packet loss for each execution_id.
    '''
    df_injected = df[df['type'] == 'packet_sent'].copy()
    df_arrived = df[df['type'] == 'packet_arrived'].copy()
    
    df_total_injected = df_injected.groupby('execution_id').size().reset_index(name='total_injected')
    df_total_arrived = df_arrived.groupby('execution_id').size().reset_index(name='total_arrived')

    df_packet_loss = pd.merge(
        df_total_arrived[['execution_id', 'total_arrived']],
        df_total_injected[['execution_id', 'total_injected']],
        on='execution_id'
    )
    df_packet_loss['packet_loss'] = df_packet_loss['total_injected'] - df_packet_loss['total_arrived']
    return df_packet_loss[['execution_id', 'packet_loss']]


###################################################
# Statistics Plotting Functions
###################################################

AXIS_LABEL_FONT_SIZE = 10
LEGEND_FONT_SIZE = 8
FONTWEIGHT = 'normal'

def _plot_throughput_comparison(ax, all_stats, colors, title_fontsize=12, is_individual=False):
    """Helper function to plot throughput comparison"""
    for label, stats in all_stats.items():
        ax.plot(range(len(stats)), stats['throughput'], marker='o', linestyle='-', 
               linewidth=2, label=label, color=colors.get(label))
    if not is_individual:
        ax.set_title('Throughput Comparison', fontsize=title_fontsize, fontweight=FONTWEIGHT)
    ax.set_xlabel('Traffic Rate Index', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.set_ylabel('Throughput (flits/cycle)', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.legend(fontsize=LEGEND_FONT_SIZE)
    ax.grid(True, alpha=0.3)


def _plot_latency_comparison(ax, all_stats, colors, title_fontsize=12, is_individual=False):
    """Helper function to plot latency comparison"""
    for label, stats in all_stats.items():
        ax.plot(range(len(stats)), stats['latency_mean'], marker='s', linestyle='-', 
               linewidth=2, label=label, color=colors.get(label))
    if not is_individual:
        ax.set_title('Average Latency Comparison', fontsize=title_fontsize, fontweight=FONTWEIGHT)
    ax.set_xlabel('Traffic Rate Index', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.set_ylabel('Latency (cycles)', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.legend(fontsize=LEGEND_FONT_SIZE)
    ax.grid(True, alpha=0.3)


def _plot_extra_delay_comparison(ax, all_stats, colors, title_fontsize=12, is_individual=False):
    """Helper function to plot extra delay comparison"""
    for label, stats in all_stats.items():
        ax.plot(range(len(stats)), stats['extra_delay'], marker='^', linestyle='-', 
               linewidth=2, label=label, color=colors.get(label))
    if not is_individual:
        ax.set_title('Extra Delay Comparison', fontsize=title_fontsize, fontweight=FONTWEIGHT)
    ax.set_xlabel('Traffic Rate Index', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.set_ylabel('Extra Delay (cycles)', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.legend(fontsize=LEGEND_FONT_SIZE)
    ax.grid(True, alpha=0.3)


def _plot_packet_loss_comparison(ax, all_stats, colors, title_fontsize=12, is_individual=False):
    """Helper function to plot packet loss comparison"""
    for label, stats in all_stats.items():
        # ax.plot(range(len(stats)), stats['packet_loss'], marker='^', linestyle='-', 
        #        linewidth=2, label=label, color=colors.get(label))
        z = np.polyfit(range(len(stats)), stats['packet_loss'], 2)
        p = np.poly1d(z)
        ax.plot(range(len(stats)), p(range(len(stats))), linestyle='-', linewidth=3, 
               label=label, color=colors.get(label))
    if not is_individual:
        ax.set_title('Packet Loss Comparison', fontsize=title_fontsize, fontweight=FONTWEIGHT)
    ax.set_xlabel('Traffic Rate Index', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.set_ylabel('Lost Packets', fontsize=AXIS_LABEL_FONT_SIZE, fontweight=FONTWEIGHT)
    ax.legend(fontsize=LEGEND_FONT_SIZE)
    ax.grid(True, alpha=0.3)


def __plot_global_average_latency(ax, all_stats, colors, title_fontsize=14, is_individual=False):
    """
    Plot a bar chart with the global average latency for each map.

    all_stats: dict-like mapping name -> stats dataframe (must contain 'latency_mean')
    metrics_folder: folder to save the chart
    Returns the path to the saved image.
    """
    # Compute mean latency per map/label
    means = {}
    for label, stats in all_stats.items():
        if isinstance(stats, pd.DataFrame) and 'latency_mean' in stats.columns:
            means[label] = stats['latency_mean'].mean()
        elif isinstance(stats, (list, tuple, np.ndarray, pd.Series)):
            means[label] = float(np.mean(stats))
        else:
            # skip unknown formats
            continue

    if not means:
        raise ValueError('No latency_mean data found in provided all_stats')

    names = list(means.keys())
    values = [means[n] for n in names]

    bars = ax.bar(range(len(names)), values, color=[colors.get(n, "#7f7f7f") for n in names])

    ax.set_title('Global Average Latency per Map', fontsize=title_fontsize, fontweight='bold')
    ax.set_xlabel('Map')
    ax.set_ylabel('Average Latency (cycles)')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha='right')

    # Annotate bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.2f}", ha='center', va='bottom', fontsize=9)


def __plot_global_average_throughput(ax, all_stats, colors, title_fontsize=14, is_individual=False):

    """
    Plot a bar chart with the global average throughput for each map.

    all_stats: dict-like mapping name -> stats dataframe (must contain 'throughput')
    metrics_folder: folder to save the chart
    Returns the path to the saved image.
    """
    # Compute mean throughput per map/label
    means = {}
    for label, stats in all_stats.items():
        if isinstance(stats, pd.DataFrame) and 'throughput' in stats.columns:
            means[label] = stats['throughput'].mean()
        elif isinstance(stats, (list, tuple, np.ndarray, pd.Series)):
            means[label] = float(np.mean(stats))
        else:
            # skip unknown formats
            continue

    if not means:
        raise ValueError('No throughput data found in provided all_stats')

    names = list(means.keys())
    values = [means[n] for n in names]

    bars = ax.bar(range(len(names)), values, color=[colors.get(n, "#7f7f7f") for n in names])

    ax.set_title('Global Average Throughput per Map', fontsize=title_fontsize, fontweight='bold')
    ax.set_xlabel('Map')
    ax.set_ylabel('Average Throughput (flits/cycle)')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha='right')

    # Annotate bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.4f}", ha='center', va='bottom', fontsize=9)


###################################################
# Utility Functions
###################################################

def save_execution_parameters(context, metrics_folder):
    """
    Save the execution parameters from the context dictionary to a CSV file.
    """
    import os
    p = dict(context)

    os.makedirs(metrics_folder, exist_ok=True)
    params_file = f"{metrics_folder}/execution_parameters.json"
    p["MAX_BUFFER_SIZE"] = constants.MAX_BUFFER_SIZE
    p["INJECTION_PATTERN"] = constants.INJECTION_PATTERN
    p["ARBITER_ALGORITHM"] = constants.ARBITER_ALGORITHM
    p["SELECTION_STRATEGY"] = constants.SELECTION_STRATEGY
    p["RETRY_MECHANISM"] = constants.ENABLE_RETRY_MECHANISM
    p["RETRY_LIMIT"] = constants.RETRY_LIMIT

    json.dump(p, open(params_file, "w"), indent=2)
    
    return params_file


def plot_all_algorithms_comparison(all_stats, metrics_folder, simulation_id, context=None):
    """
    Create comparison plots for all routing algorithms.
    all_stats: dict with routing algorithm names as keys and stats dataframes as values
    context: simulation configuration dictionary
    """
    import tkinter as tk
    
    # Get screen dimensions and calculate adaptive figure size
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    
    # Convert pixels to inches (standard DPI is 100)
    dpi = 100
    fig_width = screen_width / dpi
    fig_height = screen_height / dpi
    
    colors = {
        'XY': '#1f77b4',
        'NEGATIVE_FIRST': '#ff7f0e',
        'WEST_FIRST': '#2ca02c',
        'NORTH_LAST': '#d62728',
        'vopd_onmap': '#1f77b4',
        'vopd_xyadb': '#ff7f0e',
        'vopd_mapgraph': '#2ca02c',
        'vopd_nmap': '#d62728',
        'vopd_lmap': '#9467bd',
        'vopd_rmap': '#8c564b',
        'vopd_ga': '#e377c2',
        'vopd_sa': '#7f7f7f',
        'vopd_castnet': '#bcbd22',
        'vopd_ilp': '#17becf',
        'vopd_mapgtom': '#ff9896',
        'EV': '#1f77b4',
        'DR': '#ff7f0e',
        'DS': '#2ca02c',
        'HR': '#d62728',
        'HS': '#9467bd'
    }
        
    if not os.path.exists(metrics_folder):
        os.makedirs(metrics_folder)
    
    # Save individual plots
    fig_throughput, ax_throughput = plt.subplots(figsize=(12, 7))
    _plot_throughput_comparison(ax_throughput, all_stats, colors, title_fontsize=14, is_individual=True)
    fig_throughput.tight_layout()
    fig_throughput.savefig(f"{metrics_folder}/throughput_comparison.png", dpi=200, bbox_inches='tight')
    plt.close(fig_throughput)
    
    fig_latency, ax_latency = plt.subplots(figsize=(12, 7))
    _plot_latency_comparison(ax_latency, all_stats, colors, title_fontsize=14, is_individual=True)
    fig_latency.tight_layout()
    fig_latency.savefig(f"{metrics_folder}/latency_comparison.png", dpi=200, bbox_inches='tight')
    plt.close(fig_latency)
    
    fig_extra_delay, ax_extra_delay = plt.subplots(figsize=(12, 7))
    _plot_extra_delay_comparison(ax_extra_delay, all_stats, colors, title_fontsize=14, is_individual=True)
    fig_extra_delay.tight_layout()
    fig_extra_delay.savefig(f"{metrics_folder}/extra_delay_comparison.png", dpi=200, bbox_inches='tight')
    plt.close(fig_extra_delay)
    
    fig_packet_loss, ax_packet_loss = plt.subplots(figsize=(12, 7))
    _plot_packet_loss_comparison(ax_packet_loss, all_stats, colors, title_fontsize=14, is_individual=True)
    fig_packet_loss.tight_layout()
    fig_packet_loss.savefig(f"{metrics_folder}/packet_loss_comparison.png", dpi=200, bbox_inches='tight')
    plt.close(fig_packet_loss)

    fig_global_avg_latency, ax_global_avg_latency = plt.subplots(figsize=(12, 7))
    __plot_global_average_latency(ax_global_avg_latency, all_stats, colors, title_fontsize=14, is_individual=True)
    fig_global_avg_latency.tight_layout()
    fig_global_avg_latency.savefig(f"{metrics_folder}/global_average_latency_per_map.png", dpi=200, bbox_inches='tight')
    plt.close(fig_global_avg_latency)
    
    fig_global_avg_throughput, ax_global_avg_throughput = plt.subplots(figsize=(12, 7))
    __plot_global_average_throughput(ax_global_avg_throughput, all_stats, colors, title_fontsize=14, is_individual=True)
    fig_global_avg_throughput.tight_layout()
    fig_global_avg_throughput.savefig(f"{metrics_folder}/global_average_throughput_per_map.png", dpi=200, bbox_inches='tight')
    plt.close(fig_global_avg_throughput)

    # Print a table with mean latency and throughput for each map
    table_data = []
    for label, stats in all_stats.items():
        if isinstance(stats, pd.DataFrame):
            mean_latency = stats['latency_mean'].mean() if 'latency_mean' in stats.columns else float('nan')
            std_latency = stats['latency_mean'].std() if 'latency_mean' in stats.columns else float('nan')
            mean_throughput = stats['throughput'].mean() if 'throughput' in stats.columns else float('nan')
            std_throughput = stats['throughput'].std() if 'throughput' in stats.columns else float('nan')
            table_data.append([label.replace('vopd_', ''), f"{mean_latency:.2f}", f"{std_latency:.2f}", f"{mean_throughput:.4f}", f"{std_throughput:.4f}"])
    table_data.sort(key=lambda x: x[1])  # Sort by mean latency
    # Convert to a Pandas DataFrame for better formatting
    df_table = pd.DataFrame(table_data, columns=['Map', 'Mean Latency (cycles)', 'Latency Std Dev', 'Mean Throughput (flits/cycle)', 'Throughput Std Dev'])
    df_table.set_index('Map', inplace=True)
    # Plot boxplot of latency and throughput
    fig_box, axes_box = plt.subplots(1, 2, figsize=(12, 6))
    latency_data = [stats['latency_mean'] for stats in all_stats.values() if isinstance(stats, pd.DataFrame) and 'latency_mean' in stats.columns]
    throughput_data = [stats['throughput'] for stats in all_stats.values() if isinstance(stats, pd.DataFrame) and 'throughput' in stats.columns]
    axes_box[0].boxplot(latency_data, labels=df_table.index, patch_artist=True)
    axes_box[0].set_title('Latency Distribution per Map', fontsize=14, fontweight='bold')
    axes_box[0].set_xlabel('Map')
    axes_box[1].boxplot(throughput_data, labels=df_table.index, patch_artist=True)
    axes_box[1].set_title('Throughput Distribution per Map', fontsize=14, fontweight='bold')
    axes_box[1].set_xlabel('Map')
    fig_box.tight_layout()
    fig_box.savefig(f"{metrics_folder}/latency_throughput_boxplots.png", dpi=200, bbox_inches='tight')
    plt.close(fig_box)
    # Export to CSV file
    df_table.to_csv(f"{metrics_folder}/mean_latency_throughput_table.csv")
    
    # Create combined 2x2 comparison plot with adaptive size
    fig, axes = plt.subplots(2, 2, figsize=(fig_width, fig_height), dpi=dpi)
    # Plot to combined figure with smaller title font to reduce overlap
    _plot_throughput_comparison(axes[0, 0], all_stats, colors, title_fontsize=10)
    _plot_latency_comparison(axes[0, 1], all_stats, colors, title_fontsize=10)
    _plot_extra_delay_comparison(axes[1, 0], all_stats, colors, title_fontsize=10)
    _plot_packet_loss_comparison(axes[1, 1], all_stats, colors, title_fontsize=10)
    # Use tight_layout to prevent title/label overlap
    plt.tight_layout()
    # Save combined comparison plot
    comparison_file = f"{metrics_folder}/comparison_all_algorithms.png"
    fig.savefig(comparison_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    # Return the figure instead of showing it
    return fig, comparison_file


def calculate_metrics(metrics_file: str):
    """
    Load metrics from CSV, calculate statistics, and returns merged statistics dataframe.
    """
    df = pd.read_csv(metrics_file)
    
    # Calculate all statistics
    throughput = get_throughput(df)
    latency = get_average_latency(df)
    extra_delay = get_mean_extra_delay(df)
    packet_loss = get_packet_loss(df)
    
    # Merge all statistics
    stats = pd.merge(throughput, latency, on='execution_id')
    stats = pd.merge(stats, extra_delay, on='execution_id')
    stats = pd.merge(stats, packet_loss, on='execution_id')

    # Save statistics to CSV for this mapping/algorithm
    stats_file = metrics_file.replace("logs_", "stats_")
    stats.to_csv(stats_file, index=False)
    return stats
