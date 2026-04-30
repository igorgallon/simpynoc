# Maximum number of elements in a income/outcome buffers
MAX_BUFFER_SIZE = 4

LINK_BANDWIDTH = 8 # Maximum bandwidth (flits/cycle)

FLITS_WEIGHT = 1 # Weight of each flit for metrics calculation

NUMBER_OF_CYCLES = 10000 # Total number of cycles for the each simulation

INJECTION_PATTERN = "RANDOM"  # Default injection pattern: "RANDOM", "CONTINUOUS", "UNIFORM", "TRANSPOSE", "HOTSPOT"
ROUTING_ALGORITHM = "XY"  # Default routing algorithm: "XY", "NEGATIVE_FIRST", "WEST_FIRST", "NORTH_LEAST", "ODD_EVEN"
ARBITER_ALGORITHM = "ROUND_ROBIN"  # Default arbiter algorithm: "ROUND_ROBIN"
SELECTION_STRATEGY = "RANDOM"  # Default selection strategy: "BUFFER_LEVEL", "RANDOM"

INJECTION_INTERVAL_SECONDS = 0.7  # Interval between packet injections
RT_SLEEP_THREAD_SECONDS = 0.2
PE_SLEEP_RETRY_SECONDS = 1
PLOTTER_UPDATE_INTERVAL_SECONDS = 10
METRICS_COLLECTOR_INTERVAL_SECONDS = 10

ENABLE_RETRY_MECHANISM = False  # Enable retry mechanism for sending packets when the queue is full
RETRY_LIMIT = 3  # Number of retries for sending packets when the queue is full

DEBUGGER_MODE = False  # Set to True to enable debugging mode