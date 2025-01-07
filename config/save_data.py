from input_zone import InputZone


class SaveData:
    def __init__(self, zones: list[InputZone]):
        self.zones = zones

    def to_dict(self):
        save_dict = {}
        zones_dict_list = []
        for zone in self.zones:
            zones_dict_list.append(zone.__dict__)

        save_dict["zones"] = zones_dict_list
        return save_dict
