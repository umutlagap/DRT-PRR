"""
Household Agent class for the DRT-PRR model.

This module defines the HouseholdAgent class that represents individual
households in the post-disaster recovery simulation.
"""

from mesa import Agent
import numpy as np
import pandas as pd
from . import config


class HouseholdAgent(Agent):
    """
    A household agent in the post-disaster recovery model.
    
    Each agent represents a household with attributes including location,
    economic status, housing tenure, and access to services. Agents make
    decisions about relocation based on their satisfaction score.
    
    Attributes:
        h_id (int): Unique household identifier
        b_id (int): Current building ID
        original_b_id (int): Pre-disaster building ID
        x, y (float): Current coordinates
        original_x, original_y (float): Pre-disaster coordinates
        employment (int): Employment status (0 or 1)
        income (float): Income level (0.5 or 1.0)
        liquid (float): Liquidity/savings access (0.5 or 1.0)
        tenure (str): Housing tenure type
        satisfaction (float): Current satisfaction score
        relocation_status (str): Current relocation state
    """
    
    def __init__(self, h_id, model, row):
        """
        Initialize a household agent.
        
        Args:
            h_id (int): Unique household identifier
            model: The model instance
            row: DataFrame row with household attributes
        """
        super().__init__(h_id, model)
        self.h_id = h_id
        
        # Location attributes
        self.x = float(row["x_coord"])
        self.y = float(row["y_coord"])
        self.coord = np.array([self.x, self.y])
        self.original_x = self.x
        self.original_y = self.y
        self.original_coord = np.array([self.original_x, self.original_y])
        
        # Building and service IDs
        self.b_id = int(row["B_ID"])
        self.original_b_id = self.b_id
        self.r_id = int(row["R_ID"]) if not pd.isna(row.get("R_ID")) else None
        self.job_id = int(row["J_ID"])
        self.original_job_id = self.job_id
        self.hospital_id = int(row["closest_hospital_ID"])
        self.original_hospital_id = self.hospital_id
        self.school_id = int(row["closest_school_ID"])
        self.original_school_id = self.school_id
        
        # Closest buildings for network
        self.closest_buildings = []
        for i in range(1, config.CLOSEST_BUILDINGS_COUNT + 1):
            closest_col = f"closest_{i}"
            if closest_col in row and not pd.isna(row[closest_col]):
                self.closest_buildings.append(int(row[closest_col]))
        
        # Economic attributes - original values
        self.original_employment = int(row.get("employment", 1))
        self.original_income = float(row.get("income", 1.0))
        self.original_liquid = float(row.get("liquid", 1.0))
        
        # Current economic attributes
        self.employment = self.original_employment
        self.income = self.original_income
        self.liquid = self.original_liquid
        self.economic_score = self.employment * self.income * self.liquid
        
        # Housing tenure
        self.tenure = row.get("Tenure", "Ownership")
        self.original_tenure = self.tenure
        
        # Service distances (normalized 0-1)
        self.original_dist_to_job = float(row.get("dist_to_agent_norm", 0))
        self.original_dist_to_school = float(row.get("dist_to_school_norm", 0))
        self.original_dist_to_hospital = float(row.get("dist_to_hospital_norm", 0))
        self.dist_to_job = self.original_dist_to_job
        self.dist_to_school = self.original_dist_to_school
        self.dist_to_hospital = self.original_dist_to_hospital
        
        # Satisfaction
        self.original_satisfaction = 0
        self.satisfaction = 0
        
        # Movement tracking
        self.has_ever_left_original = False
        self.can_move = True
        self.has_decided_to_return = False
        self.relocation_status = "original"
        self.relocation_status_2 = None
        self.relocation_history = []
        
        # Shelter tracking
        self.shelter_id = None
        self.months_in_shelter = 0
        
        # Rental tracking
        self.rental_unit_id = None
        self.is_temporary_renter = False
        self.temporary_rental_original_owner = None
        
        # New building tracking
        self.new_building_id = None
        self.is_in_new_building = False
        self.moved_to_new_building = False
        
        # Job market tracking
        self.known_jobs = set()
        self.job_change_history = []
        self.eligible_for_high_income_jobs = False
        self.had_high_income_pre_disaster = (self.original_income == 1.0)
        
        # Left city tracking
        self.months_low_satisfaction = 0
        self.has_left_city = False
        self.left_city_month = None
        self.has_left_deterministically = False
        self.deterministic_departure_months = []
        self.departure_location = None
        self.departure_status = None
        self.departure_building_id = None
        
        # Stochasticity tracking
        self.stochastic_decisions_made = []
        
        # Social network
        self.network = []
        
        # Building land use (set after model initialization)
        self.building_land_use = None

    def step(self):
        """Execute one simulation step for this agent."""
        # Update economic status based on job functionality
        self.update_economic_status()
        
        # Calculate current satisfaction
        self.satisfaction = self.calc_satisfaction_fast()
        
        # Handle agents outside city
        if self.relocation_status == "left_city":
            self.evaluate_return_from_outside()
            return
        
        # Handle stuck agents
        if self.relocation_status == "stuck":
            self.try_to_get_unstuck()
            return
        
        # Decision making based on satisfaction
        if self.satisfaction < config.SATISFACTION_THRESHOLD:
            self.months_low_satisfaction += 1
            self.handle_low_satisfaction()
        else:
            self.months_low_satisfaction = 0
            self.handle_satisfied()

    def calc_satisfaction_fast(self, use_original_location=False):
        """
        Calculate satisfaction score efficiently.
        
        The satisfaction score is a multiplicative function of:
        - Housing Functionality (HF): 0 or 1
        - Work Conditions (WC): (1 - dist_to_work) * employment
        - Hospital Conditions (HC): (1 - dist_to_hospital) * functionality
        - School Conditions (SC): (1 - dist_to_school) * functionality
        
        Args:
            use_original_location (bool): If True, calculate for original location
            
        Returns:
            float: Satisfaction score between 0 and 1
        """
        if use_original_location:
            b_id = self.original_b_id
            dist_job = self.original_dist_to_job
            dist_school = self.original_dist_to_school
            dist_hospital = self.original_dist_to_hospital
            school_id = self.original_school_id
            hospital_id = self.original_hospital_id
        else:
            b_id = self.b_id
            dist_job = self.dist_to_job
            dist_school = self.dist_to_school
            dist_hospital = self.dist_to_hospital
            school_id = self.school_id
            hospital_id = self.hospital_id
        
        # Housing Functionality (binary)
        housing_func = self.model.recovery_lookup.get(
            (b_id, self.model.current_month), 1
        )
        
        if housing_func == 0:
            return 0.0
        
        # Work Conditions
        job_func = self.model.job_functionality_cache.get(self.job_id, 1)
        employment_factor = self.employment if job_func == 1 else 0
        work_condition = (1 - dist_job) * employment_factor
        
        if work_condition == 0:
            return 0.0
        
        # Hospital Conditions
        hospital_func = self.model.service_functionality_cache.get(
            ('hospital', hospital_id, self.model.current_month),
            config.MIN_SERVICE_FUNCTIONALITY
        )
        hospital_condition = (1 - dist_hospital) * hospital_func
        
        # School Conditions
        school_func = self.model.service_functionality_cache.get(
            ('school', school_id, self.model.current_month),
            config.MIN_SERVICE_FUNCTIONALITY
        )
        school_condition = (1 - dist_school) * school_func
        
        # Multiplicative satisfaction formula
        satisfaction = housing_func * work_condition * hospital_condition * school_condition
        
        return max(0.0, min(1.0, satisfaction))

    def update_economic_status(self):
        """Update economic status based on job building functionality."""
        job_func = self.model.job_functionality_cache.get(self.job_id, 1)
        
        if job_func == 0:
            self.employment = 0
            self.income = config.INCOME_LOW
        else:
            self.employment = self.original_employment
            job_info = self.model.new_jobs_info.get(self.job_id, {})
            if job_info.get('income_level') == 'high' or self.original_job_id == self.job_id:
                self.income = self.original_income
            else:
                self.income = config.INCOME_HIGH if job_info.get('income_level') == 'high' else config.INCOME_LOW
        
        self.liquid = self.original_liquid
        self.economic_score = self.employment * self.income * self.liquid
        self.eligible_for_high_income_jobs = (
            self.had_high_income_pre_disaster and
            (self.income == config.INCOME_HIGH or
             (self.original_income == config.INCOME_HIGH and self.income == config.INCOME_LOW))
        )

    def handle_low_satisfaction(self):
        """Handle agent with low satisfaction score."""
        # Check if should leave city
        if self.months_low_satisfaction >= config.MONTHS_BEFORE_LEAVE_CITY:
            if not self.has_left_deterministically:
                self.leave_city_deterministically()
                return
        
        # Try to improve situation
        if self.relocation_status == "original":
            self.decide_initial_move()
        else:
            self.evaluate_options()

    def handle_satisfied(self):
        """Handle agent with satisfactory conditions."""
        # If in temporary housing, consider return to original
        if self.relocation_status in ["shelter", "rental", "relative"]:
            original_satisfaction = self.calc_satisfaction_fast(use_original_location=True)
            if original_satisfaction >= config.SATISFACTION_THRESHOLD:
                self.return_to_original()

    def decide_initial_move(self):
        """Make initial relocation decision from original location."""
        self.has_ever_left_original = True
        
        if self.economic_score >= config.RENTAL_ECONOMIC_THRESHOLD:
            rental = self.model.find_available_rental_for_agent(self)
            if rental:
                self.move_to_rental(*rental)
                return
        
        if self.can_move_to_relative():
            self.move_to_relative()
            return
        
        self.go_to_shelter()

    def evaluate_options(self):
        """Evaluate available relocation options."""
        # Check original home
        original_sat = self.calc_satisfaction_fast(use_original_location=True)
        if original_sat >= config.SATISFACTION_THRESHOLD:
            self.return_to_original()
            return
        
        # Check rental options
        if self.economic_score >= config.RENTAL_ECONOMIC_THRESHOLD:
            rental = self.model.find_available_rental_for_agent(self)
            if rental:
                self.move_to_rental(*rental)
                return
        
        # Check new buildings
        if self.model.new_buildings_info:
            new_building = self.model.find_available_new_building(self)
            if new_building:
                self.move_to_new_building(new_building)
                return

    def can_move_to_relative(self):
        """Check if agent can move to relative's home."""
        if self.r_id is None:
            return False
        
        relative = self.model.household_dict.get(self.r_id)
        if relative is None:
            return False
        
        relative_func = self.model.recovery_lookup.get(
            (relative.b_id, self.model.current_month), 0
        )
        return relative_func == 1

    def move_to_rental(self, rental_unit_id, building_coord):
        """Move agent to rental unit."""
        self._leave_current_location()
        
        self.rental_unit_id = rental_unit_id
        self.x, self.y = building_coord
        self.coord = np.array([self.x, self.y])
        
        unit_info = self.model.rental_units[rental_unit_id]
        self.b_id = unit_info['building_id']
        
        self.model.occupied_rental_units.add(rental_unit_id)
        self.model.available_rental_units.discard(rental_unit_id)
        
        self.relocation_status = "rental"
        self.relocation_status_2 = "renting"
        self.relocation_history.append(("rental", self.model.current_month))
        
        self._update_service_distances()

    def move_to_relative(self):
        """Move agent to relative's home."""
        self._leave_current_location()
        
        relative = self.model.household_dict[self.r_id]
        self.x, self.y = relative.x, relative.y
        self.coord = np.array([self.x, self.y])
        self.b_id = relative.b_id
        
        self.relocation_status = "relative"
        self.relocation_status_2 = "with_family"
        self.relocation_history.append(("relative", self.model.current_month))
        
        self._update_service_distances()

    def go_to_shelter(self):
        """Move agent to emergency shelter."""
        shelter_result = self.model.find_shelter_for_agent(self)
        
        if shelter_result is None:
            self.leave_city_due_to_no_shelter()
            return
        
        self._leave_current_location()
        
        shelter_id, shelter_coord = shelter_result
        self.shelter_id = shelter_id
        self.x, self.y = shelter_coord
        self.coord = np.array([self.x, self.y])
        
        self.relocation_status = "shelter"
        self.relocation_status_2 = "in_shelter"
        self.months_in_shelter = 0
        self.relocation_history.append(("shelter", self.model.current_month))
        
        self._update_service_distances()

    def move_to_new_building(self, building_info):
        """Move agent to newly constructed building."""
        self._leave_current_location()
        
        building_id = building_info['id']
        self.new_building_id = building_id
        self.is_in_new_building = True
        self.moved_to_new_building = True
        
        self.x = building_info['x_coord']
        self.y = building_info['y_coord']
        self.coord = np.array([self.x, self.y])
        self.b_id = building_id
        
        self.model.occupied_new_buildings.add(building_id)
        
        self.relocation_status = "new_building"
        self.relocation_status_2 = "in_new_building"
        self.relocation_history.append(("new_building", self.model.current_month))
        
        self._update_service_distances()

    def return_to_original(self):
        """Return agent to original pre-disaster location."""
        self._leave_current_location()
        
        self.x = self.original_x
        self.y = self.original_y
        self.coord = self.original_coord.copy()
        self.b_id = self.original_b_id
        
        self.dist_to_job = self.original_dist_to_job
        self.dist_to_school = self.original_dist_to_school
        self.dist_to_hospital = self.original_dist_to_hospital
        self.school_id = self.original_school_id
        self.hospital_id = self.original_hospital_id
        
        self.relocation_status = "return_back"
        self.relocation_status_2 = "returned_home"
        self.relocation_history.append(("return_back", self.model.current_month))

    def leave_city_deterministically(self):
        """Agent leaves city after prolonged low satisfaction."""
        self._record_departure()
        
        if not self.model.can_evacuate_agent(self.model.current_month):
            self.become_stuck()
            return
        
        self.model.record_agent_evacuation(self.model.current_month)
        self._leave_current_location()
        
        self.relocation_status = "left_city"
        self.relocation_status_2 = "prolonged_dissatisfaction"
        self.has_left_city = True
        self.has_left_deterministically = True
        self.left_city_month = self.model.current_month
        self.deterministic_departure_months.append(self.model.current_month)
        
        self.x, self.y = 0, 0
        self.coord = np.array([0, 0])
        
        self.model.left_city_stats['total_departures'] += 1
        self.relocation_history.append(("left_city", self.model.current_month))

    def leave_city_due_to_no_shelter(self):
        """Agent leaves city because no shelter is available."""
        self._record_departure()
        
        if not self.model.can_evacuate_agent(self.model.current_month):
            self.become_stuck()
            return
        
        self.model.record_agent_evacuation(self.model.current_month)
        self._leave_current_location()
        
        self.relocation_status = "left_city"
        self.relocation_status_2 = "no_shelter_available"
        self.has_left_city = True
        self.left_city_month = self.model.current_month
        
        self.x, self.y = 0, 0
        self.coord = np.array([0, 0])
        
        self.model.left_city_stats['total_departures'] += 1
        self.relocation_history.append(("left_city", self.model.current_month))

    def become_stuck(self):
        """Agent becomes stuck waiting for capacity."""
        self.relocation_status = "stuck"
        self.relocation_status_2 = "waiting_for_capacity"
        self.relocation_history.append(("stuck", self.model.current_month))

    def try_to_get_unstuck(self):
        """Attempt to resolve stuck status."""
        # Try shelter first
        shelter = self.model.find_shelter_for_agent(self)
        if shelter:
            self.go_to_shelter()
            return
        
        # Try evacuation
        if self.model.can_evacuate_agent(self.model.current_month):
            self.model.record_agent_evacuation(self.model.current_month)
            self.relocation_status = "left_city"
            self.relocation_status_2 = "evacuated_after_stuck"
            self.x, self.y = 0, 0
            self.coord = np.array([0, 0])
            self.model.left_city_stats['total_departures'] += 1

    def evaluate_return_from_outside(self):
        """Evaluate if agent outside city should return."""
        # Check original home
        original_func = self.model.recovery_lookup.get(
            (self.original_b_id, self.model.current_month), 0
        )
        if original_func == 1:
            original_sat = self.calc_satisfaction_fast(use_original_location=True)
            if original_sat >= config.SATISFACTION_THRESHOLD:
                self.return_from_outside()
                return
        
        # Check job opportunities
        if self.model.new_jobs_info and self.eligible_for_high_income_jobs:
            for job_id in self.known_jobs:
                if job_id not in self.model.occupied_jobs:
                    job_func = self.model.new_job_functionality_cache.get(job_id, 0)
                    if job_func == 1:
                        self.return_from_outside()
                        return

    def return_from_outside(self):
        """Return to city from outside."""
        self.relocation_status = "return_from_outside"
        self.model.left_city_stats['total_returns'] += 1
        
        # Try to return to original
        original_func = self.model.recovery_lookup.get(
            (self.original_b_id, self.model.current_month), 0
        )
        if original_func == 1:
            self.return_to_original()
        else:
            self.decide_initial_move()

    def _leave_current_location(self):
        """Clean up when leaving current location."""
        if self.relocation_status == "shelter" and self.shelter_id is not None:
            self.model.shelter_occupancy[self.shelter_id] -= 1
            self.shelter_id = None
        
        if self.relocation_status == "rental" and self.rental_unit_id:
            self.model.occupied_rental_units.discard(self.rental_unit_id)
            self.model.available_rental_units.add(self.rental_unit_id)
            self.rental_unit_id = None
        
        if self.is_temporary_renter:
            self.model.handle_temporary_renter_departure(self)
            self.is_temporary_renter = False
            self.temporary_rental_original_owner = None
        
        if self.is_in_new_building and self.new_building_id:
            self.model.occupied_new_buildings.discard(self.new_building_id)
            self.new_building_id = None
            self.is_in_new_building = False

    def _record_departure(self):
        """Record location before leaving city."""
        self.departure_location = (self.x, self.y)
        self.departure_status = self.relocation_status
        self.departure_building_id = self.b_id

    def _update_service_distances(self):
        """Update distances to services after relocation."""
        if self.model.school_coords_dict:
            school_coord = self.model.school_coords_dict.get(self.school_id)
            if school_coord is not None:
                dist = np.linalg.norm(self.coord - school_coord)
                self.dist_to_school = min(1.0, dist / self.model.max_service_distance)
        
        if self.model.hospital_coords_dict:
            hospital_coord = self.model.hospital_coords_dict.get(self.hospital_id)
            if hospital_coord is not None:
                dist = np.linalg.norm(self.coord - hospital_coord)
                self.dist_to_hospital = min(1.0, dist / self.model.max_service_distance)

    def __str__(self):
        return f"HouseholdAgent({self.h_id}, status={self.relocation_status}, sat={self.satisfaction:.3f})"

    def __repr__(self):
        return self.__str__()
