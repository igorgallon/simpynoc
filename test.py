
if __name__ == "__main__":
    
    # run()

    r , c = 4 , 4

    maps = [
        {"name": "onmap",       "map": [3, 5, 4, 11, 2, 6, 12, 15, 1, 7, 9, 13, 0, 8, 10, 14],  "zero_index": True},
        {"name": "xy_adb",      "map": [10, 8, 9, 12, 15, 7, 6, 13, 16, 4, 5, 11, 2, 3, 1, 14], "zero_index": False},
        {"name": "map_graph",   "map": [2, 3, 4, 16, 1, 6, 5, 14, 9, 7, 12, 13, 10, 8, 11, 15], "zero_index": False},
        {"name": "nmap",        "map": [3, 4, 8, 15, 2, 5, 9, 10, 1, 6, 7, 11, 0, 14, 13, 12],  "zero_index": True},
        {"name": "lmap",        "map": [12, 9, 11, 15, 8, 10, 13, 14, 7, 6, 1, 2, 16, 5, 4, 3], "zero_index": False},
        {"name": "rmap",        "map": [13, 14, 15, 11, 7, 10, 8, 9, 2, 3, 1, 12, 4, 5, 6, 16], "zero_index": False},
        {"name": "ga",          "map": [3, 4, 2, 1, 16, 5, 11, 15, 7, 6, 12, 13, 8, 10, 9, 14], "zero_index": False},
        {"name": "sa",          "map": [8, 7, 16, 3, 10, 6, 5, 4, 9, 12, 11, 2, 14, 13, 15, 1], "zero_index": False},
        {"name": "castnet",     "map": [16, 4, 3, 2, 6, 5, 11, 1, 7, 9, 12, 15, 8, 10, 13, 14], "zero_index": False},
        {"name": "ilp",         "map": [16, 14, 13, 15, 4, 5, 12, 11, 3, 6, 7, 8, 2, 1, 9, 10], "zero_index": False},
        {"name": "mapgtom",     "map": [8, 10, 13, 14, 7, 9, 11, 15, 6, 5, 12, 1, 16, 4, 3, 2], "zero_index": False},
    ]

    for m in maps:
        crom = [0 for e in range(r * c)]
        idx = 1
        f = 0 if m['zero_index'] else -1
        for i in range(0, r*c, c):
            for j in range(c):
                crom[m['map'][i+j] + f] = idx
                idx += 1

        print(m['name'])
        print(" ".join(map(str, crom)))

    # G = create_task_graph()
    # pos = nx.spectral_layout(G)
    # nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=1200)
    # nx.draw_networkx_edges(G, pos, arrowstyle="-|>", arrowsize=25, edge_color="gray", connectionstyle="arc3,rad=0.2")
    # nx.draw_networkx_labels(G, pos, font_size=16, font_color='black')
    # edge_labels = nx.get_edge_attributes(G, 'volume')
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=12)
    # plt.axis("off")
    # plt.title("APG", fontsize=18)
    # plt.show()