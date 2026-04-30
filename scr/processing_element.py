import queue
import time
from logger import Logger
from clock import get_cycle
from packet import Packet
from metrics import MetricsCollector
from constants import PE_SLEEP_RETRY_SECONDS, MAX_BUFFER_SIZE, RETRY_LIMIT, ENABLE_RETRY_MECHANISM

class ProcessingElement:
    
    def __init__(self, x, y):
        '''
        Initializes a ProcessingElement instance at coordinates (x, y).
        '''
        super().__init__()
        self.x = x # X coordinate of the processing element
        self.y = y # Y coordinate of the processing element
        self.name = f"EP_{x}_{y}"
        self.daemon = True  # Ensures thread exits when main program exits
        self.in_router_queue = queue.Queue(maxsize=MAX_BUFFER_SIZE)  # Queue for incoming from the router
        self.running = True
        self.packets_sent = 0  # Counter for packets sent

    def set_router_queue(self, out_router_queue):
        '''
        Sets the outgoing router queue for the processing element.
        This is called after the processing element is created to establish connection with its router.
            :param out_router_queue: The queue to which packets will be sent.
        '''
        if not isinstance(out_router_queue, queue.Queue):
            raise ValueError("'out_router_queue' must be a queue instance.")
        self.out_router_queue = out_router_queue

    def inject_packet(self, p: Packet):
        '''
        Injects a packet into the processing element.
        '''
        # if p.dst != (self.x, self.y):
        if not self.out_router_queue.full():
            Logger().get_logger().debug(f"> {self.name} Injecting Packet {p.id} S: {(self.x, self.y)} T: {p.dst} W: {p.payload.get('weight')}")
            self.out_router_queue.put(p)
            self.packets_sent += 1
            MetricsCollector().push_metric({
                'source': 'router',
                'id': self.name,
                'type': 'packet_sent',
                'packet_id': p.id,
                'creation_time': p.creation_time,
                'src': p.src,
                'dst': p.dst,
                'cycles': get_cycle(),
                'execution_id': p.payload.get("execution_id"),
                'weight': p.payload.get("weight")
            })
            return True
        else:
            if ENABLE_RETRY_MECHANISM:
                # Retry mechanism
                retry_count = 0
                while retry_count < RETRY_LIMIT:
                    time.sleep(PE_SLEEP_RETRY_SECONDS)
                    Logger().get_logger().debug(f"{self.name} Outgoing queue is full, retrying to inject Packet {p.id}...")
                    if not self.out_router_queue.full():
                        self.out_router_queue.put(p)
                        self.packets_sent += 1
                        MetricsCollector().push_metric({
                            'source': 'router',
                            'id': self.name,
                            'type': 'packet_sent',
                            'packet_id': p.id,
                            'creation_time': p.creation_time,
                            'src': p.src,
                            'dst': p.dst,
                            'cycles': get_cycle(),
                            'execution_id': p.payload.get("execution_id"),
                            'weight': p.payload.get("weight")
                        })
                        return True
                    retry_count += 1
                
                if retry_count >= RETRY_LIMIT:
                    Logger().get_logger().debug(f"{self.name} Failed to inject Packet {p.id} after {retry_count} retries.")
                    MetricsCollector().push_metric({
                        'source': 'router',
                        'id': self.name,
                        'type': 'packet_loss',
                        'packet_id': p.id,
                        'execution_id': p.payload.get("execution_id"),
                        'weight': p.payload.get("weight")
                    })
                
            else:
                Logger().get_logger().debug(f"{self.name} Outgoing queue is full, cannot inject Packet {p.id}.")
                MetricsCollector().push_metric({
                    'source': 'router',
                    'id': self.name,
                    'type': 'packet_loss',
                    'packet_id': p.id,
                    'execution_id': p.payload.get("execution_id"),
                    'weight': p.payload.get("weight")
                })
        
        # else:
        #     Logger().get_logger().error(f"{self.name} Injecting Packet {p.id} to itself is not allowed.")
        
        return False

    def run_cycle(self):
        '''
        Main loop for the processing element thread.
        '''
        try:
            # Wait for a packet from the router's incoming queue
            received = self.in_router_queue.get_nowait()
            # Process the received packet
            Logger().get_logger().debug(f"{self.name} received packet {received.id} from Router {received.src}! W: {received.payload.get('weight')}")
            received.has_arrived()
        
        except queue.Empty:
            pass

    def start(self):
        '''
        Starts the processing element thread.
        '''
        self.packets_sent = 0 # Reset packets sent counter
        with self.in_router_queue.mutex:
            self.in_router_queue.queue.clear()

    def stop(self):
        '''
        Stops the processing element thread.
        '''
        with self.in_router_queue.mutex:
            self.in_router_queue.queue.clear()
        
    @property
    def position(self):
        '''
        Returns the position of the processing element as a tuple (x, y).
        '''
        return (self.x, self.y)