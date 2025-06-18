<<<<<<< HEAD
# Photonic Design Automation

A comprehensive Python-based framework for designing and fabricating photonic integrated circuits using GDSFactory.

## Project Structure

```
├── Python codes/           # Core design scripts
│   ├── width_pitch.py     # Grating coupler parameter sweeps
│   ├── ROC_array.py       # Ring resonator arrays  
│   ├── snail.py           # Spiral waveguide components
│   ├── Grid.py            # Grid and marker generation
│   └── placement.py       # Multi-die placement system
├── Json/                  # Configuration files
│   ├── width_pitch.json   # Grating parameters
│   ├── ROC_array.json     # Ring resonator specs
│   ├── Grid.json          # Grid and chip settings
│   └── placement.json     # Die placement coordinates
├── build/gds/             # Generated GDS files
└── NPF,NFF and NJF/       # E-beam lithography files
```

## Key Features

### 📐 **Design Components**
- **Grating Couplers**: Parameter sweeps for width and period optimization
- **Ring Resonators**: Arrays with variable coupling gaps and radii
- **Spiral Waveguides**: Compact delay lines with grating interfaces
- **Grid Systems**: Alignment grids with e-beam field markers

### 🎯 **Placement System** 
- Multi-die layouts with individual parameter control
- Dynamic chip sizing based on component placement
- Hierarchical component organization
- Unique naming to prevent GDS collisions

### ⚙️ **Automation Features**
- JSON-driven parameter configuration
- Batch processing for multiple designs
- Automatic grid generation and alignment
- E-beam field marker placement

## Quick Start

### Basic Component Generation
```python
# Generate grating coupler sweeps
python width_pitch.py

# Create ring resonator arrays  
python ROC_array.py

# Generate spiral waveguides
python snail.py
```

### Multi-Die Placement
```python
# Place multiple dies with different parameters
python placement.py
```

### Configuration
Edit JSON files to customize:
- **width_pitch.json**: Grating widths, periods, spacing
- **ROC_array.json**: Ring radii, coupling gaps, array spacing  
- **Grid.json**: Chip size, grid spacing, marker settings
- **placement.json**: Die positions and individual parameters

## Key Components

### Width-Pitch Sweeps (`width_pitch.py`)
Creates arrays of grating couplers with systematic width and period variations for coupling optimization.

### Ring Arrays (`ROC_array.py`) 
Generates arrays of ring resonators with different radii while maintaining constant optical path length.

### Placement System (`placement.py`)
Enables multi-die layouts where each die can have different component parameters (widths, radii, etc.).

### Grid Generation (`Grid.py`)
Creates alignment grids with coordinate markers and e-beam field indicators for precise fabrication.

## Output Files

- **GDS Files**: `build/gds/` - Industry-standard layout files
- **E-beam Files**: `NPF,NFF and NJF/` - Lithography job files  
- **Config Backups**: JSON parameter snapshots

## Requirements

- Python 3.8+
- GDSFactory
- NumPy
- JSON (built-in)

## Usage Tips

1. **Start with JSON configuration** - Modify parameters before running scripts
2. **Use placement system** - For complex multi-die layouts
3. **Check GDS output** - Verify designs before fabrication
4. **Backup configurations** - Keep track of working parameter sets

This framework enables rapid prototyping and systematic optimization of photonic devices for research and production environments.
=======
I am adding all the files where I build componants using the GDS factory library (9.5.10) as a part of my M1 internship in CEA and Instutut Neel (CNRS). 
These are codes to build different PIC that are used as test circuits for the propagation loss characterisation of th waveguide. 
In addition to the Codes for GDS file creation. I will also add codes that I wrote for specific parameter sweep and optimization simulation. I will use Tidy 3D and lumerical for this!
I will also add the NPF files and Job files that can be used using the Nanobeam platform to perform E beam patterning. 
I will try to explain the conversion from GDS  E beam files and the logic behind the different exposure steps to the best of my understanding. 
This Repository is intended to serve as a guide for students that are getting started with PIC design, E beam patterning and clean room fabrication of the designs. 
The hope is that Reviewing this project will help students understand the various steps including, Design, Optimization simulatiom, E beam patterning, Clean room fabrication, anf finally 2D and 3D simulation that are necessary in characterizing a PIC.
In addition to this you can also read the paper with the results and interpretation to understand how the results could be presented. 
>>>>>>> 9f33d889b150fb0c2cc833a548a40127910f5e9f
