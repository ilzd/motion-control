from input_zone import InputZone

class InputGroup:
    
    def __init__(self, id: int):
        self.id = id
        self.zones = []
    
    def add_zone(self, zone: InputZone):
        self.zones.append(zone)
    
    def remove_zone(self, zone: InputZone):
        self.zones.remove(zone)