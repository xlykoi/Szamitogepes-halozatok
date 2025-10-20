#!/usr/bin/env python3
"""
Sliding Squares in Parallel - Step-by-Step Interactive Visualizer
Click buttons to see each step of the reconfiguration process
"""

import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
from src.grid_config import Grid, Configuration, Point


class StepByStepVisualizer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sliding Squares Configuration Visualizer")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Configuration
        self.grid_size = 8
        self.cell_size = 60
        self.grid = Grid(self.grid_size, self.grid_size)
        
        # Current state
        self.start_config = None
        self.current_config = None
        self.final_config = None
        self.showing_final = False
        
        # Colors
        self.colors = {
            'empty': '#ecf0f1',
            'occupied': '#3498db',
            'goal': '#e74c3c',
            'moving': '#f39c12',
            'grid': '#bdc3c7',
            'text': '#2c3e50',
            'background': '#2c3e50',
            'highlight': '#9b59b6'
        }
        
        self.setup_ui()
        self.load_starting_configuration()
        # Update display after UI is fully set up
        self.root.after(100, self.update_display)
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors['background'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Sliding Squares Configuration Visualizer", 
                              font=('Arial', 18, 'bold'), 
                              fg='white', bg=self.colors['background'])
        title_label.pack(pady=(0, 15))
        
        # Status display
        self.status_label = tk.Label(main_frame, text="Configuration loaded", 
                                    font=('Arial', 12), fg='white', bg=self.colors['background'])
        self.status_label.pack(pady=(0, 10))
        
        # Control panel
        control_frame = tk.Frame(main_frame, bg=self.colors['background'])
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Load Final Configuration button
        self.final_config_btn = tk.Button(control_frame, text="Load Final Configuration", 
                                        command=self.load_final_configuration,
                                        bg='#27ae60', fg='white', font=('Arial', 14, 'bold'),
                                        width=20, height=2)
        self.final_config_btn.pack(pady=10)
        
        # Canvas for visualization
        canvas_frame = tk.Frame(main_frame, bg=self.colors['background'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, width=700, height=600, 
                               bg='white', relief=tk.RAISED, bd=2)
        self.canvas.pack(pady=10)
        
        # Bind canvas click events
        # self.canvas.bind("<Button-1>", self.on_canvas_click)
    
    def parse_coordinates(self, content):
        """Parse coordinate string like '(3,3) (4,3) (5,3)' into a set of Points"""
        points = set()
        
        # Use regex to find all coordinate pairs
        pattern = r'\((\d+),(\d+)\)'
        matches = re.findall(pattern, content)
        
        for x_str, y_str in matches:
            try:
                x = int(x_str)
                y = int(y_str)
                point = Point(x, y)
                
                # Validate that point is within grid bounds
                if self.grid.is_valid(point):
                    points.add(point)
                else:
                    print(f"Warning: Point ({x}, {y}) is outside grid bounds")
            except ValueError:
                print(f"Warning: Invalid coordinate format: ({x_str}, {y_str})")
        
        return points
    
    def load_starting_configuration(self, filepath=None):
        """Load starting configuration from file"""
        if filepath is None:
            filepath = "configurations.txt"
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"Configuration file not found: {filepath}")
            return
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Parse coordinates from the entire file content
            cells = self.parse_coordinates(content)
            
            if not cells:
                raise ValueError("No valid coordinates found in file")
            
            # Create configuration
            self.start_config = Configuration(self.grid, cells)
            self.current_config = self.start_config.copy()
            
            # Defer display update if UI not ready
            if hasattr(self, 'canvas') and self.canvas:
                self.update_display()
            self.update_status(f"Configuration loaded from {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            return
    
    def load_final_configuration(self):
        """Load the final configuration from final-configuration.txt"""
        filepath = "final-configuration.txt"
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"Final configuration file not found: {filepath}")
            return
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Parse coordinates from the file content
            cells = self.parse_coordinates(content)
            
            if not cells:
                raise ValueError("No valid coordinates found in final configuration file")
            
            # Create final configuration
            self.final_config = Configuration(self.grid, cells)
            self.showing_final = True
            
            # Update button states
            self.final_config_btn.config(text="Show Original", command=self.show_original_from_final)
            
            # Update display
            self.update_display()
            self.update_status(f"Final configuration loaded from {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load final configuration: {str(e)}")
    
    def show_original_from_final(self):
        """Show the original configuration when coming from final config"""
        self.showing_final = False
        
        # Update button states
        self.final_config_btn.config(text="Load Final Configuration", command=self.load_final_configuration)
        
        self.update_display()
        self.update_status("Showing original configuration")
    
    def update_display(self):
        """Update the visual display"""
        # Safety check - ensure canvas exists
        if not hasattr(self, 'canvas') or not self.canvas:
            return
            
        self.canvas.delete("all")
        
        if not self.current_config:
            self.draw_empty_grid()
            return
        
        # Draw grid
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                # Grid lines
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                           outline=self.colors['grid'], width=1)
        
        # Draw current configuration
        if self.showing_final and self.final_config:
            config_to_draw = self.final_config
        else:
            config_to_draw = self.current_config
        
        if config_to_draw:
            for cell in config_to_draw.occupied_cells:
                x1 = cell.x * self.cell_size + 2
                y1 = cell.y * self.cell_size + 2
                x2 = x1 + self.cell_size - 4
                y2 = y1 + self.cell_size - 4
                
                # Use different colors for different configurations
                if self.showing_final:
                    fill_color = self.colors['highlight']  # Purple for final config
                    outline_color = 'black'
                    outline_width = 3
                else:
                    fill_color = self.colors['occupied']  # Blue for original
                    outline_color = 'black'
                    outline_width = 2
                
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                           fill=fill_color, 
                                           outline=outline_color, width=outline_width)
        
        # Draw legend
        self.draw_legend()
        
        # Draw configuration info
        self.draw_config_info()
    
    def draw_empty_grid(self):
        """Draw empty grid when no configuration"""
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                           outline=self.colors['grid'], width=1)
    
    def draw_legend(self):
        """Draw the legend"""
        legend_x = 10
        legend_y = 10
        
        # Legend background
        self.canvas.create_rectangle(legend_x, legend_y, legend_x + 250, legend_y + 100, 
                                   fill='white', outline='black', width=2)
        
        # Legend items
        if self.showing_final:
            # Show final configuration legend
            self.canvas.create_rectangle(legend_x + 10, legend_y + 15, legend_x + 25, legend_y + 30, 
                                       fill=self.colors['highlight'], outline='black', width=3)
            self.canvas.create_text(legend_x + 35, legend_y + 22, text="Final Configuration", 
                                  font=('Arial', 10), anchor='w')
            
            self.canvas.create_text(legend_x + 10, legend_y + 40, text="Loaded from final-configuration.txt", 
                                  font=('Arial', 9), anchor='w')
            
            self.canvas.create_text(legend_x + 10, legend_y + 55, text="3x3 Grid Arrangement", 
                                  font=('Arial', 9), anchor='w')
            
            self.canvas.create_text(legend_x + 10, legend_y + 70, text="Phase 1: Final Result", 
                                  font=('Arial', 9), anchor='w')
        else:
            # Show original configuration legend
            self.canvas.create_rectangle(legend_x + 10, legend_y + 15, legend_x + 25, legend_y + 30, 
                                       fill=self.colors['occupied'], outline='black')
            self.canvas.create_text(legend_x + 35, legend_y + 22, text="Original Configuration", 
                                  font=('Arial', 10), anchor='w')
            
            self.canvas.create_text(legend_x + 10, legend_y + 40, text="Loaded from configurations.txt", 
                                  font=('Arial', 9), anchor='w')
            
            self.canvas.create_text(legend_x + 10, legend_y + 55, text="Scattered Module Arrangement", 
                                  font=('Arial', 9), anchor='w')
            
            self.canvas.create_text(legend_x + 10, legend_y + 70, text="Click 'Load Final Configuration'", 
                                  font=('Arial', 9), anchor='w')
    
    def draw_config_info(self):
        """Draw configuration information"""
        if not self.current_config:
            return
        
        info_x = 10
        info_y = 500
        
        # Info background
        self.canvas.create_rectangle(info_x, info_y, info_x + 300, info_y + 80, 
                                   fill='lightblue', outline='black', width=2)
        
        if self.showing_final and self.final_config:
            # Show final configuration info
            config_text = f"Final Configuration:\nModules: {len(self.final_config)}\nPerimeter: {self.final_config.perimeter()}\nConnected: {self.final_config.is_connected()}"
            
            self.canvas.create_text(info_x + 10, info_y + 15, text="Final Configuration Info", 
                                  font=('Arial', 12, 'bold'), anchor='w')
            self.canvas.create_text(info_x + 10, info_y + 35, text=config_text, 
                                  font=('Arial', 10), anchor='w')
        else:
            # Show original configuration info
            config_text = f"Original Configuration:\nModules: {len(self.current_config)}\nPerimeter: {self.current_config.perimeter()}\nConnected: {self.current_config.is_connected()}"
            
            self.canvas.create_text(info_x + 10, info_y + 15, text="Configuration Info", 
                                  font=('Arial', 12, 'bold'), anchor='w')
            self.canvas.create_text(info_x + 10, info_y + 35, text=config_text, 
                                  font=('Arial', 10), anchor='w')
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.config(text=message)
        self.root.update()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main function"""
    print("Starting Sliding Squares Configuration Visualizer...")
    print("Features:")
    print("- Load configuration from configurations.txt")
    print("- Display configuration on grid")
    print("- Click cells to modify configuration")
    print("- View configuration properties")
    print()
    
    app = StepByStepVisualizer()
    app.run()


if __name__ == "__main__":
    main()
