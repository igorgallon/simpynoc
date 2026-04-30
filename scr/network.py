import random
from logger import Logger
import threading
from constants import (
    FLITS_WEIGHT,
    ARBITER_ALGORITHM,
    ROUTING_ALGORITHM,
    INJECTION_PATTERN,
    SELECTION_STRATEGY
)
from clock import reset, tick
from metrics import MetricsCollector
from packet import Packet
from router import Router
from processing_element import ProcessingElement

class Network:

    def __init__(self, context, routing_algorithm=ROUTING_ALGORITHM, arbiter_algorithm=ARBITER_ALGORITHM, selection_strategy=SELECTION_STRATEGY):
        '''
        Initializes a Network instance based on the provided context.
            :param context: A dictionary containing network configuration parameters such as mesh size.
        '''
        self.rows, self.columns = context["mesh_size"]
        self.routers = {} # Dictionary to hold routers indexed by their (x, y) coordinates
        self.eps = [] # List to hold processing elements
        # Add start processing event
        self.start_processing = threading.Event()
        self.__execution_id = 0
        self.__setup_mesh(routing_algorithm, arbiter_algorithm, selection_strategy)
    
    
    def __setup_mesh(self, routing_algorithm, arbiter_algorithm, selection_strategy):
        '''
        Creates a network of routers and processing elements based on the specified rows and columns.
        Each router is connected to its neighbors using the X-Y topology and it has a local queue for
        processing elements.
        '''
        # Create routers for each coordinate in the specified rows and columns
        for x in range(self.rows):
            for y in range(self.columns):
                router = Router(x, y, routing_algorithm=routing_algorithm, arbiter_algorithm=arbiter_algorithm, selection_strategy=selection_strategy)
                self.routers[(x, y)] = router
        
        # Set up neighbors based on the X-Y topology
        for (x, y), router in self.routers.items():
            neighbors = {}    
            # Check for neighbors in the four cardinal directions
            if (x, y - 1) in self.routers:
                neighbors["west"] = self.routers[(x, y - 1)].in_queues["east"]
            if (x, y + 1) in self.routers:
                neighbors["east"] = self.routers[(x, y + 1)].in_queues["west"]
            if (x + 1, y) in self.routers:
                neighbors["south"] = self.routers[(x + 1, y)].in_queues["north"]
            if (x - 1, y) in self.routers:
                neighbors["north"] = self.routers[(x - 1, y)].in_queues["south"]
            # Create a processing element for each router at its coordinates
            ep = ProcessingElement(x, y)
            # Set the router's local queue as the processing element's outgoing queue
            ep.set_router_queue(router.in_queues["local"])
            neighbors["local"] = ep.in_router_queue
            # Set the outgoing queues for the router to its neighbors
            router.set_neighbors(neighbors)

            self.eps.append(ep)

        return self.routers, self.eps
    

    def start(self):
        '''
        Initialize Routers and Processing Elements
        '''
        self.__execution_id = 0
        for r in self.routers.values():
            r.start()
        for ep in self.eps:
            ep.start()
    

    def stop(self):
        '''
        Stop Routers and Processing Elements
        '''
        for ep in self.eps:
            ep.stop()
        for r in self.routers.values():
            r.stop()
    

    def begin_processing(self):
        '''
        Set the event to start processing in all routers.
        '''
        for r in self.routers.values():
            r.start()
        for ep in self.eps:
            ep.start()
    
    
    def stop_processing(self):
        '''
        Clear the event to stop processing in all routers.
        '''
        for r in self.routers.values():
            r.stop()
        for ep in self.eps:
            ep.stop()
    

    def run_step(self):
        '''
        Runs a single simulation step by advancing each router and processing element by one cycle.
        '''
        for r in self.routers.values():
            r.run_cycle()
        for ep in self.eps:
            ep.run_cycle()


    def __inject_traffic_continuous(self, injection_rate_per_node):
        """
        Injects traffic into the network continuously based on the specified injection rate per node.
        
        Args:
            injection_rate_per_node: flits/cycle per node (e.g., 0.5 = 1 flit every 2 cycles)
        """
        import random
        
        flits_injected = 0

        for p in self.eps:
            # Generate flits probabilistically based on the injection rate
            if random.random() < injection_rate_per_node:
                # Choose random destination (different from source)
                while True:
                    dst_ep = random.choice(self.eps)
                    if dst_ep.position != p.position:
                        break
                payload = {
                    "execution_id": self.__execution_id,
                    "weight": 1
                }
                packet = Packet(src=p.position, dst=dst_ep.position, payload=payload) # Flit
                
                # Try to inject packet
                if p.inject_packet(packet):
                    flits_injected += 1

        return flits_injected


    def __inject_traffic_random(self):
        """
        Injects a specified total number of flits into the network at random source and destination nodes.
        
        Args:
            total_flits: Total number of flits to inject into the network.
        """
        import random
        
        flits_injected = 0

        payload = {
            "execution_id": self.__execution_id,
            "weight": 1
        }
        
        for p in self.eps:
            # Choose random source and destination (different)
            while True:
                dst_ep = random.choice(self.eps)
                if dst_ep.position != p.position:
                    break

            packet = Packet(src=p.position, dst=dst_ep.position, payload=payload) # Flit
            
            # Try to inject packet
            if p.inject_packet(packet):
                flits_injected += 1

        return flits_injected
    
    def __inject_traffic_mapped_tasks(self, graph, map):
        """
        Injects traffic into the network based on a given task graph and mapping of tasks to processing elements.
        
        Args:
            graph: The task graph.
            map: The mapping of tasks to processing elements.
        """

        flits_injected = 0

        # For each vertex in the graph, inject packets to its neighbors based on the mapping
        for v in graph:
            payload = {
                "execution_id": self.__execution_id,
                "weight": v.get("weight", 1)
            }
            # Get source and destination processing elements based on the mapping
            src_ep = self.eps[map[v["source"]]]
            dst_ep = self.eps[map[v["target"]]]
            # Create packet
            packet = Packet(src=src_ep.position, dst=dst_ep.position, payload=payload) # Flit
            # Try to inject packet
            if src_ep.inject_packet(packet):
                flits_injected += 1

        return flits_injected


    def __inject_traffic_uniform(self, total_flits):
        """
        Injects a specified total number of flits into the network from each node uniformly to random destination nodes.
        
        Args:
            total_flits: Total number of flits to inject per node into the network.
        """
        import random
        
        flits_injected = 0

        payload = {
            "execution_id": self.__execution_id,
            "weight": FLITS_WEIGHT
        }

        for p in self.eps:
            for _ in range(total_flits):
                # Choose random destination (different)
                while True:
                    dst_ep = random.choice(self.eps)
                    if dst_ep.position != p.position:
                        break
                packet = Packet(src=p.position, dst=dst_ep.position, payload=payload) # Flit
            
                # Try to inject packet
                if p.inject_packet(packet):
                    flits_injected += 1

        return flits_injected

    def get_injection_pattern(self):
        algorithm = {
            "RANDOM": self.__inject_traffic_random,
            "CONTINUOUS": self.__inject_traffic_continuous,
            "UNIFORM": self.__inject_traffic_uniform,
            "SHUFFLE": None,
            "TRANSPOSE": None,
            "HOTSPOT": None
        }.get(INJECTION_PATTERN, None)
        if not algorithm:
            raise Exception(f"Injection pattern '{INJECTION_PATTERN}' not implemented!")
        else:
            return algorithm


    def __run_one_cycle(self):
        '''
        Runs a single cycle of the network by advancing each router and processing element by one cycle.
        '''
        for ep in self.eps:
            ep.run_cycle()
        for r in self.routers.values():
            r.run_cycle()
        # Advance global cycle counter (start of cycle)
        tick()
    
    
    def run(self, injection_rate, max_flits_per_node, total_cycles: int=0, graph=None, mapping=None):
        '''
        Runs the network with continuous packet injection at the specified rate for a total number of cycles.
        '''
        # Reset the global cycle counter
        reset()
        self.__execution_id = injection_rate
        num_flits_injected = 0

        if total_cycles <= 0:
            # Inject packets once at the beginning
            total_flits = int(injection_rate * max_flits_per_node)
            num_flits_injected = self.__inject_traffic_uniform(total_flits)
        
            Logger().get_logger().warning(f">>> Waiting for completion of {num_flits_injected} flits ({round(injection_rate*100, 2)}%)")
            # Wait for completion
            all_done = False
            while not all_done:
                self.__run_one_cycle()
                metrics = [m for m in MetricsCollector().get_all_metrics() if m.get('execution_id') == self.__execution_id and (m.get('type') == 'packet_arrived' or m.get('type') == 'packet_loss')]
                flits_caught = sum(m.get("weight", 0) for m in metrics)
                all_done = flits_caught >= num_flits_injected
                Logger().get_logger().info(f"Progress: {flits_caught}/{num_flits_injected} flits ({round(injection_rate*100, 2)}%)")
                total_cycles += 1
        else:
            for _ in range(total_cycles):
                # Generate flits probabilistically based on the injection rate
                if random.random() <= injection_rate:
                    # Inject packets on each cycle
                    total_flits = int(injection_rate * max_flits_per_node)
                    if graph and mapping:
                        num_flits_injected = self.__inject_traffic_mapped_tasks(graph, mapping)
                    else:
                        num_flits_injected = self.__inject_traffic_random()
                self.__run_one_cycle()
        
        # self.__execution_id += 1

        return num_flits_injected, total_cycles
