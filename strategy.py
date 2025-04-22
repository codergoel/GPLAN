import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
import random
import math
from collections import defaultdict
import heapq

class Room:
    def __init__(self, room_id, width, height, name=None):
        self.id = room_id
        self.width = width
        self.height = height
        self.x = None
        self.y = None
        self.region = None
        self.rotated = False
        self.name = name if name else f"Room {room_id}"

    def rotate(self):
        self.width, self.height = self.height, self.width
        self.rotated = not self.rotated

    def area(self):
        return self.width * self.height
    
    def perimeter(self):
        return 2 * (self.width + self.height)
        
    def get_rect(self):
        """Return the rectangle as (x, y, width, height)"""
        if self.x is None or self.y is None:
            return None
        return (self.x, self.y, self.width, self.height)
        
    def overlaps(self, other):
        """Check if this room overlaps with another room"""
        if self.x is None or other.x is None:
            return False
            
        return not (self.x + self.width <= other.x or
                   other.x + other.width <= self.x or
                   self.y + self.height <= other.y or
                   other.y + other.height <= self.y)
    
    def is_adjacent(self, other):
        """Check if this room is adjacent to another room"""
        if self.x is None or other.x is None:
            return False
            
        my_rect = self.get_rect()
        other_rect = other.get_rect()
        return are_adjacent(my_rect, other_rect)
    
    def distance_to(self, other):
        """Calculate the center-to-center distance between rooms"""
        if self.x is None or other.x is None:
            return float('inf')
            
        my_center = (self.x + self.width/2, self.y + self.height/2)
        other_center = (other.x + other.width/2, other.y + other.height/2)
        
        dx = my_center[0] - other_center[0]
        dy = my_center[1] - other_center[1]
        return math.sqrt(dx**2 + dy**2)
    
    def get_adjacent_positions(self, other):
        """
        Get potential positions for this room that would be adjacent to the other room.
        Returns a list of (x, y, is_rotated) tuples.
        """
        positions = []
        
        # Try original orientation
        # Left side
        positions.append((other.x - self.width, other.y, False))
        # Right side
        positions.append((other.x + other.width, other.y, False))
        # Top side
        positions.append((other.x, other.y - self.height, False))
        # Bottom side
        positions.append((other.x, other.y + other.height, False))
        
        # Try various offsets along each side to maximize adjacency
        # Left side offsets
        for offset in range(1, min(self.height, other.height)):
            positions.append((other.x - self.width, other.y + offset, False))
            positions.append((other.x - self.width, other.y - offset, False))
        
        # Right side offsets
        for offset in range(1, min(self.height, other.height)):
            positions.append((other.x + other.width, other.y + offset, False))
            positions.append((other.x + other.width, other.y - offset, False))
            
        # Top side offsets
        for offset in range(1, min(self.width, other.width)):
            positions.append((other.x + offset, other.y - self.height, False))
            positions.append((other.x - offset, other.y - self.height, False))
            
        # Bottom side offsets
        for offset in range(1, min(self.width, other.width)):
            positions.append((other.x + offset, other.y + other.height, False))
            positions.append((other.x - offset, other.y + other.height, False))
        
        # If rotation is allowed, add rotated positions
        rotated_room = Room(self.id, self.height, self.width, self.name)
        
        # Left side (rotated)
        positions.append((other.x - rotated_room.width, other.y, True))
        # Right side (rotated)
        positions.append((other.x + other.width, other.y, True))
        # Top side (rotated)
        positions.append((other.x, other.y - rotated_room.height, True))
        # Bottom side (rotated)
        positions.append((other.x, other.y + other.height, True))
        
        # Add offsets for rotated positions
        # Left side offsets (rotated)
        for offset in range(1, min(rotated_room.height, other.height)):
            positions.append((other.x - rotated_room.width, other.y + offset, True))
            positions.append((other.x - rotated_room.width, other.y - offset, True))
        
        # Right side offsets (rotated)
        for offset in range(1, min(rotated_room.height, other.height)):
            positions.append((other.x + other.width, other.y + offset, True))
            positions.append((other.x + other.width, other.y - offset, True))
            
        # Top side offsets (rotated)
        for offset in range(1, min(rotated_room.width, other.width)):
            positions.append((other.x + offset, other.y - rotated_room.height, True))
            positions.append((other.x - offset, other.y - rotated_room.height, True))
            
        # Bottom side offsets (rotated)
        for offset in range(1, min(rotated_room.width, other.width)):
            positions.append((other.x + offset, other.y + other.height, True))
            positions.append((other.x - offset, other.y + other.height, True))
        
        return positions

