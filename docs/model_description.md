# DRT-PRR Model Description

This document provides a detailed description of the Digital Risk Twin Post-Disaster Response and Recovery (DRT-PRR) model following the ODD+D protocol.

## 1. Overview

### 1.1 Purpose

The DRT-PRR model simulates post-disaster household relocation decisions and recovery dynamics. It is designed to:

- **Reproduce observed recovery patterns** following major disasters
- **Test policy scenarios** such as shelter strategies, employment programs, and service restoration
- **Support adaptive decision-making** through continuous data integration
- **Understand household heterogeneity** in recovery outcomes

### 1.2 Entities, State Variables, and Scales

#### Entities

1. **Household Agents**: The primary agents representing individual households
2. **Buildings**: Physical structures including residential, commercial, and service buildings
3. **Services**: Schools and hospitals providing essential services
4. **Shelters**: Emergency accommodation facilities

#### State Variables - Household Agents

| Variable | Type | Description |
|----------|------|-------------|
| `h_id` | Integer | Unique identifier |
| `b_id` | Integer | Current building ID |
| `original_b_id` | Integer | Pre-disaster building ID |
| `x, y` | Float | Current coordinates |
| `employment` | Binary | Employment status (0/1) |
| `income` | Float | Income level (0.5/1.0) |
| `liquid` | Float | Liquidity (0.5/1.0) |
| `tenure` | String | Housing tenure type |
| `satisfaction` | Float | Current satisfaction score |
| `relocation_status` | String | Current relocation state |

#### Spatial and Temporal Scales

- **Spatial**: Building-level resolution within urban boundaries
- **Temporal**: Monthly time steps
- **Typical simulation period**: 48 months (4 years)

### 1.3 Process Overview and Scheduling

Each simulation step (month) follows this sequence:

1. **Environment Update**: Update building recovery status, service functionality
2. **Cache Refresh**: Update functionality caches for efficiency
3. **Agent Activation**: Each agent executes its step in sequence
4. **Data Collection**: Record agent states and distributions

## 2. Design Concepts

### 2.1 Individual Decision Making

Agents make decisions based on a **satisfaction score** calculated as:

```
S = HF × WC × HC × SC
```

Where:
- **HF (Housing Functionality)**: Binary (0 or 1)
- **WC (Work Conditions)**: `(1 - D_work) × Employment`
- **HC (Hospital Conditions)**: `(1 - D_hospital) × H_functionality`
- **SC (School Conditions)**: `(1 - D_school) × S_functionality`

**Decision Rule**: If S < 0.5, agent seeks to improve situation through relocation or job change.

### 2.2 Relocation Options

Agents can choose from these options based on availability and eligibility:

1. **Stay with relatives** (R_ID not null, relative's building functional)
2. **Rent housing** (economic_score ≥ 0.5, rental available)
3. **Move to shelter** (shelter capacity available)
4. **Leave the city** (no other options, or prolonged dissatisfaction)
5. **Move to new building** (new construction available)
6. **Return to original home** (original building recovered)

### 2.3 Social Networks

Each agent has a 9-member social network across three layers:

| Layer | Size | Connection Criteria |
|-------|------|---------------------|
| Spatial | 3 | Nearest neighbors by distance |
| Workplace | 3 | Same job location |
| Economic | 3 | Similar income/education |

Networks facilitate information diffusion about:
- Available rental units
- New job opportunities
- New building availability

### 2.4 Competition for Resources

**Rental Market**:
- Limited rental units based on original renters
- Competition resolved by economic score (FC = E × I × L)
- Higher FC agents outcompete lower FC agents

**Shelter Capacity**:
- Limited shelter spaces with phased activation
- First-come, first-served allocation
- Waiting lists when capacity exceeded

### 2.5 Stochasticity

The model includes controlled stochasticity:

- **Target rate**: 10% cumulative deviation from deterministic outcomes
- **Decision types**: Initial move, job market, return timing, leave city
- **Purpose**: Enable diverse trajectories while maintaining interpretability

## 3. Details

### 3.1 Initialization

1. **Load spatial data**: Buildings, services, shelters
2. **Create agents**: One per household with attributes from data
3. **Build networks**: Spatial neighbors, workplace, economic similarity
4. **Initialize recovery lookup**: Building functionality by month
5. **Calculate pre-disaster satisfaction**: Baseline for comparison

### 3.2 Shelter System

**Capacity Activation Schedule** (based on Typhoon Haiyan data):

| Step | Month | Capacity |
|------|-------|----------|
| 1 | Nov 2013 | 20% |
| 2 | Dec 2013 | 57% |
| 3+ | Jan 2014+ | 100% |

**Evacuation Limits**:

| Step | Capacity |
|------|----------|
| 1 | 4,000 households |
| 2 | 16,000 households |
| 3+ | Unlimited |

### 3.3 Left City System

Agents leave the city when:
1. No shelter available AND no other options
2. Prolonged dissatisfaction (6+ consecutive months with S < 0.5)

**Return Conditions**:
- Original home becomes functional
- New job opportunity discovered
- New building becomes available

### 3.4 Job Market Dynamics

**Job Discovery**:
- Proximity: 10 closest agents to new job location
- Network: Information spreads through social connections

**Job Change**:
- Only high-income pre-disaster agents eligible for new high-income jobs
- Job functionality affects employment status

## 4. Digital Risk Twin Integration

The DRT-PRR model extends traditional ABM through continuous data integration:

### 4.1 Data Streams

- **Satellite imagery**: Building damage, recovery status, and new construction derived from multi-temporal very-high-resolution imagery
- **OpenStreetMap**: Detection and validation of newly constructed buildings and infrastructure changes
- **Census data**: Household socio-economic attributes, including income, tenure type, and employment status

### 4.2 Bidirectional Interaction (Human-in-the-Loop)

The DRT-PRR framework supports bidirectional interaction between the evolving environment and household behaviour, mediated by policy interpretation rather than automated control.

```
Real World Conditions
        ↓
Data Processing & Updating
        ↓
DRT Environment (Damage, Recovery, Services, Jobs)
        ↓
Agent-Based Simulation (Household Decisions)
        ↓
Model Outputs (Displacement, Satisfaction, Spatial Patterns)
        ↓
Policy Interpretation & Scenario Design
        ↓
(Revised interventions tested in the next simulation cycle)

```

### 4.3 Scenario Testing

| Scenario | Description | Key Parameter Changes |
|----------|-------------|----------------------|
| S1 | Baseline | Observed recovery timeline |
| S2 | Adaptive Shelter | Add central shelters at months 6, 14 |
| S3 | Accelerated Housing | 2-year vs 4-year reconstruction |
| S4 | Maintained Services | Services always functional |
| S5 | Employment Enhancement | New factory with 1000 jobs |
| S6 | Cascading Disruption | Hospital closure during recovery |


## 5. References

1. Ghaffarian, S. (2025). Rethinking digital twin: Introducing digital risk twin for disaster risk management.npj Natural Hazards.

2. Ghaffarian, S., Roy, D., Filatova, T., & Kerle, N. (2021). Agent-based modelling of post-disaster recovery with remote sensing data. IJDRR.

3. Müller, B., et al. (2013). Describing human decisions in agent-based models – ODD+D. Environmental Modelling & Software.
