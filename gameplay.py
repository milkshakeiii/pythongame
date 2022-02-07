from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from enum import Enum
from copy import deepcopy

class ShapeTypeEnum(Enum):
    BISHOP = 1
    ROOK = 2
    KNIGHT = 3
    KING = 4
    QUEEN = 5

def shape_enum_to_object(enum: ShapeTypeEnum):
    if enum == ShapeTypeEnum.BISHOP:
        return Bishop()
    elif enum == ShapeTypeEnum.ROOK:
        return Rook()
    elif enum == ShapeTypeEnum.KNIGHT:
        return Knight()
    elif enum == ShapeTypeEnum.KING:
        return King()
    elif enum == ShapeTypeEnum.QUEEN:
        return Queen()
    raise "Unrecognized enum"

@dataclass(eq=False)
class Placeable:
    image_name: str
    coords: Tuple[int, int]
    size: int

    def is_resource_pile(self):
        return False

    def is_wall(self):
        return False

    def is_unit(self):
        return False

@dataclass(eq=False)
class Part():
    size: int
    quality: float
    damage: int

    def max_hp(self):
        return int(self.size*10*self.quality)

    def current_hp(self):
        return self.max_hp() - self.damage

    '''
    return actual amount of damage taken
    '''
    def receive_damage(self, amount):
        starting_hp = self.current_hp()
        ending_hp = max(self.current_hp()-amount, 0)
        actual_taken = starting_hp - ending_hp
        self.damage += actual_taken
        return actual_taken
    
    def display_name(self):
        raise Exception("display_name called on part superclass")

    def is_collector(self):
        return False

    def is_researcher(self):
        return False

    def is_producer(self):
        return False

    def is_armament(self):
        return False

    def is_locomotor(self):
        return False

    def is_core(self):
        return False

    def is_armor(self):
        return False

@dataclass(eq=False)
class Unit(Placeable):
    parts: List[Part]
    owner_player_number: int
    owner_team_number: int
    unit_name: str
    production_cost: int
    research_threshhold: float

    def moveable_squares(self):
        result = []
        for part in parts:
            if type(part) is Locomotor:
                shape_type = shape_enum_to_object(part.shape_type)
                result += shape_type.move_paths(self.coords, part.size)
        return result

    def attackable_squares(self):
        result = []
        for part in parts:
            if type(part) is Armament:
                shape_type = shape_enum_to_object(part.shape_type)
                result += shape_type.move_paths(self.coords, part.size)
        return result

    def receive_damage(self, amount):
        for part in self.parts:
            amount -= part.receive_damage(amount)
            # part.receive_damage returns amount taken up to max, so
            # amount will spill over until it becomes 0

    '''
    returns True iff the cost was successfully paid
    '''
    def pay_energy(self, part, action):
        amount_to_pay = action.energy_cost(part)
        
        for part in self.parts:
            if part.is_core():
                amount_to_pay -= part.pay_energy(amount_to_pay)

        return amount_to_pay == 0

    def is_unit(self):
        return True

@dataclass(eq=False)
class Player:
    player_number: int
    team_number: int
    unit_prototypes: List[Unit]
    resource_amount: int
    research_amount: int

    def research_fraction(self):
        return 1-(199/200)**self.research_amount

@dataclass(eq=False)
class Gameboard:
    squares: Dict[Tuple[int, int], List[Placeable]]

    def get_single_occupant(self, square):
        occupants = self.squares.get(square, [])
        occupants = [o for o in occupants if not o.is_resource_pile()]
        if len(occupants) == 0:
            return None
        if len(occupants) == 1:
            return occupants[0]
        raise Exception("Multiple occupants found")

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

def unit_placement_in_bounds(coord, unit_size):
    return (in_bounds(coord)
            and in_bounds((coord[0]+unit_size-1, coord[1]+unit_size-1)))

def in_bounds(coord):
    return coord[0] < 43 and coord[1] < 30 and coord[0] >= 0 and coord[1] >= 0

@dataclass(eq=False)
class Gamestate:
    gameboard: Gameboard
    players: List[Player]

class ShapeType():
    '''
    move_paths implementations return a list of paths
    where a path is a list of coords each of which
    depends on the previous being reachable
    '''
    def move_paths(self, start_coord, part_size, unit_size) -> list:
        return NotImplemented

    '''
    blast_paths returns the same type of data as
    move_paths but each path represents a choice
    of blast direction so the king shape returns
    a single path instead of many length 1 paths
    '''
    def blast_paths(self, start_coord, part_size, unit_size) -> list:
        return self.move_paths(start_coord, part_size, unit_size)

def direct_path_move_path(start_coord, part_size, steps, unit_size):
    result = []
    for step in steps:
        path = []
        current_coord = start_coord
        for i in range(part_size):
            current_coord = (current_coord[0]+step[0],
                             current_coord[1]+step[1])
            if unit_placement_in_bounds(current_coord, unit_size):
                path.append(current_coord)
        result.append(path)
    return result

