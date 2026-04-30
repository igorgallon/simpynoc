import queue
from clock import get_cycle
from constants import MAX_BUFFER_SIZE, LINK_BANDWIDTH
from logger import Logger
from metrics import MetricsCollector
from packet import Packet
from utils import ROUTING_ALGORITHMS, ARBITER_ALGORITHMS, SELECTION_STRATEGIES
class Router():

    def __init__(self, x, y, routing_algorithm, arbiter_algorithm, selection_strategy):
        '''
        Initializes a Router instance at coordinates (x, y).
        '''
        super().__init__()
        self.x = x # X coordinate of the router
        self.y = y # Y coordinate of the router
        self.name = f"RT_{x}_{y}"
        self.daemon = True  # Ensures thread exits when main program exits
        self.running = True
        self.start_event = None
        self.routing_algorithm = routing_algorithm
        self.arbiter_algorithm = arbiter_algorithm
        self.selection_strategy = selection_strategy
        self.__arbiter_index = 0 # Round-robin arbiter index

        self.__retry_counter = 0

        # Connection queues for incoming packets from neighbors and local endpoints
        self.in_queues = {
            "local": queue.Queue(maxsize=MAX_BUFFER_SIZE),  # Local queue for packets destined to this router.
            "north": queue.Queue(maxsize=MAX_BUFFER_SIZE),  # North neighbor
            "south": queue.Queue(maxsize=MAX_BUFFER_SIZE),  # South neighbor
            "east": queue.Queue(maxsize=MAX_BUFFER_SIZE),   # East neighbor
            "west": queue.Queue(maxsize=MAX_BUFFER_SIZE)    # West neighbor
        }
                
        # Connection queues for outgoing packets to neighbors and local endpoints
        # These will be set by the 'set_neighbors' function
        self.out_queues = {}
        # Bandwidth controller for each direction
        self.bandwidth = {"local": 0, "north": 0, "south": 0, "east": 0, "west": 0}
    

    def set_neighbors(self, out_queues):
        '''
        Sets the outgoing queues for the router to its neighbors and local endpoints.
        This is called after the router is created to establish connections with its neighbors.
            :param out_queues: A dictionary mapping directions to their respective outgoing queues.
        '''
        if not isinstance(out_queues, dict):
            raise ValueError("'out_queues' must be a dictionary mapping directions to queues.")

        self.out_queues = out_queues


    def reset_bandwidth_counters(self) -> None:
        '''
        Reset bandwidth counters at start of cycle - thread safe
        '''
        self.bandwidth = {b: 0 for b in self.bandwidth}
    
    
    def reset_input_queues(self) -> None:
        '''
        Reset input queues - thread safe
        '''
        for q in self.in_queues.values():
            with q.mutex:
                q.queue.clear()
    

    def can_transmit(self, packet: Packet, direction: str) -> bool:
        '''
        (DEPRECATED) Check if bandwidth limit allows transmission - thread safe
        '''
        packet_weight = packet.payload.get("weight", None)

        if packet_weight is not None:
            return (self.bandwidth[direction] + packet_weight <= LINK_BANDWIDTH)
        else:
            Logger().get_logger().critical("Packet weight not specified in payload.")
            raise ValueError("Packet weight not specified in payload.")
    

    def get_routing_direction(self, packet, **kwargs) -> str | list[str]:
        '''
        Routes a packet to the appropriate outgoing queue based on its destination.
        '''
        algorithm = ROUTING_ALGORITHMS.get(self.routing_algorithm, None)
        if algorithm is None:
            raise KeyError(f"Routing algorithm '{self.routing_algorithm}' is not supported.")
        # Call the choosen routing algorithm
        directions = algorithm(self.x, self.y, packet, **kwargs)
        if isinstance(directions, list):
            # Multiple possible directions, apply selection strategy
            return self.get_selection_strategy()(directions)
        else:
            return directions    


    def get_arbiter_direction(self):
        '''
        Returns the next direction from the arbiter.
        '''
        arbiter = ARBITER_ALGORITHMS.get(self.arbiter_algorithm, None)
        if arbiter is None:
            raise KeyError(f"Arbiter algorithm '{self.arbiter_algorithm}' is not supported.")
        # Call the choosen arbiter to retrieve the next buffer and update the arbiter index
        next_direction, self.__arbiter_index = arbiter(self.__arbiter_index)
        return next_direction
    
    
    def get_selection_strategy(self):
        '''
        Returns the selection strategy function.
        '''
        strategy = SELECTION_STRATEGIES.get(self.selection_strategy, None)
        if strategy is None:
            raise KeyError(f"Selection strategy '{self.selection_strategy}' is not supported.")
        return strategy
    

    def run_cycle(self):
        '''
        Main loop for the router thread.
        '''
        next_dir = None
        # Get the next direction from the arbiter
        direction = self.get_arbiter_direction()
        q = self.in_queues[direction]

        try:
            # Get packet from input buffers
            packet = q.get_nowait()
            # If a packet is found, route it to the appropriate outgoing queue
            next_dir = self.get_routing_direction(packet)
            Logger().get_logger().debug(f"{self.name} received packet {packet.id} from {direction}, routing to {next_dir}")
            # If the next direction is valid, put the packet in the corresponding outgoing queue
            if next_dir == "local":
                # Deliver packet to local endpoint
                self.out_queues[next_dir].put_nowait(packet)
                MetricsCollector().push_metric({
                    'source': 'router',
                    'id': self.name,
                    'type': 'packet_routed',
                    'packet_id': packet.id,
                    'from_dir': direction,
                    'to_dir': next_dir,
                    'cycles': get_cycle(),
                    'execution_id': packet.payload.get("execution_id"),
                    'weight': packet.payload.get("weight")
                })
            else:
                packet.hops += 1
                self.out_queues[next_dir].put_nowait(packet)
                # Log the routing of the packet
                MetricsCollector().push_metric({
                    'source': 'router',
                    'id': self.name,
                    'type': 'packet_routed',
                    'packet_id': packet.id,
                    'from_dir': direction,
                    'to_dir': next_dir,
                    'hops': packet.hops,
                    'cycles': get_cycle(),
                    'execution_id': packet.payload.get("execution_id"),
                    'weight': packet.payload.get("weight", None)
                })

        except queue.Full:
            Logger().get_logger().debug(f"Full queue for {next_dir} at {self.name}, cannot transmit packet {packet.id} now. W: {packet.payload.get('weight')}")
            with q.mutex:
                # Undo the hop increment since transmission failed
                packet.hops -= 1
                # Reinsert the packet at the front of the queue. The packet will be retried in the next cycle.
                q.queue.appendleft(packet)
            pass

        except queue.Empty:
            pass

        except Exception as e:
            Logger().get_logger().error(f"Unexpected error in router {self.name} during cycle: {e}")
            Logger().get_logger().error(f"Packet info: {packet}")
            Logger().get_logger().error(f"Direction: {direction}, Next Dir: {next_dir}")
            raise e


    def start(self):
        '''
        Initializes and starts the router thread.
        '''
        self.__arbiter_index = 0
        self.reset_bandwidth_counters()
        self.reset_input_queues()
    

    def stop(self):
        '''
        Stops the router thread.
        '''
        self.reset_bandwidth_counters()        
        self.reset_input_queues()
    
    
    @property
    def position(self):
        '''
        Returns the position of the router as a tuple (x, y).
        '''
        return (self.x, self.y)