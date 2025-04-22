# How to Use the Region-Based Floorplan Generator

## Setup and Running

1. **Requirements**:
   - Python 3.6 or higher
   - Required libraries: numpy, matplotlib, PyQt5
   - Install requirements with: `pip install numpy matplotlib PyQt5`

2. **Running the application**:
   ```
   python region_floorplan_ui.py
   ```

## UI Overview

The application window is divided into two main sections:
- Left side: Control panel with settings and parameters
- Right side: Visualization area showing the floorplan

## Step-by-Step Usage Guide

### 1. Setting Algorithm Parameters

In the "Algorithm Parameters" section:
- **Sort Method**: Choose how rooms are prioritized for placement
  - Area: Larger rooms first
  - Adjacency: Rooms with more connections first
  - Hybrid: Combined approach (recommended)
  - Degree-Area: Connection count first, then area
- **Allow Rotations**: Enable/disable room rotation
- **Step Size**: Granularity of position sampling (smaller = more precise)
- **Adjacency Weight**: Importance of maintaining connections (0.1-1.0)
- **Area Weight**: Importance of room size in priority (0.0-0.9)
- **Timeout**: Maximum backtracking time before falling back to greedy approach
- **Algorithm**: Choose between pure greedy or backtracking with greedy fallback

### 2. Quick Setup with Presets

Use preset buttons for quick configuration:
- **Simple**: Basic parameters with Area sorting
- **Optimal**: Hybrid sorting with high adjacency priority (slower but better quality)
- **Adjacency**: Focus on maintaining room connections
- **Speed**: Fast results with slightly lower quality

### 3. Defining Rooms

In the "Room Definitions" section:
- Each row represents a room with name, width, and height
- Add or remove rooms using the buttons
- Default configuration includes 5 basic rooms

### 4. Creating an H-Shaped Layout

In the "Region Definitions" section:
1. Adjust the H-shape parameters:
   - W: Total width of the H-shape
   - H: Total height of the H-shape
   - Corridor: Width of the connecting corridor
2. Click "Apply H-Shape" to generate the regions

### 5. Customizing Regions (Optional)

You can manually adjust regions or add new ones:
- Each region has a name and coordinates (X1,Y1,X2,Y2)
- Add or remove regions using the buttons

### 6. Setting Adjacency Requirements

In the "Adjacency Requirements" section:
1. The matrix shows connection requirements between rooms
2. Check boxes where rooms should be adjacent
3. Quick patterns available:
   - Linear: Chain-like connections
   - Hub: First room connects to all others
   - Grid: Grid-pattern connections

### 7. Generating the Floorplan

1. Click "Generate Floorplan" to start the algorithm
2. The progress bar shows the algorithm status
3. Results appear in the visualization area with:
   - Color-coded rooms with ID numbers
   - Green lines showing satisfied adjacencies
   - Red dotted lines showing unsatisfied adjacencies
   - Statistics on placement success and adjacency satisfaction

## Example Setup (We have shown a specific steup in the demo video, follow that please!!)

1. Use these room definitions:
   - Living Room: 3×4
   - Kitchen: 2×3
   - Dining Room: 2×2
   - Bedroom: 3×3
   - Bathroom: 2×2

2. Create an H-shaped layout with:
   - Width: 15
   - Height: 15
   - Corridor width: 3

3. Set adjacency requirements:
   - Living Room adjacent to Kitchen and Dining Room
   - Bedroom adjacent to Bathroom

4. Use "Hybrid" sort method with:
   - Adjacency Weight: 0.7
   - Area Weight: 0.3
   - Allow Rotations: Checked

5. Click "Generate Floorplan"

## Interpreting Results

- Each room is displayed as a colored rectangle with its ID
- The algorithm attempts to satisfy adjacency requirements while fitting rooms in the defined regions
- Green lines indicate satisfied adjacencies
- Red dotted lines indicate unsatisfied adjacencies
- Statistics show placement success rate and adjacency satisfaction percentage

## Troubleshooting

- If rooms don't fit well, try adjusting their dimensions or the region size
- For better adjacency satisfaction, increase the adjacency weight
- If placement is too slow, increase the step size or reduce timeout
- For complex layouts, the backtracking algorithm may need more time 