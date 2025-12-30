# DRT-PRR: Digital Risk Twin for Post-Disaster Response and Recovery

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Mesa](https://img.shields.io/badge/Mesa-ABM-green.svg)](https://mesa.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-umutlagap-181717?logo=github)](https://github.com/umutlagap/drt-prr)

This repository contains an Agent-Based Model (ABM) designed to simulate post-disaster household movement and recovery dynamics. The model integrates multi-source spatial and socio-economic datasets, including remote sensing–derived damage and recovery information, machine learning–based building classification, and demographic census data. By combining dynamic environmental inputs with household-level decision rules, the framework reproduces observed recovery patterns and enables the evaluation of alternative post-disaster recovery strategies.

## Overview

The DRT-PRR model simulates household-level decision-making during post-disaster recovery, capturing the interaction between evolving environmental conditions and individual household responses. Specifically, the model represents:

- **Household relocation decisions** driven by satisfaction with housing condition, employment access, healthcare availability, and education services
- **Dynamic recovery monitoring** through satellite-derived damage, recovery, and new construction assessments
- **Social network effects** including information diffusion and competition for limited recovery resources
- **Policy-oriented scenario testing** covering adaptive shelter provision, targeted employment generation, service functionality, and housing reconstruction strategies

### Key Features

- **Household agents** with attributes such as income, tenure type, employment status, and location
- **Digital Twin integration** enabling continuous updates of environmental and recovery conditions
- **Bidirectional feedback** between household decisions, the evolving urban environment, and the policy-makers
- **Scenario analysis** supporting both fixed and adaptive recovery interventions
- **Optimized performance** using caching, spatial indexing, and efficient data handling

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/drt-prr.git
cd drt-prr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from drt_prr import DTRecoveryModel, load_data

# Load your data
data = load_data(
    households_path="data/households.xlsx",
    recovery_path="data/recovery_monitoring.xlsx",
    shelters_path="data/shelters.xlsx",
    schools_path="data/schools.xlsx",
    hospitals_path="data/hospitals.xlsx"
)

# Initialize the model
model = DTRecoveryModel(
    df_households=data['households'],
    df_recovery=data['recovery'],
    month_cols=data['month_cols'],
    df_shelters=data['shelters'],
    df_schools=data['schools'],
    df_hospitals=data['hospitals']
)

# Run simulation
for month in data['month_cols']:
    model.advance(month)

# Export results
results = model.export_collected_longitudinal_data()
```

## 📁 Project Structure

```
drt-prr/
├── drt_prr/                    # Main package
│   ├── __init__.py
│   ├── model.py                # Core ABM model
│   ├── agent.py                # Household agent class
│   ├── config.py               # Configuration parameters
│   ├── satisfaction.py         # Satisfaction calculation
│   ├── networks.py             # Social network functions
│   ├── shelter_system.py       # Shelter management
│   ├── job_market.py           # Employment dynamics
│   └── stochastic_manager.py   # Controlled randomness
├── analysis/                   # Analysis scripts
│   ├── aggregate_satisfaction.py
│   └── plot_results.py
├── examples/                   # Example notebooks
│   └── basic_simulation.ipynb
├── data/                       # Data directory (not included)
│   └── README.md
├── docs/                       # Documentation
│   ├── model_description.md
│   └── data_requirements.md
├── requirements.txt
├── setup.py
└── README.md
```

## Model Description

### Satisfaction Function

Household satisfaction is calculated as:

```
S = HF × WC × HC × SC
```

Where:
- **HF** (Housing Functionality): Binary (0 or 1) based on building damage/recovery
- **WC** (Work Conditions): `(1 - D_work) × Employment_Status`
- **HC** (Hospital Conditions): `(1 - D_hospital) × Hospital_Functionality`
- **SC** (School Conditions): `(1 - D_school) × School_Functionality`

Agents with S < 0.5 (satisfaction threshold) initiate relocation decisions.

### Relocation Options

1. **Stay with relatives** (if available and building functional)
2. **Rent housing** (if economically capable)
3. **Move to shelter** (emergency accommodation)
4. **Leave the city** (if no options available)
5. **Move to new building** (newly constructed housing)
6. **Return to original home** (when recovered)
7. **Change job**
8. **Change job and location**

### Social Networks

Each agent has a 9-member social network across three layers:
- **Spatial proximity** (3 nearest neighbors)
- **Workplace connections** (3 coworkers)
- **Economic similarity** (3 agents with similar income/education)

Networks facilitate information diffusion about:
- Rental opportunities
- New job openings
- New building availability

## Configuration

Key parameters in `config.py`:

```python
# Satisfaction threshold for relocation decisions
SATISFACTION_THRESHOLD = 0.5

# Stochasticity target 
TARGET_STOCHASTICITY = 0.10


# Evacuation capacity limits by month
EVACUATION_LIMITS = {
    'month_1': 4000,    # November 2013
    'month_2': 16000,   # December 2013
    'month_3+': float('inf')  # January 2014+
}

# Shelter activation schedule
SHELTER_ACTIVATION = {
    'month_1': 0.20,    # 20% capacity
    'month_2': 0.57,    # 57% capacity
    'month_3+': 1.00    # 100% capacity
}
```

## Scenarios

The model supports multiple policy scenarios:

| Scenario | Description |
|----------|-------------|
| S1 | **Baseline** - Actual recovery trajectory |
| S2 | **Adaptive Shelter** - Centrally located alternative shelters |
| S3 | **Accelerated Housing** - 2-year vs 4-year reconstruction |
| S4 | **Maintained Services** - Full school/hospital functionality |
| S5 | **Employment Enhancement** - New factory with 1000 jobs |
| S6 | **Cascading Disruption** - Hospital closure during recovery |

## Data Requirements

### Input Data Files

1. **Households** (`households.xlsx`)
   - H_ID, B_ID, x_coord, y_coord
   - Employment, income, liquid, tenure
   - Distance to services (normalized)
   - Closest 10 buildings

2. **Recovery Monitoring** (`recovery_monitoring.xlsx`)
   - Building ID
   - Monthly functionality (0/1) columns

3. **Shelters** (`shelters.xlsx`)
   - ID, x_coord, y_coord, capacity

4. **Schools/Hospitals** (`schools.xlsx`, `hospitals.xlsx`)
   - ID, x_coord, y_coord

See `docs/data_requirements.md` for detailed specifications.

## Running Multiple Simulations

For stochastic analysis with multiple runs:

```python
from drt_prr import run_multi_simulation

results = run_multi_simulation(
    num_runs=50,
    base_seed=42,
    output_dir="output_runs"
)

# Results include aggregated statistics across all runs
print(f"Mean returned home: {results['returned_home'].mean()}")
print(f"Std returned home: {results['returned_home'].std()}")
```


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

- **Umut Lagap** - umutlagap@gmail.com or umut.lagap.21@ucl.ac.uk
- Project Link: [https://github.com/umutlagap/DRT-PRR]

