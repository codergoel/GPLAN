# Region-Based Floorplan Generation Algorithm

## Problem Statement

Given a non-rectangular grid boundary (specifically an H-shaped layout in our implementation), place rooms of various dimensions within the boundary while maximizing adjacency satisfaction according to a predefined adjacency graph.

## Our Approach

We developed a region-based placement strategy that combines backtracking and greedy algorithms for optimal room placement.

### Key Components

1. **Region-Based Boundary Definition**
   - The non-rectangular boundary is represented as a collection of overlapping rectangular regions
   - Our implementation focuses on an H-shaped layout with configurable dimensions
   - The H-shape consists of left and right wings connected by a horizontal corridor
   - Additional corner regions provide flexibility for room placement

2. **Room Representation**
   - Each room has a unique ID, dimensions (width and height), and optional name
   - Rooms can be rotated to better fit available spaces
   - Rooms can be ordered based on various criteria (area, adjacency requirements, etc.)

3. **Adjacency Requirements**
   - A graph structure defines which rooms should be adjacent to each other
   - Adjacency is satisfied when rooms share an edge (not just a corner)
   - The algorithm attempts to maximize the satisfaction of these requirements

4. **Hybrid Placement Algorithm**
   - **Initial Approach: Backtracking with Timeout**
     - Attempts to place all rooms while satisfying constraints
     - Uses depth-first search with backtracking
     - Terminates after a configurable timeout to avoid excessive runtime
   
   - **Fallback: Greedy Placement**
     - If backtracking fails or times out, falls back to a greedy approach
     - Places rooms one by one in order of priority
     - For each room, finds the best position based on a scoring function
   
   - **Position Scoring**
     - Positions are scored based on:
       1. Adjacency satisfaction (weighted 80%)
       2. Region fit quality (weighted 20%)
     - This balances maintaining connections with efficient space usage

5. **Position Generation**
   - For rooms with adjacency requirements, generates positions adjacent to already placed rooms
   - For rooms without adjacency requirements or when no adjacent rooms are placed yet, 
     uses grid sampling within each region
   - Rotations are considered to find the best fit

6. **Visualization**
   - Rooms are displayed as colored rectangles with ID numbers
   - Satisfied adjacencies shown as green lines
   - Unsatisfied adjacencies shown as red dotted lines
   - Regions shown as transparent blue rectangles

## Implemented Optimizations

1. **Room Sorting Strategies**:
   - Area-based: Prioritizes larger rooms for placement
   - Adjacency-based: Prioritizes rooms with more connections
   - Hybrid: Weighted combination of area and adjacency
   - Degree-Area: Sort first by number of connections, then by area

2. **Rotation Optimization**:
   - Automatically adjusts room orientation based on region shape
   - For narrow regions, aligns room dimensions with region orientation

3. **Adaptive Step Size**:
   - Configurable granularity for position sampling
   - Smaller steps allow more precise placement but increase runtime

4. **Termination Control**:
   - Configurable timeout for backtracking algorithm
   - Falls back to greedy approach if optimal solution isn't found quickly