class Bishop(ShapeType):
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 1), (-1, 1), (1, -1), (-1, -1)],
                                     unit_size)

class Rook(ShapeType):
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 0), (0, 1), (0, -1), (-1, 0)],
                                     unit_size)

class Knight(ShapeType):
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 2), (1, -2), (2, 1), (2, -1),
                                      (-1, 2), (-1, -2), (-2, 1), (-2, -1)],
                                     unit_size)

class King(ShapeType):
    def move_paths(self, start_coord, part_size, unit_size):
        many_paths = []
        for i in range(-part_size, part_size):
            for j in range(-part_size, part_size):
                if (i != 0 or j != 0
                    and unit_placement_in_bounds((i, j), unit_size)):
                    many_paths.append([(i, j)])
        return many_paths

    def blast_paths(self, start_coord, part_size, unit_size):
        blast = []
        for i in range(-part_size, part_size+unit_size):
            for j in range(-part_size, part_size+unit_size):
                candidate = (start_coord[0] + i, start_coord[1] + j)
                if ((not (0 <= i < unit_size and 0 <= j < unit_size))
                    and in_bounds(candidate)):
                    blast.append(candidate)
        return [blast]

class Queen(ShapeType):
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 1), (-1, 1), (1, -1), (-1, -1),
                                      (1, 0), (0, 1), (0, -1), (-1, 0)],
                                     unit_size)
    
@dataclass(eq=False)
class ResourcePile(Placeable):
    amount: float

    def is_resource_pile(self):
        return True

@dataclass(eq=False)
class Wall(Placeable):
    def is_wall(self):
        return True

@dataclass(eq=False)
class Action():
    def energy_cost(self, part):
        return NotImplemented

    def is_armament(self):
        return False

    def is_producer(self):
        return False

    def is_researcher(self):
        return False

@dataclass(eq=False)
class Locomotor(Part):
    shape_type: ShapeTypeEnum

    def energy_per_square(self):
        return (1/self.quality)

    def max_squares_traveled(self):
        return self.size*2

    def display_name(self):
        return "Locomotor"

    def is_locomotor(self):
        return True

@dataclass(eq=False)
class LocomotorAction(Action):
    move_target: Tuple[int, int] # in relative spaces

    def energy_cost(self, locomotor):
        return max(abs(self.move_target[0]), abs(self.move_target[1]))

@dataclass(eq=False)
class Collector(Part):
    def max_resources_removed_per_turn(self):
        return self.size

    def resources_gained_per_resources_removed(self):
        return self.quality

    def energy_cost(self):
        return (1/self.quality) * self.max_resources_removed_per_turn()

    def display_name(self):
        return "Collector"

@dataclass(eq=False)
class CollectorAction(Action):
    def energy_cost(self, collector):
        return collector.energy_cost()
        
@dataclass(eq=False)
class Armament(Part):
    shape_type: ShapeTypeEnum

    def range(self):
        return self.size*2

    def energy_cost(self):
        return (1/self.quality) * self.size

    def damage_dealt(self):
        return 10

    def display_name(self):
        return "Armament"

    def is_armament(self):
        return True

@dataclass(eq=False)
class ArmamentAction(Action):
    blast_index: int

    def energy_cost(self, armament):
        return armament.energy_cost()

    def is_armament(self):
        return True

@dataclass(eq=False)
class Researcher(Part):
    def research_amount(self):
        return self.size

    def energy_cost(self):
        return (1/self.quality) * self.size

    def display_name(self):
        return "Researcher"

    def is_researcher(self):
        return True

@dataclass(eq=False)
class ResearcherAction(Action):
    def energy_cost(self, researcher):
        return researcher.energy_cost()

    def is_researcher(self):
        return True

@dataclass(eq=False)
class EnergyCore(Part):
    current_energy: float

    def maximum_energy(self):
        return self.size*10

    def energy_recharge_per_turn(self):
        return self.quality*10

    def display_name(self):
        return "Core"

    def is_core(self):
        return True

    '''
    pay up to maximum, return actual amount of energy paid
    '''
    def pay_energy(self, amount):
        starting_energy = self.current_energy
        ending_energy = max(self.current_energy-amount, 0)
        actual_paid = starting_energy - ending_energy
        self.current_energy -= actual_paid
        return actual_paid

    def charge(self):
        self.current_energy += self.energy_recharge_per_turn()

    def leak(self):
        self.current_energy = min(self.maximum_energy(), self.current_energy)

@dataclass(eq=False)
class Armor(Part):
    def display_name(self):
        return "Armor"

    def is_armor(self):
        return True

