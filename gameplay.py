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

def in_bounds(coord):
    return coord[0] < 43 and coord[1] < 30 and coord[0] >= 0 and coord[1] >= 0

class Gamestate:
    def __init__(self, gameboard, players):
        self.gameboard = gameboard
        self.players = players

class Player:
    def __init__(self,
                 player_number,
                 team_number,
                 unit_prototypes,
                 resource_amount = 0,
                 research_amount = 0.00):
        self.player_number = player_number
        self.team_number = team_number
        self.unit_prototypes = unit_prototypes
        self.resource_amount = resource_amount
        self.research_amount = research_amount

    def research_fraction(self):
        return 1-(199/200)**self.research_amount

class ShapeType(ABC):
    '''
    move_paths implementations return a list of paths
    where a path is a list of coords each of which
    depends on the previous being reachable
    '''
    @abstractmethod
    def move_paths(self, start_coord, part_size) -> list:
        return NotImplemented

    '''
    blast_paths returns the same type of data as
    move_paths but each path represents a choice
    of blast direction so the king shape returns
    a single path instead of many length 1 paths
    '''
    def blast_paths(self, start_coord, part_size) -> list:
        return self.move_paths(start_coord, part_size)

def direct_path_move_path(start_coord, part_size, steps):
    result = []
    for step in steps:
        path = []
        current_coord = start_coord
        for i in range(part_size):
            current_coord = (current_coord[0]+step[0],
                             current_coord[1]+step[1])
            if in_bounds(current_coord):
                path.append(current_coord)
        result.append(path)
    return result

class Bishop(ShapeType):
    def move_paths(self, start_coord, part_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 1), (-1, 1), (1, -1), (-1, -1)])
                
                

class Rook(ShapeType):
    def move_paths(self, start_coord, part_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 0), (0, 1), (0, -1), (-1, 0)])

class Knight(ShapeType):
    def move_paths(self, start_coord, part_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 2), (1, -2), (2, 1), (2, -1),
                                      (-1, 2), (-1, -2), (-2, 1), (-2, -1)])
    
class King(ShapeType):
    def move_paths(self, start_coord, part_size):
        many_paths = []
        for i in range(part_size+1):
            for j in range(part_size+1):
                if not (i == 0 and j == 0) and in_bounds((i, j)):
                    many_paths.append([(i, j)])
        return many_paths

    def blast_paths(self, start_coord, part_size):
        return [path[0] for path in self.move_paths(start_coord, part_size)]
    
class Queen(ShapeType):
    def move_paths(self, start_coord, part_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 1), (-1, 1), (1, -1), (-1, -1),
                                      (1, 0), (0, 1), (0, -1), (-1, 0)])
    
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
    unit_name: str
    production_cost: int
    research_threshhold: float

    def moveable_squares(self):
        result = []
        for part in parts:
            if type(part) is Locomotor:
                result += part.shape_type.move_paths(self.coords, part.size)
        return result

    def attackable_squares(self):
        result = []
        for part in parts:
            if type(part) is Armament:
                result += part.shape_type.move_paths(self.coords, part.size)
        return result

@dataclass
class Part:
    size: int
    quality: float
    damage: int

    def max_hp(self):
        return int(self.size*10*self.quality)

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
    
class Gameturn:
    def __init__(self):
        self.players_to_coords_to_actions = dict()








        
