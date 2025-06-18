#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent .pyc file creation

import gdsfactory as gf
import json

def create_box(name, width, height, layer=(69, 0)):
    """Create a single box component with specified dimensions."""
    c = gf.Component(name)
    
    # Standard GDS convention: (x, y) where x=horizontal, y=vertical
    points = [
        (-width/2, -height/2),  # bottom-left
        (width/2, -height/2),   # bottom-right  
        (width/2, height/2),    # top-right
        (-width/2, height/2)    # top-left
    ]
    
    c.add_polygon(points, layer=layer)
    return c

def load_particles_config(json_path="Json/particles.json"):
    """Load particles configuration from JSON file."""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

def create_particles_component(config=None):
    """Create a component containing all particles from the JSON configuration."""
    if config is None:
        config = load_particles_config()
    
    if not config or 'particles' not in config:
        print("Error: Invalid configuration or no particles defined")
        return None
    
    # Get origin point for the particles component (default to [0,0])
    origin = config.get('origin', [0, 0])
    origin_x, origin_y = origin
    
    # Create main particles component
    particles = gf.Component("particles")
    
    print(f"Creating particles component with {len(config['particles'])} boxes...")
    print(f"Particles origin set at: [{origin_x}, {origin_y}]")
    
    for i, particle_config in enumerate(config['particles']):
        # Extract particle parameters
        name = particle_config.get('name', f'particle_{i+1}')
        width = particle_config.get('width', 1000)
        height = particle_config.get('height', 1000)
        position = particle_config.get('position', [0, 0])
        layer = tuple(particle_config.get('layer', [69, 0]))
        
        # Calculate absolute position relative to origin
        rel_x, rel_y = position
        abs_x = rel_x + origin_x
        abs_y = rel_y + origin_y
        
        # Create individual box
        box = create_box(f"box_{name}", width, height, layer)
        
        # Add box to particles component and position it
        box_ref = particles.add_ref(box)
        box_ref.move((abs_x, abs_y))
        box_ref.name = name
        
        print(f"  ✓ Added {name}: {width}x{height} at rel{position} -> abs[{abs_x}, {abs_y}] on layer {layer}")
    
    return particles

def get_component():
    """Main function to create particles component - compatible with placement system."""
    particles = create_particles_component()
    if particles is None:
        # Return empty component if configuration fails
        particles = gf.Component("particles_empty")
    
    return particles, "Particles"

# For direct testing and GDS export
def main():
    """Test function to create and save particles component."""
    particles = create_particles_component()
    
    if particles:
        # Save as GDS file
        particles.write_gds("GDS_Files/particles.gds")
        print(f"\n✓ Particles GDS saved as GDS_Files/particles.gds")
        
        # Show in viewer
        particles.show()
        print(f"✓ Particles component created with bbox: {particles.bbox}")
    else:
        print("✗ Failed to create particles component")

if __name__ == "__main__":
    main()
