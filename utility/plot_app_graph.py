import sys
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt

# Ensure repository root is on sys.path so `from simpynoc.scr import ...` works
# when this script is executed directly (not as a package).
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def read_app(path):
    ntasks = None
    edges = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') and not line.startswith('#[graph]'):
                # capture ntasks
                if line.startswith('#[ntasks]'):
                    continue
                # next line after #[ntasks] is number — handled below if numeric
                try:
                    if ntasks is None and line.isdigit():
                        ntasks = int(line)
                        continue
                except:
                    pass
            if line.startswith('#[graph]'):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                src = int(parts[0]); dst = int(parts[1])
                w = float(parts[2]) if len(parts) > 2 else 1.0
                edges.append((src, dst, w))
    return ntasks, edges

def plot_app(path, out=None):
    ntasks, edges = read_app(path)
    G = nx.DiGraph()
    if ntasks:
        G.add_nodes_from(range(ntasks))
    for s,d,w in edges:
        G.add_edge(s, d, weight=w)
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10,6))
    nx.draw_networkx_nodes(G, pos, node_size=600, node_color='lightblue')
    nx.draw_networkx_labels(G, pos)
    widths = [max(0.5, G[u][v]['weight']/max(1,max(nx.get_edge_attributes(G,'weight').values()))) for u,v in G.edges()]
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=12, width=widths, edge_color='gray')
    edge_labels = {(u,v): f"{d['weight']:.0f}" for u,v,d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    plt.title(path)
    plt.axis('off')
    if out:
        plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python plot_app_graph.py path.app [out.png]')
    else:
        plot_app(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)