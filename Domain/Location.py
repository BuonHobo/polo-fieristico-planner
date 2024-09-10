from typing import Self

class Location:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def distance(self, other: Self) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
