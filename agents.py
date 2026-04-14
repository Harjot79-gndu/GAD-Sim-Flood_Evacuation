from mesa import Agent
from logic import get_dynamic_route


class ShelterAgent(Agent):
    def __init__(self, unique_id, model, location, shelter_node, capacity, shelter_type):
        super().__init__(unique_id, model)
        self.location = location
        self.shelter_node = shelter_node
        self.capacity = capacity
        self.shelter_type = shelter_type
        self.occupants = 0
        self.readiness = False
        self.route = []

    def step(self):
        if self.readiness:
            self.route = get_dynamic_route(
                self.model.network,
                self.location,
                self.shelter_node,
                self.model.UT
            )


