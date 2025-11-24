# What's Flying Over My House?

A Python tool that uses the OpenSky Network API to detect aircraft flying within a specified radius of your location.

## Features

- Real-time aircraft tracking using the OpenSky Network API
- Configurable location (address-based)
- Customizable detection radius
- Automatic address geocoding

## Requirements

- Python 3.11 or higher
- OpenSky Network API access (free, no authentication required for basic use)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd whats-flying-over-my-house
```

2. Run the setup script:
```bash
./setup.sh
```

Or manually install dependencies using uv:
```bash
uv sync
```

## Configuration

Create a `config.yaml` file in the project root with the following structure:

```yaml
location:
  address: "Your Address, City, State/Country"
distance: 5.0  # radius in miles
```

Example:
```yaml
location:
  address: "1600 Pennsylvania Avenue NW, Washington, DC"
distance: 10.0
```

## Usage

Run the script:
```bash
python main.py
```

The script will:
1. Geocode your configured address
2. Query the OpenSky Network API for current aircraft positions
3. Filter aircraft within your specified radius
4. Display the callsigns of aircraft currently in range

## Dependencies

- `opensky_api` - Interface to the OpenSky Network API
- `geopy` - Geocoding and distance calculations
- `pyyaml` - Configuration file parsing

## How It Works

1. Reads your location and radius from `config.yaml`
2. Converts the address to coordinates using Nominatim geocoding
3. Retrieves current aircraft states from OpenSky Network
4. Calculates the distance between each aircraft and your location
5. Filters and displays aircraft within the specified radius

## Notes

- The geocoding service (Nominatim) has rate limits; the script includes retry logic
- OpenSky Network API may have rate limits for unauthenticated requests
- Aircraft positions are updated based on ADS-B data availability
