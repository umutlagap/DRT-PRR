"""
Digital Risk Twin for Post-Disaster Response and Recovery (DRT-PRR) Model.

This module contains the main ABM model class that simulates household
movements and recovery dynamics in post-disaster settings.
"""

from mesa import Model
from mesa.time import BaseScheduler
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from collections import defaultdict

from .agent import HouseholdAgent
from .stochastic_manager import StochasticDecisionManager
from . import config


class DTRecoveryModel(Model):
    """
    Agent-Based Model for post-disaster household recovery simulation.
    
    This model simulates household decision-making during post-disaster recovery,
    integrating building damage/recovery data, service functionality, and
    socio-economic factors to model relocation patterns.
    
    Attributes:
        schedule: Mesa scheduler for agent activation
        current_month (str): Current simulation month
        current_step (int): Current simulation step number
        stochastic_manager: Manager for controlled stochasticity
    """
    
    def __init__(self, df_households, df_recovery, month_cols, df_shelters, 
                 df_schools, df_hospitals, df_new_buildings=None, df_new_jobs=None,
                 df_new_buildings_recovery=None):
        """
        Initialize the DRT-PRR model.
        
        Args:
            df_households: DataFrame with household data
            df_recovery: DataFrame with building recovery timelines
            month_cols: List of month column names for simulation
            df_shelters: DataFrame with shelter locations
            df_schools: DataFrame with school locations
            df_hospitals: DataFrame with hospital locations
            df_new_buildings: Optional DataFrame with new building data
            df_new_jobs: Optional DataFrame with new job opportunities
            df_new_buildings_recovery: Optional DataFrame with new buildings recovery
        """
        super().__init__()
        
        # Store input data
        self.df_households = df_households
        self.df_recovery = df_recovery
        self.month_cols = month_cols
        self.df_shelters = df_shelters
        self.df_schools = df_schools
        self.df_hospitals = df_hospitals
        self.df_new_buildings = df_new_buildings if df_new_buildings is not None else pd.DataFrame()
        self.df_new_jobs = df_new_jobs if df_new_jobs is not None else pd.DataFrame()
        self.df_new_buildings_recovery = df_new_buildings_recovery if df_new_buildings_recovery is not None else pd.DataFrame()
        
        # Initialize scheduler
        self.schedule = BaseScheduler(self)
        self.current_month = None
        self.current_step = 0
        
        # Initialize stochastic manager
        self.stochastic_manager = StochasticDecisionManager(
            target_cumulative_stochasticity=config.TARGET_STOCHASTICITY
        )
        
        # Build lookup tables
        self._build_recovery_lookup()
        self._build_new_buildings_lookup()
        self._build_service_structures()
        self._build_shelter_system()
        
        # Initialize tracking structures
        self._initialize_tracking_structures()
        
        # Create agents
        self._create_agents()
        
        # Build spatial and network structures
        self._build_spatial_structures()
        self._build_networks()
        
        # Calculate max service distance for normalization
        self._calculate_max_service_distance()
        
        # Initialize pre-disaster state
        self._initialize_predisaster_state()
        
        # Initialize data collection
        self.longitudinal_data = []
        self.collect_longitudinal = True
        
        print(f"Model initialized with {len(self.schedule.agents)} agents")

    def _build_recovery_lookup(self):
        """Build lookup table for building recovery status."""
        self.recovery_lookup = {}
        self.building_land_use_map = {}
        
        for _, row in self.df_recovery.iterrows():
            b_id = int(row["ID_1"])
            for month in self.month_cols:
                if month in row:
                    self.recovery_lookup[(b_id, month)] = int(row[month])
            
            if 'Land_use' in row:
                self.building_land_use_map[b_id] = row['Land_use']

    def _build_new_buildings_lookup(self):
        """Build lookup tables for new buildings and jobs."""
        self.new_building_lookup = {}
        self.new_buildings_info = {}
        self.new_jobs_info = {}
        self.new_job_locations = {}
        self.job_proximity_map = {}
        
        # New buildings
        if not self.df_new_buildings.empty:
            for _, row in self.df_new_buildings.iterrows():
                b_id = int(row["ID_1"])
                self.new_buildings_info[b_id] = {
                    'id': b_id,
                    'land_use': row.get('Land_use', 'Other'),
                    'x_coord': float(row.get('x_coord', 0)),
                    'y_coord': float(row.get('y_coord', 0)),
                    'closest_school_id': int(row.get('closest_school_ID', 1)),
                    'closest_hospital_id': int(row.get('closest_hospital_ID', 1)),
                    'dist_to_school': float(row.get('dist_to_school', 0)),
                    'dist_to_hospital': float(row.get('dist_to_hospital', 0))
                }
        
        # New jobs
        if not self.df_new_jobs.empty:
            for _, row in self.df_new_jobs.iterrows():
                job_id = int(row["J_ID"])
                self.new_jobs_info[job_id] = {
                    'x_coord': float(row['x_coord']),
                    'y_coord': float(row['y_coord']),
                    'income_level': 'high',
                    'land_use': row.get('Land_use', 'Other')
                }
                self.new_job_locations[job_id] = np.array([
                    float(row['x_coord']), float(row['y_coord'])
                ])
                
                # Pre-calculated closest agents
                closest_agents = []
                for i in range(1, 11):
                    col_name = f"closest_agent_{i}"
                    if col_name in row and not pd.isna(row[col_name]):
                        try:
                            closest_agents.append(int(row[col_name]))
                        except (ValueError, TypeError):
                            continue
                self.job_proximity_map[job_id] = closest_agents[:10]
        
        # New buildings recovery timeline
        if not self.df_new_buildings_recovery.empty:
            for _, row in self.df_new_buildings_recovery.iterrows():
                b_id = int(row["ID_1"])
                for month in self.month_cols:
                    if month in row:
                        self.new_building_lookup[(b_id, month)] = int(row[month])

    def _build_service_structures(self):
        """Build service location structures."""
        # Service ID mappings
        self.hospital_ids = [int(row["ID_1"]) for _, row in self.df_hospitals.iterrows()]
        self.school_ids = [int(row["ID_1"]) for _, row in self.df_schools.iterrows()]
        
        # Service coordinates
        self.school_coords_array = np.array(list(zip(
            self.df_schools["x_coord"], self.df_schools["y_coord"]
        )))
        self.hospital_coords_array = np.array(list(zip(
            self.df_hospitals["x_coord"], self.df_hospitals["y_coord"]
        )))
        self.shelter_coords_array = np.array(list(zip(
            self.df_shelters["x_coord"], self.df_shelters["y_coord"]
        )))
        
        # Coordinate dictionaries
        self.school_coords_dict = {
            self.school_ids[i]: self.school_coords_array[i]
            for i in range(len(self.school_ids))
        }
        self.hospital_coords_dict = {
            self.hospital_ids[i]: self.hospital_coords_array[i]
            for i in range(len(self.hospital_ids))
        }
        
        # KD-trees for efficient nearest-neighbor queries
        self.school_kdtree = cKDTree(self.school_coords_array)
        self.hospital_kdtree = cKDTree(self.hospital_coords_array)
        self.shelter_kdtree = cKDTree(self.shelter_coords_array)

    def _build_shelter_system(self):
        """Initialize shelter capacity management."""
        self.shelter_capacity = {}
        self.shelter_occupancy = {}
        self.total_shelter_capacity = config.TOTAL_SHELTER_UNITS * config.DEFAULT_SHELTER_CAPACITY
        self.current_shelter_occupancy = 0
        
        for i in range(len(self.shelter_coords_array)):
            self.shelter_capacity[i] = config.DEFAULT_SHELTER_CAPACITY
            self.shelter_occupancy[i] = 0
        
        # Evacuation tracking
        self.monthly_evacuations = {}

    def _initialize_tracking_structures(self):
        """Initialize all tracking dictionaries."""
        self.occupied_new_buildings = set()
        self.occupied_jobs = set()
        self.building_to_agents = defaultdict(list)
        self.building_coords = {}
        self.building_capacity = {}
        self.building_closest_10 = {}
        self.rental_units = {}
        self.occupied_rental_units = set()
        self.available_rental_units = set()
        self.temporary_rentals = {}
        
        # Statistics tracking
        self.left_city_stats = {
            'total_departures': 0,
            'total_returns': 0,
            'return_reasons': defaultdict(int)
        }
        self.job_market_stats = {
            'total_job_changes': 0,
            'proximity_discoveries': 0,
            'network_discoveries': 0
        }
        self.monthly_distributions = {
            'relocation_status': {},
            'relocation_status_2': {}
        }
        
        # Caches
        self.job_functionality_cache = {}
        self.new_job_functionality_cache = {}
        self.service_functionality_cache = {}
        self.spatial_neighbors = {}
        self.nearest_shelter_cache = {}

    def _create_agents(self):
        """Create household agents from data."""
        self.household_dict = {}
        coords = []
        self.job_networks = defaultdict(list)
        self.economic_networks = defaultdict(list)
        
        for _, row in self.df_households.iterrows():
            h_id = int(row["H_ID"])
            if h_id in self.household_dict:
                continue
            
            agent = HouseholdAgent(h_id, self, row)
            agent.building_land_use = self.building_land_use_map.get(agent.b_id, "Other")
            
            self.schedule.add(agent)
            self.household_dict[h_id] = agent
            coords.append([agent.x, agent.y])
            
            # Register in networks
            self.job_networks[agent.job_id].append(h_id)
            self.building_to_agents[agent.b_id].append(h_id)
            self.building_coords[agent.b_id] = (agent.x, agent.y)
            
            economic_tier = config.get_economic_tier(agent.economic_score)
            self.economic_networks[economic_tier].append(h_id)
            
            # Building capacity
            if agent.b_id not in self.building_capacity:
                self.building_capacity[agent.b_id] = int(row.get("Households", 1))
                self.building_closest_10[agent.b_id] = agent.closest_buildings
            
            # Rental units
            rental_unit_id = f"{agent.b_id}_{agent.h_id}"
            self.rental_units[rental_unit_id] = {
                'building_id': agent.b_id,
                'coord': (agent.x, agent.y),
                'original_tenure': agent.original_tenure,
                'original_occupant_id': h_id if agent.tenure == "Rental" else None
            }
            if agent.tenure == "Rental":
                self.occupied_rental_units.add(rental_unit_id)
        
        self.coords_array = np.array(coords)

    def _build_spatial_structures(self):
        """Build spatial data structures."""
        self.kdtree = cKDTree(self.coords_array)
        self.hid_to_index = {agent.h_id: i for i, agent in enumerate(self.schedule.agents)}
        self.index_to_hid = {i: agent.h_id for i, agent in enumerate(self.schedule.agents)}
        
        # Pre-compute spatial neighbors
        all_coords = np.array([agent.original_coord for agent in self.schedule.agents])
        _, indices = self.kdtree.query(all_coords, k=config.SPATIAL_NEIGHBORS_COUNT + 1)
        
        for i, agent in enumerate(self.schedule.agents):
            neighbor_ids = [self.index_to_hid[idx] for idx in indices[i] 
                           if self.index_to_hid[idx] != agent.h_id]
            self.spatial_neighbors[agent.h_id] = neighbor_ids[:config.SPATIAL_NEIGHBORS_COUNT]
        
        # Pre-compute nearest shelters
        _, shelter_indices = self.shelter_kdtree.query(all_coords)
        for i, agent in enumerate(self.schedule.agents):
            self.nearest_shelter_cache[agent.h_id] = shelter_indices[i]

    def _build_networks(self):
        """Build social networks for agents."""
        for agent in self.schedule.agents:
            network = []
            
            # Spatial neighbors
            network.extend(self.spatial_neighbors.get(agent.h_id, [])[:3])
            
            # Workplace connections
            workplace_peers = [h for h in self.job_networks[agent.job_id] if h != agent.h_id]
            network.extend(workplace_peers[:3])
            
            # Economic similarity
            economic_tier = config.get_economic_tier(agent.economic_score)
            economic_peers = [h for h in self.economic_networks[economic_tier] if h != agent.h_id]
            network.extend(economic_peers[:3])
            
            agent.network = list(set(network))

    def _calculate_max_service_distance(self):
        """Calculate maximum service distance for normalization."""
        all_coords = np.array([agent.original_coord for agent in self.schedule.agents])
        max_dist = 0
        
        if len(self.school_coords_array) > 0:
            school_dists = self.school_kdtree.query(all_coords)[0]
            max_dist = max(max_dist, school_dists.max())
        
        if len(self.hospital_coords_array) > 0:
            hospital_dists = self.hospital_kdtree.query(all_coords)[0]
            max_dist = max(max_dist, hospital_dists.max())
        
        self.max_service_distance = max_dist if max_dist > 0 else 1.0

    def _initialize_predisaster_state(self):
        """Initialize pre-disaster satisfaction values."""
        for agent in self.schedule.agents:
            agent.original_satisfaction = agent.calc_satisfaction_fast(use_original_location=True)
            agent.satisfaction = agent.original_satisfaction

    def advance(self, month):
        """
        Advance the simulation by one month.
        
        Args:
            month (str): The month to simulate (e.g., "2013_11")
        """
        self.current_month = month
        self.current_step += 1
        
        # Update caches
        self._update_functionality_caches()
        self._update_available_rentals()
        
        # Execute agent steps
        self.schedule.step()
        
        # Collect data
        self._collect_step_data()
        self._record_monthly_distributions()

    def _update_functionality_caches(self):
        """Update functionality caches for current month."""
        # Job functionality
        for agent in self.schedule.agents:
            job_b_id = agent.job_id
            self.job_functionality_cache[job_b_id] = self.recovery_lookup.get(
                (job_b_id, self.current_month), 1
            )
        
        # New job functionality
        for job_id in self.new_jobs_info:
            self.new_job_functionality_cache[job_id] = self.new_building_lookup.get(
                (job_id, self.current_month), 0
            )
        
        # Service functionality
        for school_id in self.school_ids:
            func = self.recovery_lookup.get((school_id, self.current_month), 1)
            self.service_functionality_cache[('school', school_id, self.current_month)] = (
                1.0 if func == 1 else config.MIN_SERVICE_FUNCTIONALITY
            )
        
        for hospital_id in self.hospital_ids:
            func = self.recovery_lookup.get((hospital_id, self.current_month), 1)
            self.service_functionality_cache[('hospital', hospital_id, self.current_month)] = (
                1.0 if func == 1 else config.MIN_SERVICE_FUNCTIONALITY
            )

    def _update_available_rentals(self):
        """Update available rental units based on recovery status."""
        for rental_unit_id, unit_info in self.rental_units.items():
            if rental_unit_id in self.occupied_rental_units:
                continue
            
            building_id = unit_info['building_id']
            is_functional = self.recovery_lookup.get((building_id, self.current_month), 0) == 1
            
            if is_functional:
                self.available_rental_units.add(rental_unit_id)
            else:
                self.available_rental_units.discard(rental_unit_id)

    def find_shelter_for_agent(self, agent):
        """
        Find available shelter for an agent.
        
        Args:
            agent: The agent seeking shelter
            
        Returns:
            tuple: (shelter_id, shelter_coord) or None if no shelter available
        """
        # Check capacity limit
        active_capacity = self.get_active_shelter_capacity(self.current_month)
        if self.current_shelter_occupancy >= active_capacity:
            return None
        
        # Find nearest shelter with capacity
        agent_coord = agent.coord.reshape(1, -1)
        distances, indices = self.shelter_kdtree.query(agent_coord, k=len(self.shelter_coords_array))
        
        for idx in indices[0]:
            if self.shelter_occupancy[idx] < self.shelter_capacity[idx]:
                self.shelter_occupancy[idx] += 1
                self.current_shelter_occupancy += 1
                return idx, tuple(self.shelter_coords_array[idx])
        
        return None

    def get_active_shelter_capacity(self, month):
        """Get active shelter capacity for a given month."""
        activation = config.get_shelter_activation(self.current_step)
        return int(self.total_shelter_capacity * activation)

    def can_evacuate_agent(self, month):
        """Check if evacuation is possible this month."""
        limit = config.get_evacuation_limit(self.current_step)
        current = self.monthly_evacuations.get(month, 0)
        return current < limit

    def record_agent_evacuation(self, month):
        """Record an agent evacuation."""
        self.monthly_evacuations[month] = self.monthly_evacuations.get(month, 0) + 1

    def find_available_rental_for_agent(self, agent):
        """
        Find available rental unit for an agent.
        
        Args:
            agent: The agent seeking rental
            
        Returns:
            tuple: (rental_unit_id, building_coord) or None
        """
        if not self.available_rental_units:
            return None
        
        # Find nearest available rental
        available_list = list(self.available_rental_units)
        best_rental = None
        best_distance = float('inf')
        
        for rental_id in available_list:
            unit_info = self.rental_units[rental_id]
            coord = np.array(unit_info['coord'])
            distance = np.linalg.norm(agent.coord - coord)
            
            if distance < best_distance:
                best_distance = distance
                best_rental = (rental_id, unit_info['coord'])
        
        return best_rental

    def find_available_new_building(self, agent):
        """
        Find available new building for an agent.
        
        Args:
            agent: The agent seeking housing
            
        Returns:
            dict: Building info or None
        """
        for b_id, info in self.new_buildings_info.items():
            if b_id in self.occupied_new_buildings:
                continue
            
            is_functional = self.new_building_lookup.get((b_id, self.current_month), 0) == 1
            if is_functional:
                return info
        
        return None

    def handle_temporary_renter_departure(self, agent):
        """Handle cleanup when temporary renter leaves."""
        if agent.temporary_rental_original_owner:
            if agent.temporary_rental_original_owner in self.temporary_rentals:
                del self.temporary_rentals[agent.temporary_rental_original_owner]

    def _collect_step_data(self):
        """Collect longitudinal data for current step."""
        if not self.collect_longitudinal:
            return
        
        for agent in self.schedule.agents:
            self.longitudinal_data.append({
                'H_ID': agent.h_id,
                'Step': self.current_step,
                'Month': self.current_month,
                'Satisfaction': agent.satisfaction,
                'Relocation_Status': agent.relocation_status,
                'Relocation_Status_2': agent.relocation_status_2,
                'X': agent.x,
                'Y': agent.y,
                'Building_ID': agent.b_id,
                'Economic_Score': agent.economic_score,
                'Employment': agent.employment,
                'Income': agent.income,
                'Land_Use': agent.building_land_use
            })

    def _record_monthly_distributions(self):
        """Record distribution of statuses for current month."""
        status_counts = {}
        status_2_counts = {}
        
        for agent in self.schedule.agents:
            status_counts[agent.relocation_status] = status_counts.get(agent.relocation_status, 0) + 1
            if agent.relocation_status_2:
                status_2_counts[agent.relocation_status_2] = status_2_counts.get(agent.relocation_status_2, 0) + 1
        
        self.monthly_distributions['relocation_status'][self.current_month] = status_counts
        self.monthly_distributions['relocation_status_2'][self.current_month] = status_2_counts

    def export_collected_longitudinal_data(self):
        """
        Export collected longitudinal data to DataFrame.
        
        Returns:
            pd.DataFrame: Longitudinal data for all agents across all steps
        """
        if not self.longitudinal_data:
            return None
        
        df = pd.DataFrame(self.longitudinal_data)
        return df

    def get_summary_statistics(self):
        """
        Get summary statistics for the simulation.
        
        Returns:
            dict: Summary statistics
        """
        total_agents = len(self.schedule.agents)
        
        status_counts = {}
        for agent in self.schedule.agents:
            status_counts[agent.relocation_status] = status_counts.get(agent.relocation_status, 0) + 1
        
        return {
            'total_agents': total_agents,
            'current_step': self.current_step,
            'current_month': self.current_month,
            'status_distribution': status_counts,
            'stochasticity': self.stochastic_manager.get_statistics(),
            'left_city_stats': self.left_city_stats,
            'shelter_occupancy': self.current_shelter_occupancy,
            'total_shelter_capacity': self.total_shelter_capacity
        }
