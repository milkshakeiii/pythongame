from dataclasses import dataclass
from abc import ABC, abstractmethod

class Gameboard:
    def __init__(self):
        self.squares = dict()

    def add_to_board(self, placeable):
        size = placeable.size
        for i in range(size):
            for j in range(size):
                coords = (placeable.coords[0]+i, placeable.coords[1]+j)
                self.squares[coords] = self.squares.get(coords, []) + [placeable]

    def remove_from_board(self, placeable):
        size = placeable.size
        for i in range(size):
            for j in range(size):
                coords = (placeable.coords[0]+i, placeable.coords[1]+j)
                if not (placeable in self.squares[coords]):
                    raise Exception("Expected placeable not found at " + coords)
                self.squares[coords].remove(placeable)

class ShapeType(ABC):
    @abstractmethod
    def possible_squares(self, origin_unit):
        return NotImplemented

    @abstractmethod
    def move_unit(self, unit, gameboard, direction, distance):
        return NotImplemented

class Bishop(ShapeType):
    def possible_squares(self, origin_unit):
        pass

    def move_unit(self, unit, gameboard, direction, distance):
        pass

class Rook(ShapeType):
    def possible_squares(self, origin_unit):
        pass

    def move_unit(self, unit, gameboard, direction, distance):
        pass

class Knight(ShapeType):
    def possible_squares(self, origin_unit):
        pass

    def move_unit(self, unit, gameboard, direction, distance):
        pass

class King(ShapeType):
    def possible_squares(self, origin_unit):
        pass

    def move_unit(self, unit, gameboard, direction, distance):
        pass

class Queen(ShapeType):
    def possible_squares(self, origin_unit):
        pass

    def move_unit(self, unit, gameboard, direction, distance):
        pass

@dataclass
class Placeable:
    image_name: str
    coords: tuple
    size: int

@dataclass
class ResourcePile(Placeable):
    amount: float

@dataclass
class Unit(Placeable):
    parts: list
    owner_player_number: int

@dataclass
class Part:
    size: int
    quality: float
    damage: int

    def max_hp(self):
        return self.size*10*self.quality

    def display_name(self):
        raise Exception("display_name called on part superclass")

@dataclass
class Locomotor(Part):
    shape_type: ShapeType

    def energy_per_square(self):
        return (1/self.quality)

    def max_squares_traveled(self):
        return self.size*2

    def display_name(self):
        return "Locomotor"

@dataclass
class Collector(Part):
    def max_resources_removed_per_turn(self):
        return self.size

    def resources_gained_per_resources_removed(self):
        return self.quality

    def energy_per_unit_removed(self):
        return (1/self.quality)

    def display_name(self):
        return "Collector"
        
@dataclass
class Armament(Part):
    shape_type: ShapeType

    def range(self):
        return self.size*2

    def energy_cost(self):
        return (1/self.quality) * self.size

    def damage(self):
        return 10

    def display_name(self):
        return "Armament"

@dataclass
class Researcher(Part):
    def research_amount(self):
        return self.size

    def energy_cost(self):
        return (1/self.quality) * self.size

    def display_name(self):
        return "Researcher"

@dataclass
class EnergyCore(Part):
    current_energy: float

    def maximum_energy(self):
        return self.size*10

    def energy_recharge_per_turn(self):
        return self.quality*10

    def display_name(self):
        return "Core"

@dataclass
class Armor(Part):
    def display_name(self):
        return "Armor"

@dataclass
class Producer(Part):
    under_production: str
    points_to_produce: float
    current_production_points: float

    def energy_cost(self):
        return (1/self.quality) * self.size

    def points_per_activation(self):
        return self.size

    def display_name(self):
        return "Producer"
    