@dataclass(eq=False)
class Producer(Part):
    under_production: Unit
    current_production_points: int

    def size_under_production(self):
        return self.under_production.size

    def points_to_produce(self):
        return self.under_production.production_cost

    def energy_cost(self):
        return (1/self.quality) * self.size

    def points_per_activation(self):
        return self.size

    def next_activation_produces(self):
        if self.under_production == None:
            return None
        current_amount = self.current_production_points
        next_amount = current_amount + self.points_per_activation()
        return next_amount >= self.points_to_produce()

    def spawn_coords(self, spawner_coords, spawner_size, spawnee_size):
        spawn_spots = set()
        for y in [spawner_coords[1]-spawnee_size,
                  spawner_coords[1]+spawner_size]:
            for x in range(spawner_coords[0]-spawnee_size,
                           spawner_coords[0]+spawner_size+1):
                if unit_placement_in_bounds((x, y), spawnee_size):
                    spawn_spots.add((x, y))
        for x in [spawner_coords[0]-spawnee_size,
                  spawner_coords[0]+spawner_size]:
            for y in range(spawner_coords[1]-spawnee_size,
                           spawner_coords[1]+spawner_size+1):
                if unit_placement_in_bounds((x, y), spawnee_size):
                    spawn_spots.add((x, y))
        return spawn_spots

    def display_name(self):
        return "Producer"

    def is_producer(self):
        return True

@dataclass(eq=False)
class ProducerAction(Action):
    produced_unit: Unit
    out_coords: tuple

    def energy_cost(self, producer):
        return producer.energy_cost()

    def is_producer(self):
        return True

def build_gameturn(players):
    dictionary = dict()
    for player in players:
            dictionary[player] = dict()
    return Gameturn(players_to_units_to_parts_to_actions=dictionary)

@dataclass(eq=False)
class Gameturn:
    players_to_units_to_parts_to_actions: Dict[Player,
                                               Dict[Unit,
                                                    Dict[Part, Action]]]

    def add_action(self, player, unit, part, action):
        self[player][unit] = self[player].get(unit, dict())
        self[player][unit][part] = action

    def remove_action(self, player, unit, part):
        del self[player][unit][part]

    def part_active(self, player, unit, part):
        return (unit in self[player]) and (part in self[player][unit])

    def __getitem__(self, key):
        return self.players_to_units_to_parts_to_actions[key]

    def __setitem__(self, key, value):
        self.players_to_units_to_parts_to_actions[key] = value

    def unit_pending_true_max_gain_energy(self, player, unit):
        parts = unit.parts
        max_energy = 0
        true_energy = 0
        gain_energy = 0
        for part in parts:
            if type(part) == EnergyCore:
                max_energy += part.maximum_energy()
                true_energy += part.current_energy
                gain_energy += part.energy_recharge_per_turn()

        pending_energy = true_energy
        for part, action in self[player].get(unit, dict()).items():
            pending_energy -= action.energy_cost(part)

        return (pending_energy, true_energy, max_energy, gain_energy)

def merge_turns(turns):
    merged_turn = build_gameturn([])
    for turn in turns:
        for player in turn.players_to_units_to_parts_to_actions:
            merged_turn[player] = turn[player]
    return merged_turn

def default_turn_for(gamestate, player):
    return build_gameturn(gamestate.players) # TODO

def advance_gamestate_via_mutation(gamestate, do_turn):
    def do_blast():
        shape_type = shape_enum_to_object(part.shape_type)
        for path in shape_type.blast_paths(unit.coords, part.size, unit.size):
            for square in path:
                occupant = gamestate.gameboard.get_single_occupant(square)
                if not occupant:
                    continue
                elif occupant.is_wall():
                    break
                elif occupant.is_unit():
                    occupant.receive_damage(part.damage_dealt())

    def do_production():
        part.under_production = action.produced_unit
        if part.next_activation_produces():
            new_unit = deepcopy(action.produced_unit)
            new_unit.coords = action.out_coords
            gamestate.gameboard.add_to_board(new_unit)
            part.current_production_points = 0
            part.under_production = None
        else:
            part.current_production_points += part.points_per_activation()

    def do_research():
        pass

    turn_dict = do_turn.players_to_units_to_parts_to_actions

    # energy gain
    charged_parts = set()
    for placeables in gamestate.gameboard.squares.values():
        for placeable in placeables:
            if placeable.is_unit():
                for part in placeable.parts:
                    if part.is_core():
                        if part not in charged_parts:
                            part.charge()
                            charged_parts.add(part)

    # research
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if action.is_researcher() and unit.pay_energy(part, action):
                    do_research()

    # armaments
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if action.is_armament() and unit.pay_energy(part, action):
                    do_blast()

    # producers
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if action.is_producer() and unit.pay_energy(part, action):
                    do_production()

    # energy leak
    for placeables in gamestate.gameboard.squares.values():
        for placeable in placeables:
            if placeable.is_unit():
                for part in placeable.parts:
                    if part.is_core():
                        part.leak()                    

    return gamestate
