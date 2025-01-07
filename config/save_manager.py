import tkinter as tk
import json
import os
from tkinter import filedialog
from .save_data import SaveData
from input_zone import InputZone


class SaveManager:
    last_save_path = "last_save.ini"

    def __init__(self):
        root = tk.Tk()
        root.withdraw()

    def get_load_file(self):
        return filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./config/saves/"
        )

    def load(self, file_path: str = None):
        if file_path is None:
            file_path = self.get_load_file()
            self.set_last_save(file_path)
        
        if not file_path:
            return

        with open(file_path, "r") as file:
            save_dict = json.loads(file.read())
            saved_zones = save_dict["zones"]
            zones = []
            for z in saved_zones:
                newZone = InputZone(z["x1"], z["y1"], z["x2"], z["y2"], key=z["key"],
                                    inverted=z["inverted"], group=z["group"], priority=z["priority"])
                zones.append(newZone)
            return SaveData(zones)

    def get_save_file(self):
        return filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./config/saves/"
        )

    def save(self, data: SaveData):
        file_path = self.get_save_file()
        if not file_path:
            return

        self.set_last_save(file_path)
        with open(file_path, "w") as file:
            save_dict = data.to_dict()
            file.write(json.dumps(save_dict))

    def get_last_save(self):
        if not os.path.exists(self.last_save_path):
            return

        with open(self.last_save_path, "r") as file:
            return file.readline()

    def set_last_save(self, file_path: str):
        with open(self.last_save_path, "w") as file:
            file.write(file_path)
