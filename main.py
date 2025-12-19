#!/usr/bin/env python
import opensky_api, geopy, yaml, logging, requests, time, datetime, urllib
from geopy.distance import geodesic
from typing import Tuple
from requests.exceptions import RequestException, HTTPError

USER_AGENT="whats_flying_over_my_house"

logger = logging.getLogger(__name__)

class CurrentFlight:
    home_lat: float
    home_lon: float
    radius: float
    bounding_box: Tuple[float,float,float,float]
    icao: str
    origin_airport: str
    rate_limit_remaining: str
    fa_api_key: str

    def __init__(self, config:str) -> None:
        # dynamically updated
        self.origin_airport = ""
        self.icao = ""
        # static
        self._set_radius_from_config(config)
        self._set_home_from_config(config)
        self._set_fa_api_key_from_config(config)
        self._set_bounding_box()
    
    # Currently unused - could be useful
    def _set_home_from_config_address(self, config_file: str) -> None:
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
                if attempt >= max_attempts:
                    exit()
        self.home_lat = coord.latitude
        self.home_lon = coord.longitude
    
    def _set_radius_from_config(self, config_file: str) -> None:
        with open(config_file) as f:
            data = yaml.safe_load(f)

        radius = data.get("radius", False)

        if not radius:
            raise ValueError("configuration is missing radius")
    
        self.radius = radius

    def _set_fa_api_key_from_config(self, config_file: str) -> None:
        with open(config_file) as f:
            data = yaml.safe_load(f)

        fa_api_key = data.get("apiKey", False)

        if not fa_api_key:
            raise ValueError("configuration is missing apiKey")
    
        self.fa_api_key = fa_api_key

    def _set_home_from_config(self, config_file: str) -> None:
        with open(config_file) as f:
            data = yaml.safe_load(f)

        home_lat = data["location"].get("lat", False)
        home_lon = data["location"].get("lon", False)

        if not home_lat or not home_lon:
            raise ValueError("configuration is missing address.lat and or address.lon")
    
        self.home_lat = home_lat
        self.home_lon = home_lon

    def _set_bounding_box(self) -> None:
        lomin = self.home_lon - self.radius 
        lomax = self.home_lon + self.radius
        lamin = self.home_lat - self.radius
        lamax = self.home_lat + self.radius
        self.bounding_box = (lamin, lamax, lomin, lomax)
    
    def _home_as_tuple(self) -> Tuple[str,str]:
        return (str(self.home_lat), str(self.home_lon))

    # Placeholder function for sending signal to split flap display
    def update_origin_airport(self) -> None:
        params = {
                "ident_type": "designator",
                # "end": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
        params = urllib.parse.urlencode(params)
        headers = {
                "x-apikey": self.fa_api_key,
                "Accept": "application/json; charset=UTF-8"
                } 
        flight_aware_uri = f"https://aeroapi.flightaware.com/aeroapi/flights/{self.icao}"
        res = requests.get(flight_aware_uri, headers=headers, params=params)
        res.raise_for_status()
        origin_airport = res.json()["flights"][0]["origin"]["code_icao"]
        if not origin_airport:
            raise ValueError("origin airport could not be parsed for icao {self.icao}")
        if self.origin_airport != origin_airport:
            self.origin_airport = origin_airport

    def get_distance_from_home(self, state: opensky_api.StateVector) -> float:
        state_coord = (state.latitude, state.longitude)
        dist = geodesic(state_coord, self._home_as_tuple())
        return dist.miles
def get_rate_from_config(config_file: str) -> int:
    with open(config_file) as f:
        data = yaml.safe_load(f)

    # Default to getting current flight data every 60 seconds
    return data.get("rate", 60)

def main():
    api = opensky_api.OpenSkyApi()
    rate = get_rate_from_config("config.yaml")
    current_flight = CurrentFlight("config.yaml")
    while True:
        try:
            states = api.get_states(bbox=current_flight.bounding_box).states
        except Exception as e:
            logger.warning(f"failed to get states, retrying in 5 seconds: {e}")
            time.sleep(5)
            continue
        closest_icao = ""
        # Initialize closest_distance as equal to the search radius
        closest_distance = None

        # Find state closest to home
        for state in states:
            distance_from_home = current_flight.get_distance_from_home(state)
            if closest_distance is None or distance_from_home < closest_distance:
                closest_distance = distance_from_home
                closest_icao = state.callsign.strip()

        # Retrieve origin airport from closest state icao.  Skip if we already know icao origin info.
        if closest_icao and closest_icao != current_flight.icao:
            logger.info("Closer flight detected, retrieving origin airport")
            current_flight.icao = closest_icao
            try:
                current_flight.update_origin_airport()
            except HTTPError as e:
                logger.error(f"HTTP error encountered while retreiving origin airport code: {e}")
                raise e
            except RequestException as e:
                logger.erro("Exception encountered while updating origin airport")
                raise e
        logger.info(f"icao: {current_flight.icao}, origin: {current_flight.origin_airport}")
        # this is debug
        raise SystemExit()
        time.sleep(rate)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        main()
    except KeyboardInterrupt:
        logger.error("\nExiting by user request\n")
    except Exception as e:
        logger.error(f"\nProgram exited due to exception: {e}")
