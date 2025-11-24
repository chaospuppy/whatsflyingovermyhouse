#!/usr/bin/env python
import opensky_api, geopy, yaml, logging
from geopy.distance import geodesic
from typing import Tuple

USER_AGENT="whats_flying_over_my_house"

logger = logging.getLogger(__name__)

def flight_is_within_radius(state: opensky_api.StateVector, home_coord: Tuple[str,str], radius: float) -> bool:
    state_coord = (state.latitude, state.longitude)
    dist = geodesic(state_coord, home_coord)
    if dist.miles < radius:
        return True

def get_radius_from_config(config_file: str) -> float:
    with open(config_file) as f:
        data = yaml.safe_load(f)

    return float(data["distance"])

def get_addr_from_config(config_file: str) -> Tuple[str, str]:
    with open(config_file) as f:
        data = yaml.safe_load(f)

    address = data["location"]["address"]
    geolocator = geopy.Nominatim(user_agent=USER_AGENT)


    attempt = 0
    max_attempts = 3
    while True:
        attempt += 1
        try:
            logger.info(f"attempt {attempt} of {max_attempts}")
            coord = geolocator.geocode(address)
            break
        except Exception as e:
            logger.error(f"failed on attempt {attempt} of {max_attempts}: {e}")
            if attempt > max_attempts:
                exit()
    return (coord.latitude, coord.longitude)

def main():
    logging.basicConfig(level=logging.INFO)
    home_coord = get_addr_from_config("config.yaml")
    radius = get_radius_from_config("config.yaml")
    api = opensky_api.OpenSkyApi()
    s = api.get_states()
    states_in_range = (state for state in s.states if flight_is_within_radius(state, home_coord, radius))
    for state in states_in_range:
        print(state.callsign)
    # for state in s.states:
    #   if calculate_radius(state, home_coord):          
    #       print(state.callsign)

    return

if __name__ == "__main__":
    exit(main())
