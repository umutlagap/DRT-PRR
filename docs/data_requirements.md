# Data Requirements for DRT-PRR Model

This document describes the input data requirements for the Digital Risk Twin Post-Disaster Response and Recovery (DRT-PRR) model.

## Overview

The model requires several input files in Excel format (`.xlsx`). All files should be placed in a single data directory.

## Required Files

### 1. Households Data (`households.xlsx`)

Contains information about each household in the simulation.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `H_ID` | Integer | ✓ | Unique household identifier |
| `B_ID` | Integer | ✓ | Building ID where household resides |
| `x_coord` | Float | ✓ | X coordinate of building |
| `y_coord` | Float | ✓ | Y coordinate of building |
| `J_ID` | Integer | ✓ | Job/workplace building ID |
| `R_ID` | Integer |  | Relative's household ID (if any) |
| `closest_hospital_ID` | Integer | ✓ | Nearest hospital ID |
| `closest_school_ID` | Integer | ✓ | Nearest school ID |
| `dist_to_agent_norm` | Float | ✓ | Normalized distance to workplace (0-1) |
| `dist_to_school_norm` | Float | ✓ | Normalized distance to school (0-1) |
| `dist_to_hospital_norm` | Float | ✓ | Normalized distance to hospital (0-1) |
| `employment` | Integer |  | Employment status: 0 (unemployed), 1 (employed) |
| `income` | Float |  | Income level: 0.5 (low), 1.0 (high) |
| `liquid` | Float |  | Access to savings: 0.5 (no), 1.0 (yes) |
| `Tenure` | String |  | Housing tenure: "Ownership", "Rental", "Rent-free" |
| `Households` | Integer |  | Number of households in building |
| `closest_1` to `closest_10` | Integer |  | IDs of 10 closest buildings |

**Notes:**
- Normalized distances should be calculated as: `distance / max_distance` where `max_distance` is the maximum distance in the study area
- Default values are applied if optional columns are missing:
  - `employment`: 1 (employed)
  - `income`: 1.0 (high)
  - `liquid`: 1.0 (has savings)
  - `Tenure`: "Ownership"

### 2. Recovery Monitoring Data (`recovery_monitoring.xlsx`)

Contains building recovery status over time.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `ID_1` | Integer | ✓ | Building identifier |
| `Land_use` | String |  | Land use type: "Formal", "Informal", "Commercial" |
| `YYYY_MM` | Integer | ✓ | Recovery status for each month (0 = damaged, 1 = functional) |

**Example columns:** `2013_09`, `2013_10`, `2013_11`, ..., `2017_11`

**Notes:**
- Month columns should follow the format `YYYY_MM`
- Values must be binary: 0 (not functional) or 1 (functional)
- The simulation starts from the first month column specified

### 3. Shelters Data (`shelters.xlsx`)

Contains emergency shelter locations.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `ID_1` | Integer | ✓ | Shelter identifier |
| `x_coord` | Float | ✓ | X coordinate |
| `y_coord` | Float | ✓ | Y coordinate |
| `capacity` | Integer |  | Maximum household capacity (default: 2) |

### 4. Schools Data (`schools.xlsx`)

Contains school locations.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `ID_1` | Integer | ✓ | School identifier |
| `x_coord` | Float | ✓ | X coordinate |
| `y_coord` | Float | ✓ | Y coordinate |

### 5. Hospitals Data (`hospitals.xlsx`)

Contains hospital locations.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `ID_1` | Integer | ✓ | Hospital identifier |
| `x_coord` | Float | ✓ | X coordinate |
| `y_coord` | Float | ✓ | Y coordinate |

### 6. New Buildings Data (`new_buildings.xlsx`)

Contains newly constructed buildings during recovery.

| Column | Type | Description |
|--------|------|-------------|
| `ID_1` | Integer | Building identifier |
| `x_coord` | Float | X coordinate |
| `y_coord` | Float | Y coordinate |
| `Land_use` | String | Land use type |
| `closest_school_ID` | Integer | Nearest school |
| `closest_hospital_ID` | Integer | Nearest hospital |
| `dist_to_school` | Float | Distance to school |
| `dist_to_hospital` | Float | Distance to hospital |

### 7. New Jobs Data (`new_jobs.xlsx`)

Contains new employment opportunities.

| Column | Type | Description |
|--------|------|-------------|
| `J_ID` | Integer | Job identifier |
| `x_coord` | Float | X coordinate |
| `y_coord` | Float | Y coordinate |
| `Land_use` | String | Associated land use |
| `closest_agent_1` to `closest_agent_10` | Integer | IDs of nearest households |

### 8. New Buildings Recovery (`new_buildings_recovery.xlsx`)

Recovery timeline for new buildings.

| Column | Type | Description |
|--------|------|-------------|
| `ID_1` | Integer | Building identifier |
| `YYYY_MM` | Integer | Functionality status per month |

## Coordinate System

- All coordinates should use the same coordinate reference system (CRS)
- The model uses Euclidean distances for calculations

## Data Preparation Steps

1. **Geocode buildings**: Ensure all buildings have accurate coordinates
2. **Calculate distances**: Pre-calculate normalized distances to services
3. **Identify neighbors**: Pre-calculate 10 closest buildings for each household
4. **Assign attributes**: Distribute socio-economic attributes based on census data
5. **Prepare recovery timeline**: Create monthly functionality status from damage and recovery assessments

## Data Validation

Before running the simulation, validate your data:

```python
from drt_prr import load_data, validate_data

data = load_data(
    households_path="data/households.xlsx",
    recovery_path="data/recovery_monitoring.xlsx",
    shelters_path="data/shelters.xlsx",
    schools_path="data/schools.xlsx",
    hospitals_path="data/hospitals.xlsx"
)

validate_data(data)  # Raises ValueError if validation fails
```

