class InputZone:
    
    def __init__(self, x1, y1, x2, y2, *, key, inverted, group = None, priority = 0):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.key = key
        self.inverted = inverted
        self.group = group
        self.priority = priority
        self.pressed = False
    
    def set_size(self, w, h):
        self.x2 = self.x1 + w
        self.y2 = self.y1 + h
    
    def set_position(self, x, y):
        difX = x - self.x1
        difY = y - self.y1
        self.x1 += difX
        self.y1 += difY
        self.x2 += difX
        self.y2 += difY
    
    def get_w(self):
        return self.x2 - self.x1
    
    def get_h(self):
        return self.y2 - self.y1
    
    