from datetime import datetime

class Simulation:
    def __init__(self, start_date_time: datetime, step_size: str):
        self.start_date_time = start_date_time
        self.step_size = step_size
        self.current_date_time = start_date_time
        self.aggregated_data = {}  # {species_code: {(lat, lon): {"catch": 0.0, "biomass": 0.0}}}
        self.last_written_stock_names = []
        self.last_written_year = None

