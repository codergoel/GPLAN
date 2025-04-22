import sys
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSpinBox, QSlider, QPushButton, 
                             QCheckBox, QTabWidget, QGridLayout, QGroupBox, 
                             QRadioButton, QProgressBar, QMessageBox, QDoubleSpinBox,
                             QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QLineEdit, QScrollArea, QSizePolicy)
import time
import random

# Import the region-based strategy
from strategy import (Room, PlotRegion, RegionBasedPlacement, 
                     create_h_shape_regions, are_adjacent)

class RegionViewer(FigureCanvas):
    """Widget to display the regions and room placements"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.strategy = None
        
    def update_view(self, strategy=None, title=None):
        """Update the visualization with the given strategy"""
        if strategy:
            self.strategy = strategy
            
        if self.strategy:
            self.axes.clear()
            self.strategy.visualize(show_adjacency=True, title=title, axes=self.axes)
            self.draw()
        else:
            self.axes.clear()
            self.axes.set_title("No data to display")
            self.axes.text(0.5, 0.5, "Configure regions and rooms to generate a floorplan", 
                         ha='center', va='center')
            self.draw()

class StrategyThread(QThread):
    """Thread for running the placement strategy"""
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(object)
    
    def __init__(self, strategy, parent=None):
        super().__init__(parent)
        self.strategy = strategy
        
    def run(self):
        try:
            start_time = time.time()
            self.progress_signal.emit(10, "Starting room placement...")
            
            # Run the placement algorithm
            self.strategy.clear_placements()
            self.strategy.place_rooms()
            
            # Get the results
            elapsed_time = time.time() - start_time
            adjacency_score = self.strategy.get_adjacency_score()
            
            self.progress_signal.emit(90, f"Placed {len(self.strategy.placed_rooms)} rooms in {elapsed_time:.2f}s")
            self.finished_signal.emit(self.strategy)
            
        except Exception as e:
            print(f"Error in strategy thread: {str(e)}")
            self.progress_signal.emit(100, f"Error: {str(e)}")

class RoomDefinitionTable(QTableWidget):
    """Custom table widget for defining rooms"""
    
    roomChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Room Name", "Width", "Height"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(True)
        
        # Initial setup with default 5 rooms
        self.setRowCount(5)
        self.setup_default_rooms()
        
        # Connect signals
        self.cellChanged.connect(self.on_cell_changed)
    
    def setup_default_rooms(self):
        """Setup default room names and dimensions"""
        default_rooms = [
            ("Living Room", 3, 4),
            ("Kitchen", 2, 3),
            ("Dining Room", 2, 2),
            ("Bedroom", 3, 3),
            ("Bathroom", 2, 2)
        ]
        
        for row, (name, width, height) in enumerate(default_rooms):
            # Room name
            name_item = QTableWidgetItem(name)
            self.setItem(row, 0, name_item)
            
            # Width
            width_spinner = QSpinBox()
            width_spinner.setRange(1, 20)
            width_spinner.setValue(width)
            width_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 1, width_spinner)
            
            # Height
            height_spinner = QSpinBox()
            height_spinner.setRange(1, 20)
            height_spinner.setValue(height)
            height_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 2, height_spinner)
    
    def on_cell_changed(self):
        """Handle cell content changes"""
        self.roomChanged.emit()
    
    def add_room(self):
        """Add a new room to the table"""
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        
        # Default values for the new room
        self.setItem(row_count, 0, QTableWidgetItem(f"Room {row_count + 1}"))
        
        # Width spinner
        width_spinner = QSpinBox()
        width_spinner.setRange(1, 20)
        width_spinner.setValue(2)
        width_spinner.valueChanged.connect(self.on_cell_changed)
        self.setCellWidget(row_count, 1, width_spinner)
        
        # Height spinner
        height_spinner = QSpinBox()
        height_spinner.setRange(1, 20)
        height_spinner.setValue(2)
        height_spinner.valueChanged.connect(self.on_cell_changed)
        self.setCellWidget(row_count, 2, height_spinner)
        
        self.roomChanged.emit()
    
    def remove_room(self):
        """Remove the last room from the table"""
        row_count = self.rowCount()
        if row_count > 1:
            self.setRowCount(row_count - 1)
            self.roomChanged.emit()
    
    def get_rooms(self):
        """Get the room definitions as a list of Room objects"""
        rooms = []
        for row in range(self.rowCount()):
            try:
                # Get room name with fallback
                name = self.item(row, 0).text() if self.item(row, 0) else f"Room {row+1}"
                
                # Get width and height with error checking
                width_widget = self.cellWidget(row, 1)
                height_widget = self.cellWidget(row, 2)
                
                width = width_widget.value() if width_widget else 2
                height = height_widget.value() if height_widget else 2
                
                room = Room(row + 1, width, height, name)
                rooms.append(room)
            except Exception as e:
                print(f"Error creating room at row {row}: {str(e)}")
                # Add a default room as fallback
                room = Room(row + 1, 2, 2, f"Room {row+1}")
                rooms.append(room)
        return rooms

class RegionDefinitionTable(QTableWidget):
    """Custom table widget for defining regions"""
    
    regionChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Region Name", "X1", "Y1", "X2", "Y2"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(True)
        
        # Initial setup with default H-shape regions
        self.setRowCount(3)
        self.setup_default_regions()
        
        # Connect signals
        self.cellChanged.connect(self.on_cell_changed)
    
    def setup_default_regions(self):
        """Setup default H-shape regions"""
        default_regions = [
            ("Left Wing", 0, 0, 5, 15),
            ("Corridor", 5, 6, 10, 9),
            ("Right Wing", 10, 0, 15, 15)
        ]
        
        for row, (name, x1, y1, x2, y2) in enumerate(default_regions):
            # Region name
            name_item = QTableWidgetItem(name)
            self.setItem(row, 0, name_item)
            
            # X1
            x1_spinner = QSpinBox()
            x1_spinner.setRange(0, 50)
            x1_spinner.setValue(x1)
            x1_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 1, x1_spinner)
            
            # Y1
            y1_spinner = QSpinBox()
            y1_spinner.setRange(0, 50)
            y1_spinner.setValue(y1)
            y1_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 2, y1_spinner)
            
            # X2
            x2_spinner = QSpinBox()
            x2_spinner.setRange(0, 50)
            x2_spinner.setValue(x2)
            x2_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 3, x2_spinner)
            
            # Y2
            y2_spinner = QSpinBox()
            y2_spinner.setRange(0, 50)
            y2_spinner.setValue(y2)
            y2_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 4, y2_spinner)
    
    def on_cell_changed(self):
        """Handle cell content changes"""
        # Ensure x1 < x2 and y1 < y2
        for row in range(self.rowCount()):
            # Get cell widgets with safety checks
            x1_widget = self.cellWidget(row, 1)
            y1_widget = self.cellWidget(row, 2)
            x2_widget = self.cellWidget(row, 3)
            y2_widget = self.cellWidget(row, 4)
            
            # Skip if any widgets are missing
            if not all([x1_widget, y1_widget, x2_widget, y2_widget]):
                continue
                
            # Get values safely
            x1 = x1_widget.value()
            y1 = y1_widget.value()
            x2 = x2_widget.value()
            y2 = y2_widget.value()
            
            if x2 <= x1:
                x2_widget.setValue(x1 + 1)
            if y2 <= y1:
                y2_widget.setValue(y1 + 1)
        
        self.regionChanged.emit()
    
    def add_region(self):
        """Add a new region to the table"""
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        
        # Default values for the new region
        self.setItem(row_count, 0, QTableWidgetItem(f"Region {row_count + 1}"))
        
        # X1
        x1_spinner = QSpinBox()
        x1_spinner.setRange(0, 50)
        x1_spinner.setValue(0)
        x1_spinner.valueChanged.connect(self.on_cell_changed)
        self.setCellWidget(row_count, 1, x1_spinner)
        
        # Y1
        y1_spinner = QSpinBox()
        y1_spinner.setRange(0, 50)
        y1_spinner.setValue(0)
        y1_spinner.valueChanged.connect(self.on_cell_changed)
        self.setCellWidget(row_count, 2, y1_spinner)
        
        # X2
        x2_spinner = QSpinBox()
        x2_spinner.setRange(0, 50)
        x2_spinner.setValue(5)
        x2_spinner.valueChanged.connect(self.on_cell_changed)
        self.setCellWidget(row_count, 3, x2_spinner)
        
        # Y2
        y2_spinner = QSpinBox()
        y2_spinner.setRange(0, 50)
        y2_spinner.setValue(5)
        y2_spinner.valueChanged.connect(self.on_cell_changed)
        self.setCellWidget(row_count, 4, y2_spinner)
        
        self.regionChanged.emit()
    
    def remove_region(self):
        """Remove the last region from the table"""
        row_count = self.rowCount()
        if row_count > 1:
            self.setRowCount(row_count - 1)
            self.regionChanged.emit()
    
    def get_regions(self):
        """Get the region definitions as a list of PlotRegion objects"""
        regions = []
        for row in range(self.rowCount()):
            try:
                # Get region name with fallback
                name = self.item(row, 0).text() if self.item(row, 0) else f"Region {row+1}"
                
                # Get coordinates with error checking
                x1_widget = self.cellWidget(row, 1)
                y1_widget = self.cellWidget(row, 2)
                x2_widget = self.cellWidget(row, 3)
                y2_widget = self.cellWidget(row, 4)
                
                x1 = x1_widget.value() if x1_widget else 0
                y1 = y1_widget.value() if y1_widget else 0
                x2 = x2_widget.value() if x2_widget else 5
                y2 = y2_widget.value() if y2_widget else 5
                
                # Ensure x2 > x1 and y2 > y1
                if x2 <= x1:
                    x2 = x1 + 1
                if y2 <= y1:
                    y2 = y1 + 1
                    
                region = PlotRegion(x1, y1, x2, y2, name)
                regions.append(region)
            except Exception as e:
                print(f"Error creating region at row {row}: {str(e)}")
                # Add a default region as fallback
                region = PlotRegion(0, 0, 5, 5, f"Region {row+1}")
                regions.append(region)
        return regions
    
    def apply_h_shape(self, width, height, corridor_width):
        """Apply H-shape regions with the given dimensions"""
        regions = create_h_shape_regions(width, height, corridor_width)
        
        # Update the table with the new regions
        self.setRowCount(len(regions))
        for row, region in enumerate(regions):
            # Region name
            name_item = QTableWidgetItem(region.name)
            self.setItem(row, 0, name_item)
            
            # X1
            x1_spinner = QSpinBox()
            x1_spinner.setRange(0, 50)
            x1_spinner.setValue(int(region.x1))
            x1_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 1, x1_spinner)
            
            # Y1
            y1_spinner = QSpinBox()
            y1_spinner.setRange(0, 50)
            y1_spinner.setValue(int(region.y1))
            y1_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 2, y1_spinner)
            
            # X2
            x2_spinner = QSpinBox()
            x2_spinner.setRange(0, 50)
            x2_spinner.setValue(int(region.x2))
            x2_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 3, x2_spinner)
            
            # Y2
            y2_spinner = QSpinBox()
            y2_spinner.setRange(0, 50)
            y2_spinner.setValue(int(region.y2))
            y2_spinner.valueChanged.connect(self.on_cell_changed)
            self.setCellWidget(row, 4, y2_spinner)
        
        self.regionChanged.emit()

class AdjacencyMatrix(QTableWidget):
    """Widget for editing the adjacency matrix"""
    
    adjacencyChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.room_count = 5  # Default
        self.setup_matrix()
        
    def setup_matrix(self):
        """Set up the adjacency matrix with the current room count"""
        self.setRowCount(self.room_count)
        self.setColumnCount(self.room_count)
        
        # Set headers (room numbers)
        headers = [str(i + 1) for i in range(self.room_count)]
        self.setHorizontalHeaderLabels(headers)
        self.setVerticalHeaderLabels(headers)
        
        # Center align headers
        for i in range(self.room_count):
            self.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)
            self.verticalHeaderItem(i).setTextAlignment(Qt.AlignCenter)
        
        # Resize columns and rows to contents
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        
        # Fill with checkboxes
        for row in range(self.room_count):
            for col in range(self.room_count):
                if row == col:
                    # No self-connections
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                    item.setBackground(Qt.lightGray)
                    self.setItem(row, col, item)
                else:
                    # Create checkbox
                    checkbox = QCheckBox()
                    checkbox.setChecked(False)
                    
                    # For diagonal symmetry, check if opposite already exists
                    if col < row and self.cellWidget(col, row) is not None:
                        opposite_checkbox = self.cellWidget(col, row).findChild(QCheckBox)
                        if opposite_checkbox:
                            checkbox.setChecked(opposite_checkbox.isChecked())
                    
                    # Center checkbox in cell
                    cell_widget = QWidget()
                    layout = QHBoxLayout(cell_widget)
                    layout.addWidget(checkbox)
                    layout.setAlignment(Qt.AlignCenter)
                    layout.setContentsMargins(0, 0, 0, 0)
                    cell_widget.setLayout(layout)
                    
                    # Connect to maintain symmetry
                    checkbox.stateChanged.connect(self.on_checkbox_changed)
                    
                    self.setCellWidget(row, col, cell_widget)
    
    def on_checkbox_changed(self):
        """Handle checkbox state changes and ensure matrix symmetry"""
        # Find which checkbox was changed
        changed_checkbox = self.sender()
        if not changed_checkbox:
            return
            
        # Find its position in the table
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                cell_widget = self.cellWidget(row, col)
                if cell_widget:
                    checkbox = cell_widget.findChild(QCheckBox)
                    if checkbox is changed_checkbox:
                        # Update the symmetric position
                        opposite_widget = self.cellWidget(col, row)
                        if opposite_widget:
                            opposite_checkbox = opposite_widget.findChild(QCheckBox)
                            if opposite_checkbox:
                                # Block signals to prevent recursion
                                opposite_checkbox.blockSignals(True)
                                opposite_checkbox.setChecked(checkbox.isChecked())
                                opposite_checkbox.blockSignals(False)
                        
                        # Emit signal for change
                        self.adjacencyChanged.emit()
                        return
    
    def update_size(self, room_count):
        """Update the matrix size for the given room count"""
        if room_count == self.room_count:
            return
            
        # Store existing connections
        connections = {}
        for row in range(min(self.room_count, room_count)):
            for col in range(min(self.room_count, room_count)):
                if row != col:
                    cell_widget = self.cellWidget(row, col)
                    if cell_widget:
                        checkbox = cell_widget.findChild(QCheckBox)
                        if checkbox:
                            connections[(row, col)] = checkbox.isChecked()
        
        # Update room count and recreate matrix
        self.room_count = room_count
        self.setup_matrix()
        
        # Restore connections
        for (row, col), is_connected in connections.items():
            cell_widget = self.cellWidget(row, col)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(is_connected)
    
    def get_adjacency_dict(self):
        """
        Get the adjacency requirements as a dictionary.
        Returns a dict mapping room ids to lists of adjacent room ids.
        """
        adjacency_dict = {}
        
        for row in range(self.room_count):
            try:
                room_id = row + 1  # 1-indexed
                adjacency_dict[room_id] = []
                
                for col in range(self.room_count):
                    if row != col:
                        cell_widget = self.cellWidget(row, col)
                        if cell_widget:
                            checkbox = cell_widget.findChild(QCheckBox)
                            if checkbox and checkbox.isChecked():
                                adjacency_dict[room_id].append(col + 1)  # 1-indexed
            except Exception as e:
                print(f"Error processing adjacency at row {row}: {str(e)}")
                # Initialize empty adjacency list as fallback
                adjacency_dict[row + 1] = []
        
        return adjacency_dict
    
    def fill_with_pattern(self, pattern):
        """Fill the adjacency matrix with a predefined pattern"""
        # Clear all connections first
        for row in range(self.room_count):
            for col in range(self.room_count):
                if row != col:
                    cell_widget = self.cellWidget(row, col)
                    if cell_widget:
                        checkbox = cell_widget.findChild(QCheckBox)
                        if checkbox:
                            checkbox.setChecked(False)
        
        if pattern == "Linear":
            # Each room connects to next/previous room (chain)
            for i in range(self.room_count - 1):
                cell_widget1 = self.cellWidget(i, i + 1)
                cell_widget2 = self.cellWidget(i + 1, i)
                if cell_widget1 and cell_widget2:
                    checkbox1 = cell_widget1.findChild(QCheckBox)
                    checkbox2 = cell_widget2.findChild(QCheckBox)
                    if checkbox1 and checkbox2:
                        checkbox1.setChecked(True)
                        checkbox2.setChecked(True)
                        
        elif pattern == "Hub":
            # First room connects to all others (star)
            for i in range(1, self.room_count):
                cell_widget1 = self.cellWidget(0, i)
                cell_widget2 = self.cellWidget(i, 0)
                if cell_widget1 and cell_widget2:
                    checkbox1 = cell_widget1.findChild(QCheckBox)
                    checkbox2 = cell_widget2.findChild(QCheckBox)
                    if checkbox1 and checkbox2:
                        checkbox1.setChecked(True)
                        checkbox2.setChecked(True)
                        
        elif pattern == "Grid":
            # Grid pattern (if enough rooms)
            side_length = int(np.sqrt(self.room_count))
            for i in range(self.room_count):
                # Connect to right neighbor
                if (i + 1) % side_length != 0 and i + 1 < self.room_count:
                    cell_widget1 = self.cellWidget(i, i + 1)
                    cell_widget2 = self.cellWidget(i + 1, i)
                    if cell_widget1 and cell_widget2:
                        checkbox1 = cell_widget1.findChild(QCheckBox)
                        checkbox2 = cell_widget2.findChild(QCheckBox)
                        if checkbox1 and checkbox2:
                            checkbox1.setChecked(True)
                            checkbox2.setChecked(True)
                
                # Connect to bottom neighbor
                if i + side_length < self.room_count:
                    cell_widget1 = self.cellWidget(i, i + side_length)
                    cell_widget2 = self.cellWidget(i + side_length, i)
                    if cell_widget1 and cell_widget2:
                        checkbox1 = cell_widget1.findChild(QCheckBox)
                        checkbox2 = cell_widget2.findChild(QCheckBox)
                        if checkbox1 and checkbox2:
                            checkbox1.setChecked(True)
                            checkbox2.setChecked(True)
        
        self.adjacencyChanged.emit()

class RegionFloorplanApp(QMainWindow):
    """Main application window for region-based floorplan generation"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Region-Based Floorplan Generator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        
        # Create control panel with scrolling
        self.create_control_panel()
        
        # Create visualization panel
        self.create_visualization_panel()
        
        # Initialize the generator thread
        self.strategy_thread = None
        
        # Initialization flag
        self.initializing = True
        
        # Show the UI
        self.show()
        
        # Connect signals for initial setup
        self.on_room_changed()
        self.initializing = False
    
    def create_control_panel(self):
        # Create a scroll area for the control panel
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create control panel widget and layout
        self.control_panel = QWidget()
        self.control_layout = QVBoxLayout(self.control_panel)
        self.control_panel.setMaximumWidth(450)
        
        # Create algorithm parameters group
        self.create_algorithm_params_group()
        
        # Add preset button group
        self.control_layout.addWidget(self.create_preset_button_group())
        
        # Create room definition group
        self.create_room_definition_group()
        
        # Create region definition group
        self.create_region_definition_group()
        
        # Create adjacency matrix group
        self.create_adjacency_group()
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.control_layout.addWidget(self.progress_bar)
        
        # Add status label
        self.status_label = QLabel("Ready")
        self.control_layout.addWidget(self.status_label)
        
        # Add generate button
        self.generate_button = QPushButton("Generate Floorplan")
        self.generate_button.clicked.connect(self.generate_floorplan)
        self.control_layout.addWidget(self.generate_button)
        
        # Add some space at the bottom
        self.control_layout.addSpacing(20)
        
        # Set the control panel as the widget for the scroll area
        self.scroll_area.setWidget(self.control_panel)
        
        # Add to main layout
        self.main_layout.addWidget(self.scroll_area)
    
    def create_algorithm_params_group(self):
        """Create the algorithm parameters group"""
        params_group = QGroupBox("Algorithm Parameters")
        params_layout = QGridLayout()
        
        # Sort method
        params_layout.addWidget(QLabel("Sort Method:"), 0, 0)
        self.sort_method_combo = QComboBox()
        self.sort_method_combo.addItems(["Area", "Adjacency", "Width", "Height", "Perimeter", "Hybrid", "Degree-Area"])
        self.sort_method_combo.setCurrentText("Hybrid")  # Default to hybrid
        params_layout.addWidget(self.sort_method_combo, 0, 1)
        
        # Allow rotations
        params_layout.addWidget(QLabel("Allow Rotations:"), 1, 0)
        self.rotation_checkbox = QCheckBox()
        self.rotation_checkbox.setChecked(True)
        params_layout.addWidget(self.rotation_checkbox, 1, 1)
        
        # Step size for position sampling
        params_layout.addWidget(QLabel("Step Size:"), 2, 0)
        self.step_size_spin = QSpinBox()
        self.step_size_spin.setRange(1, 5)
        self.step_size_spin.setValue(1)
        self.step_size_spin.setToolTip("Increment size when searching positions (larger = faster but less precise)")
        params_layout.addWidget(self.step_size_spin, 2, 1)
        
        # Adjacency weight
        params_layout.addWidget(QLabel("Adjacency Weight:"), 3, 0)
        self.adjacency_weight_spin = QDoubleSpinBox()
        self.adjacency_weight_spin.setRange(0.1, 1.0)
        self.adjacency_weight_spin.setSingleStep(0.1)
        self.adjacency_weight_spin.setValue(0.7)
        self.adjacency_weight_spin.setToolTip("Weight given to adjacency in hybrid sorting (0.1-1.0)")
        params_layout.addWidget(self.adjacency_weight_spin, 3, 1)
        
        # Area weight
        params_layout.addWidget(QLabel("Area Weight:"), 4, 0)
        self.area_weight_spin = QDoubleSpinBox()
        self.area_weight_spin.setRange(0.0, 0.9)
        self.area_weight_spin.setSingleStep(0.1)
        self.area_weight_spin.setValue(0.3)
        self.area_weight_spin.setToolTip("Weight given to area in hybrid sorting (0.0-0.9)")
        params_layout.addWidget(self.area_weight_spin, 4, 1)
        
        # Timeout
        params_layout.addWidget(QLabel("Timeout (sec):"), 5, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setToolTip("Maximum time to try backtracking before falling back to greedy approach")
        params_layout.addWidget(self.timeout_spin, 5, 1)
        
        # Algorithm type
        params_layout.addWidget(QLabel("Algorithm:"), 6, 0)
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["Backtracking + Greedy", "Greedy Only"])
        self.algorithm_combo.setToolTip("Backtracking tries harder to satisfy all constraints but may be slower")
        params_layout.addWidget(self.algorithm_combo, 6, 1)
        
        # Connect signals for weights to ensure they sum to <= 1.0
        self.adjacency_weight_spin.valueChanged.connect(self.update_area_weight_max)
        self.area_weight_spin.valueChanged.connect(self.update_adjacency_weight_max)
        
        params_group.setLayout(params_layout)
        self.control_layout.addWidget(params_group)
    
    def update_area_weight_max(self, value):
        """Update the maximum allowed area weight based on adjacency weight"""
        max_area = min(0.9, 1.0 - value)
        current_area = self.area_weight_spin.value()
        self.area_weight_spin.setMaximum(max_area)
        if current_area > max_area:
            self.area_weight_spin.setValue(max_area)
    
    def update_adjacency_weight_max(self, value):
        """Update the maximum allowed adjacency weight based on area weight"""
        max_adj = min(1.0, 1.0 - value)
        current_adj = self.adjacency_weight_spin.value()
        self.adjacency_weight_spin.setMaximum(max_adj)
        if current_adj > max_adj:
            self.adjacency_weight_spin.setValue(max_adj)
    
    def create_room_definition_group(self):
        """Create the room definition group"""
        room_group = QGroupBox("Room Definitions")
        room_layout = QVBoxLayout()
        
        # Room table
        self.room_table = RoomDefinitionTable()
        self.room_table.roomChanged.connect(self.on_room_changed)
        room_layout.addWidget(self.room_table)
        
        # Add/Remove buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Room")
        add_button.clicked.connect(self.room_table.add_room)
        remove_button = QPushButton("Remove Room")
        remove_button.clicked.connect(self.room_table.remove_room)
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        room_layout.addLayout(button_layout)
        
        room_group.setLayout(room_layout)
        self.control_layout.addWidget(room_group)
    
    def create_region_definition_group(self):
        """Create the region definition group"""
        region_group = QGroupBox("Region Definitions")
        region_layout = QVBoxLayout()
        
        # H-shape controls
        h_shape_layout = QHBoxLayout()
        h_shape_layout.addWidget(QLabel("H-Shape:"))
        
        # Width
        h_shape_layout.addWidget(QLabel("W:"))
        self.h_width_spin = QSpinBox()
        self.h_width_spin.setRange(6, 30)
        self.h_width_spin.setValue(15)
        h_shape_layout.addWidget(self.h_width_spin)
        
        # Height
        h_shape_layout.addWidget(QLabel("H:"))
        self.h_height_spin = QSpinBox()
        self.h_height_spin.setRange(6, 30)
        self.h_height_spin.setValue(15)
        h_shape_layout.addWidget(self.h_height_spin)
        
        # Corridor width
        h_shape_layout.addWidget(QLabel("Corridor:"))
        self.corridor_width_spin = QSpinBox()
        self.corridor_width_spin.setRange(1, 10)
        self.corridor_width_spin.setValue(3)
        h_shape_layout.addWidget(self.corridor_width_spin)
        
        # Apply button
        h_shape_button = QPushButton("Apply H-Shape")
        h_shape_button.clicked.connect(self.apply_h_shape)
        h_shape_layout.addWidget(h_shape_button)
        
        region_layout.addLayout(h_shape_layout)
        
        # Region table
        self.region_table = RegionDefinitionTable()
        self.region_table.regionChanged.connect(self.on_region_changed)
        region_layout.addWidget(self.region_table)
        
        # Add/Remove buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Region")
        add_button.clicked.connect(self.region_table.add_region)
        remove_button = QPushButton("Remove Region")
        remove_button.clicked.connect(self.region_table.remove_region)
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        region_layout.addLayout(button_layout)
        
        region_group.setLayout(region_layout)
        self.control_layout.addWidget(region_group)
    
    def create_adjacency_group(self):
        """Create the adjacency matrix group"""
        adjacency_group = QGroupBox("Adjacency Requirements")
        adjacency_layout = QVBoxLayout()
        
        # Pattern buttons
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Pattern:"))
        
        # Patterns dropdown
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["None", "Linear", "Hub", "Grid"])
        pattern_layout.addWidget(self.pattern_combo)
        
        # Apply button
        apply_pattern_button = QPushButton("Apply Pattern")
        apply_pattern_button.clicked.connect(self.apply_adjacency_pattern)
        pattern_layout.addWidget(apply_pattern_button)
        
        adjacency_layout.addLayout(pattern_layout)
        
        # Create scrollable area for adjacency matrix
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Adjacency matrix
        self.adjacency_matrix = AdjacencyMatrix()
        self.adjacency_matrix.adjacencyChanged.connect(self.on_adjacency_changed)
        scroll_area.setWidget(self.adjacency_matrix)
        
        adjacency_layout.addWidget(scroll_area)
        
        adjacency_group.setLayout(adjacency_layout)
        self.control_layout.addWidget(adjacency_group)
    
    def create_visualization_panel(self):
        """Create the visualization panel"""
        # Create visualization widget
        self.viz_widget = QWidget()
        self.viz_layout = QVBoxLayout(self.viz_widget)
        
        # Create region viewer
        self.region_viewer = RegionViewer(self.viz_widget)
        self.viz_layout.addWidget(self.region_viewer)
        
        # Add to main layout
        self.main_layout.addWidget(self.viz_widget, 1)  # 1 = stretch factor
    
    def on_room_changed(self):
        """Handle room definition changes"""
        # Update adjacency matrix size
        room_count = self.room_table.rowCount()
        self.adjacency_matrix.update_size(room_count)
        
        # Update the visualization if not initializing
        if not self.initializing:
            self.update_preview()
    
    def on_region_changed(self):
        """Handle region definition changes"""
        # Update the visualization if not initializing
        if not self.initializing:
            self.update_preview()
    
    def on_adjacency_changed(self):
        """Handle adjacency matrix changes"""
        # Update the visualization if not initializing
        if not self.initializing:
            self.update_preview()
    
    def apply_h_shape(self):
        """Apply H-shape regions with current dimensions"""
        width = self.h_width_spin.value()
        height = self.h_height_spin.value()
        corridor_width = self.corridor_width_spin.value()
        
        # Update region table
        self.region_table.apply_h_shape(width, height, corridor_width)
    
    def apply_adjacency_pattern(self):
        """Apply the selected adjacency pattern"""
        pattern = self.pattern_combo.currentText()
        if pattern != "None":
            self.adjacency_matrix.fill_with_pattern(pattern)
    
    def update_preview(self):
        """Update the visualization preview"""
        try:
            # Get current data
            rooms = self.room_table.get_rooms()
            regions = self.region_table.get_regions()
            adjacency_dict = self.adjacency_matrix.get_adjacency_dict()
            
            # Create a strategy object for preview
            strategy = RegionBasedPlacement(rooms, regions, adjacency_dict)
            
            # Update the viewer without running the placement
            self.region_viewer.update_view(strategy, "Region Preview (No Placement)")
        except Exception as e:
            print(f"Error updating preview: {str(e)}")
            self.status_label.setText(f"Error updating preview: {str(e)}")
    
    def create_preset_button_group(self):
        """Create preset buttons for quick configuration"""
        preset_group = QGroupBox("Presets")
        preset_layout = QHBoxLayout()
        
        # Create preset buttons
        simple_preset = QPushButton("Simple")
        simple_preset.clicked.connect(lambda: self.apply_preset("simple"))
        
        optimal_preset = QPushButton("Optimal")
        optimal_preset.clicked.connect(lambda: self.apply_preset("optimal"))
        
        adjacency_preset = QPushButton("Adjacency")
        adjacency_preset.clicked.connect(lambda: self.apply_preset("adjacency"))
        
        speed_preset = QPushButton("Speed")
        speed_preset.clicked.connect(lambda: self.apply_preset("speed"))
        
        # Add buttons to layout
        preset_layout.addWidget(simple_preset)
        preset_layout.addWidget(optimal_preset)
        preset_layout.addWidget(adjacency_preset)
        preset_layout.addWidget(speed_preset)
        
        preset_group.setLayout(preset_layout)
        return preset_group
    
    def apply_preset(self, preset_name):
        """Apply predefined parameter presets"""
        if preset_name == "simple":
            # Simple preset - basic parameters
            self.sort_method_combo.setCurrentText("Area")
            self.rotation_checkbox.setChecked(True)
            self.step_size_spin.setValue(1)
            self.adjacency_weight_spin.setValue(0.5)
            self.area_weight_spin.setValue(0.5)
            self.timeout_spin.setValue(15)
            self.algorithm_combo.setCurrentText("Greedy Only")
            
        elif preset_name == "optimal":
            # Optimal preset - best quality but slower
            self.sort_method_combo.setCurrentText("Hybrid")
            self.rotation_checkbox.setChecked(True)
            self.step_size_spin.setValue(1)
            self.adjacency_weight_spin.setValue(0.7)
            self.area_weight_spin.setValue(0.3)
            self.timeout_spin.setValue(60)
            self.algorithm_combo.setCurrentText("Backtracking + Greedy")
            
        elif preset_name == "adjacency":
            # Adjacency preset - focus on connections
            self.sort_method_combo.setCurrentText("Degree-Area")
            self.rotation_checkbox.setChecked(True)
            self.step_size_spin.setValue(1)
            self.adjacency_weight_spin.setValue(0.9)
            self.area_weight_spin.setValue(0.1)
            self.timeout_spin.setValue(45)
            self.algorithm_combo.setCurrentText("Backtracking + Greedy")
            
        elif preset_name == "speed":
            # Speed preset - faster results
            self.sort_method_combo.setCurrentText("Area")
            self.rotation_checkbox.setChecked(True)
            self.step_size_spin.setValue(2)
            self.adjacency_weight_spin.setValue(0.6)
            self.area_weight_spin.setValue(0.4)
            self.timeout_spin.setValue(10)
            self.algorithm_combo.setCurrentText("Greedy Only")
    
    def generate_floorplan(self):
        """Generate floorplan using the region-based strategy"""
        try:
            # Get current data
            rooms = self.room_table.get_rooms()
            regions = self.region_table.get_regions()
            adjacency_dict = self.adjacency_matrix.get_adjacency_dict()
            
            # Validate input data
            if not rooms:
                self.status_label.setText("Error: No rooms defined")
                return
                
            if not regions:
                self.status_label.setText("Error: No regions defined")
                return
            
            # Create and configure the strategy
            strategy = RegionBasedPlacement(rooms, regions, adjacency_dict)
            
            # Set algorithm parameters
            sort_method = self.sort_method_combo.currentText().lower()
            if sort_method == "degree-area":
                sort_method = "degree_area"  # Match the internal name
            
            strategy.set_sort_method(sort_method)
            strategy.optimize_rotations = self.rotation_checkbox.isChecked()
            strategy.step_size = self.step_size_spin.value()
            strategy.adjacency_weight = self.adjacency_weight_spin.value()
            strategy.area_weight = self.area_weight_spin.value()
            strategy.timeout = self.timeout_spin.value()
            
            # Set algorithm type
            if self.algorithm_combo.currentText() == "Greedy Only":
                # Disable backtracking by setting timeout to 0
                strategy.timeout = 0
            
            # Disable the generate button during generation
            self.generate_button.setEnabled(False)
            self.status_label.setText("Generating floorplan...")
            self.progress_bar.setValue(0)
            
            # Start the generator thread
            self.strategy_thread = StrategyThread(strategy)
            self.strategy_thread.progress_signal.connect(self.update_progress)
            self.strategy_thread.finished_signal.connect(self.show_results)
            self.strategy_thread.start()
        except Exception as e:
            print(f"Error generating floorplan: {str(e)}")
            self.status_label.setText(f"Error generating floorplan: {str(e)}")
            self.generate_button.setEnabled(True)
    
    def update_progress(self, progress, status):
        """Update the progress bar and status label"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def show_results(self, strategy):
        """Show the generated floorplan results"""
        # Re-enable the generate button
        self.generate_button.setEnabled(True)
        
        # Get adjacency score
        satisfied, total, ratio = strategy.get_adjacency_score()
        self.status_label.setText(
            f"Placed {len(strategy.placed_rooms)}/{len(strategy.rooms)} rooms. "
            f"Adjacency: {satisfied}/{total} ({ratio:.2f})"
        )
        
        # Update the visualization
        self.region_viewer.update_view(strategy, f"Region-Based Placement (Sort: {strategy.sort_method})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegionFloorplanApp()
    sys.exit(app.exec_()) 