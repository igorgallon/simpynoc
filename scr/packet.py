import threading
from clock import get_cycle
from datetime import datetime
from logger import Logger
from metrics import MetricsCollector
class Packet:
    
    _id_counter = 0
    _lock = threading.Lock()

    @classmethod
    def next_id(cls):
        '''
        Generates a unique ID for each packet.
        '''
        with cls._lock:
            cls._id_counter += 1
            return cls._id_counter
    

    def __init__(self, src, dst, payload):
        '''
        Initializes a new Packet instance.
            :param src: Source coordinates (x, y) of the packet.
            :param dst: Destination coordinates (x, y) of the packet.
            :param payload: The data payload of the packet.
        '''
        self.id = Packet.next_id()
        self.src = src # Source coordinates (x, y) of the packet
        self.dst = dst # Destination coordinates (x, y) of the packet
        self.payload = payload # Data carried by the packet
        self.hops = 0 # Number of hops the packet has made
        self.creation_time = datetime.now() # Time when the packet was created
        self.deliver_time = 0 # Time when the packet was delivered (0 if not yet delivered)
    

    def has_arrived(self):
        '''
        Marks the packet as arrived by setting the delivery time.
        This method should be called when the packet reaches its destination.
        '''
        Logger().get_logger().debug(f"Packet #{self.id} arrived to {self.dst}! W: {self.payload.get('weight')}")
        self.deliver_time = datetime.now()
        # Log the arrival of the packet
        MetricsCollector().push_metric({
            'source': 'packet',
            'id': self.id,
            'type': 'packet_arrived',
            'packet_id': self.id,
            'src': self.src,
            'dst': self.dst,
            'hops': self.hops,
            'cycles': get_cycle(),
            'creation_time': self.creation_time,
            'deliver_time': self.deliver_time,
            "execution_id": self.payload.get("execution_id"),
            "weight": self.payload.get("weight")
        })

    def __str__(self):
        return f"Packet(id={self.id}, src={self.src}, dst={self.dst}, payload={self.payload}, hops={self.hops}, creation_time={self.creation_time}, deliver_time={self.deliver_time})"