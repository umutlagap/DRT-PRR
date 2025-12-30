"""
Configuration parameters for the DRT-PRR model.

This file contains all configurable parameters for the Digital Risk Twin
Post-Disaster Response and Recovery model.
"""

# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

# Satisfaction threshold - agents with S < threshold will seek relocation
SATISFACTION_THRESHOLD = 0.5

# Stochasticity control - target cumulative deviation from deterministic behavior
TARGET_STOCHASTICITY = 0.10

# Random seed for reproducibility (set to None for truly random)
RANDOM_SEED = None

# =============================================================================
# SHELTER SYSTEM PARAMETERS
# =============================================================================

# Default capacity per shelter unit (households per shelter)
DEFAULT_SHELTER_CAPACITY = 1

# Total number of emergency shelter units
TOTAL_SHELTER_UNITS = 20000

# Shelter activation schedule (proportion of total capacity by simulation step)
# Based on post-Typhoon Haiyan data where 57% capacity met by early January
SHELTER_ACTIVATION_SCHEDULE = {
    1: 0.20,   # Step 1 (Nov 2013): 20% capacity
    2: 0.57,   # Step 2 (Dec 2013): 57% capacity  
    3: 1.00,   # Step 3+ (Jan 2014+): 100% capacity
}

# =============================================================================
# EVACUATION SYSTEM PARAMETERS
# =============================================================================

# Evacuation capacity limits by simulation step
# Based on ~1,000 households/day peak departure rate post-Haiyan
EVACUATION_LIMITS = {
    1: 4000,           # Step 1: Limited evacuation capacity
    2: 16000,          # Step 2: Expanded capacity
    3: float('inf'),   # Step 3+: Unlimited
}

# =============================================================================
# ECONOMIC PARAMETERS
# =============================================================================

# Income levels
INCOME_HIGH = 1.0
INCOME_LOW = 0.5

# Employment status
EMPLOYED = 1
UNEMPLOYED = 0

# Liquidity levels (access to savings/grants)
LIQUIDITY_HIGH = 1.0
LIQUIDITY_LOW = 0.5

# Economic threshold for rental affordability
RENTAL_ECONOMIC_THRESHOLD = 0.5

# =============================================================================
# SERVICE FUNCTIONALITY PARAMETERS
# =============================================================================

# Minimum functionality score for non-functional services
# (services still provide some value even when damaged)
MIN_SERVICE_FUNCTIONALITY = 0.5

# Housing functionality is binary (0 = damaged, 1 = functional)
HOUSING_FUNCTIONALITY_DAMAGED = 0
HOUSING_FUNCTIONALITY_FUNCTIONAL = 1

# =============================================================================
# SOCIAL NETWORK PARAMETERS
# =============================================================================

# Number of connections per network layer
SPATIAL_NEIGHBORS_COUNT = 3
WORKPLACE_CONNECTIONS_COUNT = 3
ECONOMIC_SIMILARITY_COUNT = 3

# Total network size per agent
TOTAL_NETWORK_SIZE = (SPATIAL_NEIGHBORS_COUNT + 
                      WORKPLACE_CONNECTIONS_COUNT + 
                      ECONOMIC_SIMILARITY_COUNT)

# Number of closest buildings to track for each household
CLOSEST_BUILDINGS_COUNT = 10

# =============================================================================
# JOB MARKET PARAMETERS
# =============================================================================

# Number of closest agents for job proximity discovery
JOB_PROXIMITY_AGENTS = 10

# =============================================================================
# STOCHASTIC DECISION WEIGHTS
# =============================================================================

# Default weight ranges for different decision types
# Adjust these parameters to sum to TARGET_STOCHASTICITY
DECISION_WEIGHT_RANGES = {
    'initial_move_choice': (0, 0),
    'job_market_decisions':  (0, 0),
    'return_decision_timing':  (0, 0),
    'leave_city_decision':  (0, 0),
    'shelter_preference_decision':  (0, 0),
}

# =============================================================================
# LEFT CITY SYSTEM PARAMETERS
# =============================================================================

# Number of consecutive months of low satisfaction before leaving city
MONTHS_BEFORE_LEAVE_CITY = None

# =============================================================================
# OUTPUT PARAMETERS
# =============================================================================

# Output directory for simulation results
OUTPUT_DIR = "output_steps"

# File names for output files
OUTPUT_FILES = {
    'longitudinal_csv': 'longitudinal_satisfaction_status.csv',
    'longitudinal_xlsx': 'longitudinal_satisfaction_status.xlsx',
    'monthly_status': 'monthly_relocation_status_distribution.xlsx',
    'monthly_status_2': 'monthly_relocation_status_2_distribution.xlsx',
    'rental_composition': 'monthly_rental_composition_by_tenure.xlsx',
    'final_status': 'relocation_status_distribution.xlsx',
    'final_status_2': 'relocation_status_2_distribution.xlsx',
}

# =============================================================================
# CACHE PARAMETERS (for optimized model)
# =============================================================================

# Cache directory
CACHE_DIR = "model_cache"

# Cache version (increment when model structure changes)
CACHE_VERSION = "v2.1"

# Maximum cache size in GB
MAX_CACHE_SIZE_GB = 5.0

# =============================================================================
# VALIDATION PARAMETERS
# =============================================================================

# Enable/disable validation checks during simulation
ENABLE_VALIDATION = True

# Validation frequency (every N steps)
VALIDATION_FREQUENCY = 1

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_shelter_activation(step):
    """Get shelter activation proportion for a given simulation step."""
    if step in SHELTER_ACTIVATION_SCHEDULE:
        return SHELTER_ACTIVATION_SCHEDULE[step]
    return SHELTER_ACTIVATION_SCHEDULE[max(SHELTER_ACTIVATION_SCHEDULE.keys())]


def get_evacuation_limit(step):
    """Get evacuation capacity limit for a given simulation step."""
    if step in EVACUATION_LIMITS:
        return EVACUATION_LIMITS[step]
    return EVACUATION_LIMITS[max(EVACUATION_LIMITS.keys())]


def get_economic_tier(economic_score):
    """Categorize economic score into tiers for network grouping."""
    if economic_score >= 0.75:
        return "high"
    elif economic_score >= 0.375:
        return "medium"
    else:
        return "low"
