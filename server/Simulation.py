from datetime import datetime

class Simulation:
    def __init__(self, start_date_time: datetime, step_size: str):
        self.start_date_time = start_date_time
        self.step_size = step_size
        self.current_date_time = start_date_time
        self.aggregated_biomass = {}
        self.aggregated_catch_dictionary = {}