class PlotRegion:
    def __init__(self, x1, y1, x2, y2, name=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.name = name if name else f"Region ({x1},{y1})-({x2},{y2})"

    def contains(self, room, x, y):
        """Check if the room fits entirely in this region at position (x,y)"""
        return (x >= self.x1 and x + room.width <= self.x2 and
                y >= self.y1 and y + room.height <= self.y2)
                
    def area(self):
        """Calculate the area of this region"""
        return (self.x2 - self.x1) * (self.y2 - self.y1)
    
    def get_rect(self):
        """Return the rectangle as (x, y, width, height)"""
        return (self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1)
    
    def aspect_ratio(self):
        """Calculate the region's aspect ratio (width/height)"""
        width = self.x2 - self.x1
        height = self.y2 - self.y1
        return width / max(height, 0.01)
    
    def is_narrow(self, threshold=0.5):
        """Check if the region is narrow (aspect ratio < threshold or > 1/threshold)"""
        ratio = self.aspect_ratio()
        return ratio < threshold or ratio > 1/threshold
    
    def get_sample_positions(self, room, step_size=1):
        """
        Get a list of sample positions within this region for the room.
        Returns a list of (x, y) tuples.
        """
        positions = []
        x = self.x1
        while x <= self.x2 - room.width:
            y = self.y1
            while y <= self.y2 - room.height:
                positions.append((x, y))
                y += step_size
            x += step_size
        return positions

def are_adjacent(rect1, rect2):
    """
    Check if two rectangles are adjacent (sharing an edge).
    Each rectangle should be (x, y, width, height).
    """
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2

    # Horizontal adjacency (left or right edge)
    if (x1 + w1 == x2 or x2 + w2 == x1):
        # Check if they overlap vertically
        return not (y1 + h1 <= y2 or y2 + h2 <= y1)
    # Vertical adjacency (top or bottom edge)
    elif (y1 + h1 == y2 or y2 + h2 == y1):
        # Check if they overlap horizontally
        return not (x1 + w1 <= x2 or x2 + w2 <= x1)
    
    return False

class RegionBasedPlacement:
    """Class to handle room placement using the region-based strategy"""
    
    def __init__(self, rooms=None, regions=None, adjacency=None):
        """
        Initialize the placement strategy.
        
        Args:
            rooms: List of Room objects
            regions: List of PlotRegion objects
            adjacency: Dictionary mapping room ids to lists of adjacent room ids
        """
        self.rooms = rooms or []
        self.regions = regions or []
        self.adjacency = adjacency or {}
        self.placed_rooms = []
        self.sort_method = "hybrid"  # Default to hybrid sorting
        self.optimize_rotations = True
        self.step_size = 1  # For position sampling
        self.adjacency_weight = 0.7  # Weight for adjacency in hybrid sorting
        self.area_weight = 0.3  # Weight for area in hybrid sorting
        self.max_backtrack = 3  # Maximum number of backtracking attempts
        self.use_adjacency_driven = True  # Whether to use adjacency-driven placement
        self.timeout = 30  # Timeout in seconds
        
        # Create adjacency graph for faster lookups
        self.adjacency_graph = self._build_adjacency_graph()
        
    def _build_adjacency_graph(self):
        """Build adjacency graph from adjacency dictionary"""
        graph = defaultdict(list)
        for room_id, neighbors in self.adjacency.items():
            for neighbor_id in neighbors:
                graph[room_id].append(neighbor_id)
        return graph
        
    def clear_placements(self):
        """Reset all room placements"""
        for room in self.rooms:
            room.x = None
            room.y = None
            room.region = None
            room.rotated = False
        self.placed_rooms = []
    
    def set_sort_method(self, method="hybrid"):
        """Set the method for sorting rooms before placement"""
        valid_methods = ["area", "adjacency", "width", "height", "perimeter", "hybrid", "degree_area"]
        if method not in valid_methods:
            raise ValueError(f"Sort method must be one of {valid_methods}")
        self.sort_method = method
            
    def sort_rooms(self):
        """Sort rooms according to the current sorting method"""
        if self.sort_method == "area":
            return sorted(self.rooms, key=lambda r: -r.area())
        elif self.sort_method == "adjacency":
            return sorted(self.rooms, key=lambda r: -len(self.adjacency.get(r.id, [])))
        elif self.sort_method == "width":
            return sorted(self.rooms, key=lambda r: -r.width)
        elif self.sort_method == "height":
            return sorted(self.rooms, key=lambda r: -r.height)
        elif self.sort_method == "perimeter":
            return sorted(self.rooms, key=lambda r: -(r.width + r.height))
        elif self.sort_method == "hybrid":
            # Weighted combination of adjacency and area
            return sorted(self.rooms, key=lambda r: 
                -(self.adjacency_weight * len(self.adjacency.get(r.id, [])) + 
                 self.area_weight * r.area() / max(r.area() for r in self.rooms)))
        elif self.sort_method == "degree_area":
            # Sort first by adjacency degree, then by area
            return sorted(self.rooms, 
                         key=lambda r: (-len(self.adjacency.get(r.id, [])), -r.area()))
        return self.rooms  # No sorting
    
    def _is_rotation_preferred(self, room, region):
        """
        Determine if rotation is preferred for this room in this region.
        """
        if not self.optimize_rotations:
            return False
            
        # For narrow regions, align with region's orientation
        if region.is_narrow():
            region_ratio = region.aspect_ratio()
            room_ratio = room.width / max(room.height, 0.01)
            
            if region_ratio < 1:  # Tall region
                # Room should be taller than wide
                return room_ratio > 1
            else:  # Wide region
                # Room should be wider than tall
                return room_ratio < 1
                
        # For normal regions, prefer original orientation
        return False
    
    def _get_region_fit_score(self, room, region, x, y):
        """
        Calculate how well a room fits in a region at position (x,y).
        Returns a score from 0 (poor fit) to 1 (perfect fit).
        """
        if not region.contains(room, x, y):
            return 0
            
        # Calculate free space on each side
        left_space = x - region.x1
        right_space = region.x2 - (x + room.width)
        top_space = y - region.y1
        bottom_space = region.y2 - (y + room.height)
        
        # Total free space
        total_space = left_space + right_space + top_space + bottom_space
        
        # Region area and room area
        region_area = region.area()
        room_area = room.area()
        
        # Calculate fit score as ratio of room area to available area
        fit_score = room_area / (room_area + total_space)
        
        return fit_score
        
    def _get_adjacency_score(self, room, position, orientation):
        """
        Calculate adjacency satisfaction score for a room at the given position.
        Returns the number of satisfied adjacencies.
        """
        score = 0
        original_pos = (room.x, room.y, room.rotated)
        
        # Temporarily set the room position
        room.x, room.y = position
        if orientation != room.rotated:
            room.rotate()
            
        # Check adjacency with already placed rooms
        for placed_room in self.placed_rooms:
            # Add score for required adjacencies
            if placed_room.id in self.adjacency_graph.get(room.id, []):
                if room.is_adjacent(placed_room):
                    score += 1
            
            # Also consider adjacencies the other way around
            if room.id in self.adjacency_graph.get(placed_room.id, []):
                if room.is_adjacent(placed_room):
                    score += 0.5  # half weight for inverse adjacencies
                    
        # Restore original position
        room.x, room.y = original_pos[:2]
        if orientation != original_pos[2]:
            room.rotate()
            
        return score
    
    def _generate_candidate_positions(self, room):
        """
        Generate candidate positions for a room based on adjacency requirements.
        Returns a list of (position, region, is_rotated, score) tuples.
        """
        candidates = []
        required_adjacencies = set(self.adjacency_graph.get(room.id, []))
        
        # Get rooms that should be adjacent to this one
        adjacent_placed_rooms = [r for r in self.placed_rooms 
                               if r.id in required_adjacencies]
        
        # If no adjacency requirements or no placed adjacent rooms, 
        # use regular grid sampling
        if not adjacent_placed_rooms and self.placed_rooms:
            # If there are placed rooms but none are adjacent requirements,
            # try positions near existing rooms anyway for better layouts
            adjacent_placed_rooms = self.placed_rooms
            
        if not adjacent_placed_rooms:
            # No rooms placed yet or no adjacency - use grid sampling
            for region in self.regions:
                # Check original orientation
                for pos in region.get_sample_positions(room, self.step_size):
                    fit_score = self._get_region_fit_score(room, region, pos[0], pos[1])
                    if fit_score > 0:
                        candidates.append((pos, region, False, fit_score))
                
                # Check rotated orientation if allowed
                if self.optimize_rotations:
                    room.rotate()
                    for pos in region.get_sample_positions(room, self.step_size):
                        fit_score = self._get_region_fit_score(room, region, pos[0], pos[1])
                        if fit_score > 0:
                            candidates.append((pos, region, True, fit_score))
                    room.rotate()  # Restore original orientation
        else:
            # Generate positions adjacent to already placed rooms
            for placed_room in adjacent_placed_rooms:
                adj_positions = room.get_adjacent_positions(placed_room)
                
                for pos, is_rotated in [(p[:2], p[2]) for p in adj_positions]:
                    # Check if position is valid in any region
                    if is_rotated != room.rotated:
                        room.rotate()
                        
                    for region in self.regions:
                        fit_score = self._get_region_fit_score(room, region, pos[0], pos[1])
                        if fit_score > 0:
                            adj_score = self._get_adjacency_score(room, pos, is_rotated)
                            # Combined score - adjacency is most important
                            score = 0.8 * adj_score + 0.2 * fit_score
                            candidates.append((pos, region, is_rotated, score))
                    
                    if is_rotated != room.rotated:
                        room.rotate()  # Restore original orientation
        
        # Sort candidates by score
        candidates.sort(key=lambda x: -x[3])
        return candidates
    
    def _place_room_backtracking(self, room_idx, depth=0, timeout_start=None):
        """
        Attempt to place rooms using backtracking.
        Returns True if successful, False otherwise.
        """
        # Check timeout
        if timeout_start and time.time() - timeout_start > self.timeout:
            return False
            
        # If all rooms are placed, we're done
        if room_idx >= len(self.rooms):
            return True
            
        current_room = self.rooms[room_idx]
        
        # Generate candidate positions
        candidates = self._generate_candidate_positions(current_room)
        
        for position, region, is_rotated, score in candidates:
            # Set room to current orientation
            if is_rotated != current_room.rotated:
                current_room.rotate()
                
            # Check for overlaps with placed rooms
            current_room.x, current_room.y = position
            current_room.region = region
            
            has_overlap = False
            for placed_room in self.placed_rooms:
                if current_room.overlaps(placed_room):
                    has_overlap = True
                    break
                    
            if not has_overlap:
                # Valid placement, add to placed rooms
                self.placed_rooms.append(current_room)
                
                # Try to place next room
                if self._place_room_backtracking(room_idx + 1, depth + 1, timeout_start):
                    return True
                    
                # If we couldn't place the next room, backtrack
                self.placed_rooms.remove(current_room)
                
        # Restore original orientation
        if current_room.rotated != (self.rooms[room_idx].rotated):
            current_room.rotate()
            
        current_room.x = None
        current_room.y = None
        current_room.region = None
        
        return False
        
    def place_rooms(self):
        """
        Place rooms according to the strategy.
        Returns the number of successfully placed rooms.
        """
        self.clear_placements()
        
        # Sort rooms by the selected method
        sorted_rooms = self.sort_rooms()
        self.rooms = sorted_rooms  # Use the sorted order for backtracking
        
        # If using backtracking algorithm
        timeout_start = time.time()
        if self._place_room_backtracking(0, timeout_start=timeout_start):
            return len(self.placed_rooms)
            
        # If backtracking failed or timed out, fall back to greedy approach
        self.clear_placements()
        return self._place_rooms_greedy(sorted_rooms)
        
    def _place_rooms_greedy(self, sorted_rooms):
        """
        Place rooms using a greedy algorithm.
        Returns the number of successfully placed rooms.
        """
        for room in sorted_rooms:
            best_score = -1
            best_pos = None
            best_rot = False
            best_region = None
            
            # Generate and evaluate candidate positions
            candidates = self._generate_candidate_positions(room)
            
            for position, region, is_rotated, score in candidates:
                # Set room to current orientation
                if is_rotated != room.rotated:
                    room.rotate()
                    
                # Check for overlaps with placed rooms
                room.x, room.y = position
                
                overlap = False
                for placed_room in self.placed_rooms:
                    if room.overlaps(placed_room):
                        overlap = True
                        break
                        
                if not overlap:
                    # Calculate final score
                    adjacency_score = self._get_adjacency_score(room, position, is_rotated)
                    region_score = self._get_region_fit_score(room, region, position[0], position[1])
                    
                    # Combined score - adjacency is most important
                    combined_score = 0.8 * adjacency_score + 0.2 * region_score
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_pos = position
                        best_rot = is_rotated
                        best_region = region
                
                # Restore original orientation for next candidate
                if is_rotated != room.rotated:
                    room.rotate()
            
            # Apply best placement if found
            if best_pos:
                if best_rot != room.rotated:
                    room.rotate()
                room.x, room.y = best_pos
                room.region = best_region
                self.placed_rooms.append(room)
                
        return len(self.placed_rooms)
    
    def get_adjacency_score(self):
        """
        Calculate the adjacency satisfaction score.
        Returns tuple (satisfied, total, ratio)
        """
        satisfied = 0
        total = 0
        
        for room1 in self.placed_rooms:
            required_neighbors = self.adjacency.get(room1.id, [])
            for neighbor_id in required_neighbors:
                total += 1
                # Find the neighbor room
                for room2 in self.placed_rooms:
                    if room2.id == neighbor_id and room1.is_adjacent(room2):
                        satisfied += 1
                        break
                        
        ratio = satisfied / total if total > 0 else 1.0
        return (satisfied, total, ratio)
    
    def visualize(self, show_adjacency=True, title=None, axes=None):
        """
        Visualize the placement results.
        
        Args:
            show_adjacency: Whether to draw adjacency connections
            title: Title for the plot
            axes: Matplotlib axes to draw on (if None, creates a new figure)
        """
        if axes is None:
            fig, axes = plt.subplots(figsize=(10, 8))
            show_fig = True
        else:
            show_fig = False
        
        # Plot regions
        for i, region in enumerate(self.regions):
            rect = patches.Rectangle(
                (region.x1, region.y1), 
                region.x2 - region.x1, 
                region.y2 - region.y1,
                linewidth=2,
                edgecolor='blue',
                facecolor='lightblue',
                alpha=0.2,
                label=f"Region {i+1}" if i == 0 else ""
            )
            axes.add_patch(rect)
        
        # Colors for rooms
        colors = plt.cm.tab10(np.linspace(0, 1, 10))
        
        # Store room centers for adjacency lines
        room_centers = {}
        
        # Plot placed rooms
        for i, room in enumerate(self.placed_rooms):
            if room.x is not None and room.y is not None:
                color = colors[i % len(colors)]
                rect = patches.Rectangle(
                    (room.x, room.y),
                    room.width,
                    room.height,
                    linewidth=1,
                    edgecolor='black',
                    facecolor=color,
                    alpha=0.7
                )
                axes.add_patch(rect)
                
                # Store center for adjacency lines
                center_x = room.x + room.width/2
                center_y = room.y + room.height/2
                room_centers[room.id] = (center_x, center_y)
                
                # Add room label
                axes.text(
                    center_x,
                    center_y,
                    f"{room.id}",
                    ha='center',
                    va='center',
                    fontsize=10,
                    fontweight='bold'
                )
        
        # Draw adjacency connections
        if show_adjacency:
            satisfied_edges = []
            unsatisfied_edges = []
            
            for room1 in self.placed_rooms:
                required_neighbors = self.adjacency.get(room1.id, [])
                for neighbor_id in required_neighbors:
                    # Find the neighbor room
                    neighbor_placed = False
                    adjacency_satisfied = False
                    
                    for room2 in self.placed_rooms:
                        if room2.id == neighbor_id:
                            neighbor_placed = True
                            if room1.is_adjacent(room2):
                                adjacency_satisfied = True
                            break
                    
                    if neighbor_placed:
                        if room1.id in room_centers and neighbor_id in room_centers:
                            x1, y1 = room_centers[room1.id]
                            x2, y2 = room_centers[neighbor_id]
                            
                            if adjacency_satisfied:
                                satisfied_edges.append(((x1, y1), (x2, y2)))
                            else:
                                unsatisfied_edges.append(((x1, y1), (x2, y2)))
            
            # Plot satisfied adjacencies
            for (x1, y1), (x2, y2) in satisfied_edges:
                axes.plot([x1, x2], [y1, y2], color='green', linestyle='-', linewidth=2, alpha=0.7)
                
            # Plot unsatisfied adjacencies
            for (x1, y1), (x2, y2) in unsatisfied_edges:
                axes.plot([x1, x2], [y1, y2], color='red', linestyle=':', linewidth=1, alpha=0.7)
            
            # Add legend for adjacency lines
            axes.plot([], [], color='green', linestyle='-', linewidth=2, label='Satisfied adjacency')
            axes.plot([], [], color='red', linestyle=':', linewidth=1, label='Unsatisfied adjacency')
            
        # Calculate and show statistics
        placed_count = len(self.placed_rooms)
        total_count = len(self.rooms)
        adjacency_score = self.get_adjacency_score()
        
        # Add statistics text
        stats_text = (
            f"Statistics:\n"
            f"- Rooms placed: {placed_count}/{total_count}\n"
            f"- Adjacency satisfaction: {adjacency_score[0]}/{adjacency_score[1]} "
            f"({adjacency_score[2]:.2f})"
        )
        axes.text(
            0,
            -1,
            stats_text,
            fontsize=9,
            horizontalalignment='left',
            verticalalignment='top'
        )
        
        # Set title
        if title:
            axes.set_title(title)
        else:
            axes.set_title(f"Region-Based Room Placement (Sort: {self.sort_method})")
            
        # Set axis properties
        axes.set_aspect('equal')
        axes.legend(loc='upper right')
        
        # Set limits with padding
        all_x = [r.x1 for r in self.regions] + [r.x2 for r in self.regions]
        all_y = [r.y1 for r in self.regions] + [r.y2 for r in self.regions]
        
        margin = 2
        axes.set_xlim(min(all_x) - margin, max(all_x) + margin)
        axes.set_ylim(min(all_y) - margin, max(all_y) + margin)
        
        if show_fig:
            plt.tight_layout()
            plt.show()

def create_h_shape_regions(width, height, corridor_width):
    """
    Create regions for an H-shaped layout.
    
    Args:
        width: Total width of the H-shape
        height: Total height of the H-shape
        corridor_width: Width of the horizontal corridor
        
    Returns:
        List of PlotRegion objects defining the H-shape
    """
    left_width = right_width = width / 3
    corridor_y = (height - corridor_width) / 2
    
    # Left vertical region
    left_region = PlotRegion(0, 0, left_width, height, "Left Wing")
    
    # Middle horizontal corridor
    middle_region = PlotRegion(
        left_width, corridor_y,
        width - right_width, corridor_y + corridor_width,
        "Corridor"
    )
    
    # Right vertical region
    right_region = PlotRegion(
        width - right_width, 0,
        width, height,
        "Right Wing"
    )
    
    # Add overlapping corner regions for more flexibility
    upper_left = PlotRegion(
        left_width * 0.7, corridor_y + corridor_width,
        left_width * 1.3, height,
        "Upper Left Corner"
    )
    
    lower_left = PlotRegion(
        left_width * 0.7, 0,
        left_width * 1.3, corridor_y,
        "Lower Left Corner"
    )
    
    upper_right = PlotRegion(
        width - right_width * 1.3, corridor_y + corridor_width,
        width - right_width * 0.7, height,
        "Upper Right Corner"
    )
    
    lower_right = PlotRegion(
        width - right_width * 1.3, 0, 
        width - right_width * 0.7, corridor_y,
        "Lower Right Corner"
    )
    
    return [left_region, middle_region, right_region, 
            upper_left, lower_left, upper_right, lower_right]

def main():
    # Define basic room data
    rooms_data = [
        (1, 3, 9), (2, 8, 3), (3, 6, 4), (4, 3, 5), (5, 6, 5),
        (6, 4, 4), (7, 5, 5), (8, 4, 3), (9, 3, 5), (10, 4, 3)
    ]
    
    # Room names
    room_names = [
        "Living Room", "Kitchen", "Dining", "Master Bedroom", 
        "Bedroom 2", "Bathroom 1", "Bedroom 3", "Bathroom 2", 
        "Study", "Utility"
    ]
    
    # Create rooms
    rooms = [Room(rid, w, h, name) for (rid, w, h), name in zip(rooms_data, room_names)]
    
    # Define regions for H-shape
    regions = create_h_shape_regions(15, 15, 3)
    
    # Define adjacency requirements
    adjacency = {
        1: [2, 3],   2: [1, 4],   3: [1, 5],
        4: [2, 6],   5: [3, 7],   6: [4, 8],
        7: [5, 9],   8: [6, 10],  9: [7], 10: [8]
    }
    
    # Create and configure the placement strategy
    strategy = RegionBasedPlacement(rooms, regions, adjacency)
    strategy.set_sort_method("hybrid")  # Hybrid sort method
    strategy.adjacency_weight = 0.7
    strategy.area_weight = 0.3
    
    # Place rooms
    start_time = time.time()
    num_placed = strategy.place_rooms()
    elapsed_time = time.time() - start_time
    
    print(f"Placed {num_placed} out of {len(rooms)} rooms in {elapsed_time:.2f} seconds.")
    
    # Calculate adjacency satisfaction
    satisfied, total, ratio = strategy.get_adjacency_score()
    print(f"Adjacency satisfaction: {satisfied}/{total} ({ratio:.2f})")
    
    # Print room placements
    for room in strategy.placed_rooms:
        print(f"Room {room.id} ({room.name}): Position ({room.x}, {room.y}), "
              f"Dimensions {room.width}x{room.height} "
              f"(Rotated: {room.rotated})")
    
    # Visualize
    strategy.visualize()

if __name__ == "__main__":
    main()