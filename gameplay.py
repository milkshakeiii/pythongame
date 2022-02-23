from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum
from copy import deepcopy
from uuid import UUID, uuid4
from random import Random

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
class NetHashable:
    uuid: UUID

    def evolve_uuid(self, seed):
        rng = Random()
        rng.seed(seed)
        self.uuid = UUID(int=rng.getrandbits(128))
    
    def __eq__(self, other):
        if (other == None):
            return False
        return self.uuid == other.uuid

    def __hash__(self):
        return int(self.uuid)
        

@dataclass(eq=False)
class Placeable(NetHashable):
    image_name: str
    coords: Tuple[int, int]
    size: int

    def is_resource_pile(self):
        return False

    def is_wall(self):
        return False

    def is_unit(self):
        return False

PartType = Union['Producer',
                 'EnergyCore',
                 'Researcher',
                 'Armament',
                 'Collector',
                 'Locomotor',
                 'Armor',]

@dataclass(eq=False)
class Part(NetHashable):
    size: int
    quality: float
    damage: int

    def display_name(self):
        raise Exception("Part superclass has no display name.")

    def max_hp(self):
        return int(self.size*10*self.quality)

    def current_hp(self):
        return self.max_hp() - self.damage

    def is_functional(self):
        return self.current_hp() > 0

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
    parts: List[PartType]
    owner_player_number: int
    owner_team_number: int
    unit_name: str
    production_cost: int
    research_threshhold: float

    def set_owner(self, owner):
        self.owner_player_number = owner.player_number
        self.owner_team_number = owner.team_number

    def summed_hp(self):
        result = 0
        for part in self.parts:
            result += part.max_hp() - part.damage
        return result

    def is_destroyed(self):
        return self.summed_hp() == 0

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

    def try_pay_energy(self, part, action):
        amount_to_pay = action.energy_cost(part)

        amount_available = 0
        for core in self.parts:
            if core.is_core():
                amount_available += core.current_energy

        if (amount_available >= amount_to_pay):
            self.pay_energy(part, action)
            return True
        return False
        

    def is_unit(self):
        return True

    def movement_priority(self):
        return (self.size,
                sum([part.size for part in self.parts]),
                self.owner_player_number)

def get_mothership_prototype(player):
    for unit in player.unit_prototypes:
        if unit.research_threshhold == 0 and unit.production_cost == 0:
            return unit
    raise Exception("No mothership found.")

def get_mothership(player):
    mothership_prototype = get_mothership_prototype(player)
    mothership = copy.deepcopy(mothership_prototype)
    mothership.set_owner(player)
    mothership.uuid = uuid4()
    return mothership

@dataclass(eq=False)
class Player(NetHashable):
    player_number: int
    team_number: int
    unit_prototypes: List[Unit]
    resource_amount: float
    research_amount: int

    def research_fraction(self):
        return 1-(199/200)**self.research_amount

    '''
    returns True iff the cost is successfully paid
    '''
    def pay_for_unit(self, unit):
        if self.resource_amount >= unit.production_cost:
            self.resource_amount -= unit.production_cost
            return True
        return False

    def unit_unlocked(self, unit):
        return self.research_fraction() >= unit.research_threshhold

@dataclass(eq=False)
class Gameboard:
    squares: Dict[Tuple[int, int], List[Union['Unit', 'ResourcePile', 'Wall']]]

    def prune_transporter_clones(self):
        originals = dict()
        new_squares = dict()
        for coords, placeables in self.squares.items():
            new_squares[coords] = list()
            for placeable in placeables:
                if placeable not in originals:
                    originals[placeable] = placeable
                new_squares[coords].append(originals[placeable])
        self.squares = new_squares

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
                    raise Exception("Expected placeable not found at " +
                                    str(coords))
                self.squares[coords].remove(placeable)

    def conflicts_exist(self):
        for placeables in self.squares.values():
            units = [p for p in placeables if p.is_unit()]
            if len(units) > 1:
                return True
        return False

    def adding_would_cause_conflict(self, placeable):
        self.add_to_board(placeable)
        result = self.conflicts_exist()
        self.remove_from_board(placeable)
        return result
        

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
    def display_name(self):
        raise Exception("ShapeType superclass has no display name.")
    
    '''
    move_paths implementations return a list of paths
    where a path is a list of coords each of which
    depends on the previous being reachable
    '''
    def move_paths(self, start_coord, part_size, unit_size) -> list:
        raise Exception("move_paths called on ShapeType superclass.")

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
    def display_name(self):
        return "Bishop"
    
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 1), (-1, 1), (1, -1), (-1, -1)],
                                     unit_size)

class Rook(ShapeType):
    def display_name(self):
        return "Rook"
    
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 0), (0, 1), (0, -1), (-1, 0)],
                                     unit_size)

class Knight(ShapeType):
    def display_name(self):
        return "Knight"
    
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 2), (1, -2), (2, 1), (2, -1),
                                      (-1, 2), (-1, -2), (-2, 1), (-2, -1)],
                                     unit_size)

class King(ShapeType):
    def display_name(self):
        return "King"
    
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
    def display_name(self):
        return "Queen"
    
    def move_paths(self, start_coord, part_size, unit_size):
        return direct_path_move_path(start_coord,
                                     part_size,
                                     [(1, 1), (-1, 1), (1, -1), (-1, -1),
                                      (1, 0), (0, 1), (0, -1), (-1, 0)],
                                     unit_size)
    
@dataclass(eq=False)
class ResourcePile(Placeable):
    amount: int

    def is_resource_pile(self):
        return True

    '''
    return actual amount yielded
    '''
    def yield_resources(self, amount_to_yield) -> int:
        yielded = min(self.amount, amount_to_yield)
        self.amount -= yielded
        return yielded

@dataclass(eq=False)
class Wall(Placeable):
    def is_wall(self):
        return True

ActionType = Union['ProducerAction',
                   'ResearcherAction',
                   'ArmamentAction',
                   'CollectorAction',
                   'LocomotorAction']

@dataclass(eq=False)
class Action():
    def energy_cost(self, part):
        raise Exception("energy_cost called on Action superclass")

    def is_armament(self):
        return False

    def is_producer(self):
        return False

    def is_researcher(self):
        return False

    def is_collector(self):
        return False

    def is_locomotor(self):
        return False

@dataclass(eq=False)
class Armor(Part):
    def display_name(self):
        return "Armor"

    def is_armor(self):
        return True

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

def locomotor_action_factory(move_target):
    return LocomotorAction(move_target=move_target)

@dataclass(eq=False)
class LocomotorAction(Action):
    move_target: Tuple[int, int] # in relative spaces

    def energy_cost(self, locomotor):
        return max(abs(self.move_target[0]), abs(self.move_target[1]))

    def is_locomotor(self):
        return True

@dataclass(eq=False)
class Collector(Part):
    spot_1_decoy: int
    spot_2_decoy: int
    
    def max_resources_removed_per_turn(self) -> int:
        return self.size

    def resources_gained_per_resources_removed(self) -> float:
        return self.quality

    def energy_cost(self):
        return (1/self.quality) * self.max_resources_removed_per_turn()

    def display_name(self):
        return "Collector"

    def is_collector(self):
        return True

def collector_action_factory():
    return CollectorAction(spot_1_decoy=0,
                           spot_2_decoy=0)

@dataclass(eq=False)
class CollectorAction(Action):
    spot_1_decoy: int
    spot_2_decoy: int
    
    def energy_cost(self, collector):
        return collector.energy_cost()

    def is_collector(self):
        return True
        
@dataclass(eq=False)
class Armament(Part):
    shape_type: ShapeTypeEnum

    spot_2_decoy: int
    spot_3_decoy: int

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

def armament_action_factory(blast_index):
    return ArmamentAction(blast_index=blast_index,
                          spot_2_decoy=0,
                          spot_3_decoy=0)

@dataclass(eq=False)
class ArmamentAction(Action):
    blast_index: int

    spot_2_decoy: int
    spot_3_decoy: int

    def energy_cost(self, armament):
        return armament.energy_cost()

    def is_armament(self):
        return True

@dataclass(eq=False)
class Researcher(Part):
    spot_1_decoy: int
    spot_2_decoy: int
    spot_3_decoy: int
    spot_4_decoy: int
    
    def research_amount(self):
        return self.size

    def energy_cost(self):
        return (1/self.quality) * self.size

    def display_name(self):
        return "Researcher"

    def is_researcher(self):
        return True

def researcher_action_factory():
    return ResearcherAction(spot_1_decoy=0,
                            spot_2_decoy=0,
                            spot_3_decoy=0,
                            spot_4_decoy=0)

@dataclass(eq=False)
class ResearcherAction(Action):
    spot_1_decoy: int
    spot_2_decoy: int
    spot_3_decoy: int
    spot_4_decoy: int
    
    def energy_cost(self, researcher):
        return researcher.energy_cost()

    def is_researcher(self):
        return True

@dataclass(eq=False)
class EnergyCore(Part):
    current_energy: float
    spot_2_decoy: int
    spot_3_decoy: int
    spot_4_decoy: int
    spot_5_decoy: int

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
        current = self.current_energy
        actual_paid = current if current < amount else amount
        self.current_energy -= actual_paid
        return actual_paid

    def charge(self):
        self.current_energy += self.energy_recharge_per_turn()

    def leak(self):
        self.current_energy = min(self.maximum_energy(), self.current_energy)

@dataclass(eq=False)
class Producer(Part):
    under_production: Optional[Unit]
    current_production_points: int
    evolved_uuids_counter: int
    spot_4_decoy: int
    spot_5_decoy: int
    spot_6_decoy: int

    def get_evolved_uuid_seed(self):
        self.evolved_uuids_counter += 1
        return int(self.uuid) * self.evolved_uuids_counter

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

    def action_produces(self, action):
        current_amount = self.current_production_points
        next_amount = current_amount + self.points_per_activation()
        return next_amount >= action.produced_unit.production_cost

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

def producer_action_factory(produced_unit, out_coords):
    return ProducerAction(produced_unit=produced_unit,
                          out_coords=out_coords,
                          spot_3_decoy=0,
                          spot_4_decoy=0,
                          spot_5_decoy=0,
                          spot_6_decoy=0)

@dataclass(eq=False)
class ProducerAction(Action):
    produced_unit: Unit
    out_coords: Tuple[int, int]
    spot_3_decoy: int
    spot_4_decoy: int
    spot_5_decoy: int
    spot_6_decoy: int

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
                                                    Dict[PartType, ActionType]]]

    def add_action(self, player, unit, part, action):
        self[player][unit] = self[player].get(unit, dict())
        self[player][unit][part] = action

    def remove_action(self, player, unit, part):
        del self[player][unit][part]

    def part_active(self, player, unit, part):
        return (unit in self[player]) and (part in self[player][unit])

    def contains_player(self, player):
        return (player in self.players_to_units_to_parts_to_actions)

    def __getitem__(self, key):
        return self.players_to_units_to_parts_to_actions[key]

    def __setitem__(self, key, value):
        self.players_to_units_to_parts_to_actions[key] = value

    def align_net_objects(self, gamestate):
        new_dict = {}
        for player, unit_dict in self.players_to_units_to_parts_to_actions.items():
            replacement_player = None
            for candidate_player in gamestate.players:
                if candidate_player == player:
                    replacement_player = candidate_player
            if replacement_player == None:
                raise Exception("Expected player not found in gamestate.")
            new_dict[replacement_player] = dict()
            for unit, part_dict in unit_dict.items():
                placeables = gamestate.gameboard.squares[unit.coords]
                replacement_unit = None
                for placeable in placeables:
                    if placeable == unit:
                        replacement_unit = placeable
                if replacement_unit == None:
                    raise Exception("Unit from turn not found on gameboard")
                new_dict[player][replacement_unit] = dict()
                for part, action in part_dict.items():
                    replacement_part = None
                    for replacement_candidate in replacement_unit.parts:
                        if replacement_candidate == part:
                            replacement_part = replacement_candidate
                    if replacement_part == None:
                        raise Exception("Expected part not found.")
                    new_dict[replacement_player][replacement_unit][replacement_part] = action

        self.players_to_units_to_parts_to_actions = new_dict
                    

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

'''
higher indexed player turns overwrite lower indexed ones if duplicates exist
'''
def merge_turns(turns):
    merged_turn = build_gameturn([])
    for turn in turns:
        for player in turn.players_to_units_to_parts_to_actions:
            merged_turn[player] = turn[player]
    return merged_turn

def default_turn_for(gamestate, player, working_turn):
    default_turn = build_gameturn([player])
    for unit in working_turn[player]:
        for part in working_turn[player][unit]:
            action = working_turn[player][unit][part]
            if action.is_researcher():
                new_action = researcher_action_factory()
                default_turn.add_action(player, unit, part, new_action)
            elif action.is_collector():
                new_action = collector_action_factory()
                default_turn.add_action(player, unit, part, new_action)
            elif (action.is_producer() and
                  part.under_production == action.produced_unit):
                new_action = producer_action_factory(action.produced_unit,
                                                     action.out_coords)
                default_turn.add_action(player, unit, part, new_action)
    return default_turn

def unit_production_legal(builder, buildee, player):
    unit_unlocked = player.unit_unlocked(buildee)
    smaller_size =  buildee.size < builder.size
    one_making_six = (builder.size == 1 and buildee.size == 6)
    size_appropriate = smaller_size or one_making_six
    enough_resources = player.resource_amount >= buildee.production_cost
    return unit_unlocked and size_appropriate and enough_resources

def advance_gamestate_via_mutation(gamestate, do_turn):
    do_turn.align_net_objects(gamestate)
    
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
        if (part.under_production != action.produced_unit):
            if unit_production_legal(unit, action.produced_unit, player):
                player.pay_for_unit(action.produced_unit)
            else:
                return
            
        part.under_production = action.produced_unit
        if part.next_activation_produces():
            new_unit = deepcopy(action.produced_unit)
            new_unit.evolve_uuid(part.get_evolved_uuid_seed())
            for new_part in new_unit.parts:
                new_part.evolve_uuid(part.get_evolved_uuid_seed())
            new_unit.coords = action.out_coords
            new_unit.owner_player_number = unit.owner_player_number
            new_unit.owner_team_number = unit.owner_team_number
            if not gamestate.gameboard.adding_would_cause_conflict(new_unit):
                gamestate.gameboard.add_to_board(new_unit)
                part.current_production_points = 0
                part.under_production = None
        else:
            part.current_production_points += part.points_per_activation()

    def do_research():
        player.research_amount += part.research_amount()

    def do_collection():
        resource_piles = []
        covered_coords = []
        for i in range(unit.size):
            for j in range(unit.size):
                covered_coords.append((unit.coords[0]+i,
                                       unit.coords[1]+j))
        gatherable = part.max_resources_removed_per_turn()
        for coord in covered_coords:
            placeables = gamestate.gameboard.squares[coord]
            for placeable in placeables:
                if placeable.is_resource_pile():
                    gatherable -= placeable.yield_resources(gatherable)
                    if placeable.amount == 0:
                        gamestate.gameboard.remove_from_board(placeable)
        gathered = part.max_resources_removed_per_turn() - gatherable
        ratio = part.resources_gained_per_resources_removed()
        player.resource_amount += gathered * ratio
                
        

    turn_dict = do_turn.players_to_units_to_parts_to_actions

    # energy gain
    charged_parts = set()
    for placeables in gamestate.gameboard.squares.values():
        for placeable in placeables:
            if placeable.is_unit():
                for part in placeable.parts:
                    if part.is_core() and part.is_functional():
                        if part not in charged_parts:
                            part.charge()
                            charged_parts.add(part)

    # researchers
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if (action.is_researcher() and
                    part.is_functional() and
                    unit.try_pay_energy(part, action)):
                    do_research()

    # collectors
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if (action.is_collector() and
                    part.is_functional() and
                    unit.try_pay_energy(part, action)):
                    do_collection()

    # armaments
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if (action.is_armament() and
                    part.is_functional() and
                    unit.try_pay_energy(part, action)):
                    do_blast()

    # producers
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if (action.is_producer() and
                    part.is_functional() and
                    unit.try_pay_energy(part, action)):
                    do_production()

    # removal of destroyed units
    for placeables in gamestate.gameboard.squares.values():
        for placeable in placeables:
            if placeable.is_unit():
                if placeable.is_destroyed():
                    gamestate.gameboard.remove_from_board(placeable)
                    for player in turn_dict:
                        if placeable in turn_dict[player]:
                            del turn_dict[player][placeable]

    ### movement ###
    start_squares = {}
    blocked_squares = set()
    stationary_units = set()
    moving_units = set()
    #fill moving_units
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if (action.is_locomotor() and
                    part.is_functional() and
                    unit.try_pay_energy(part, action)):
                    moving_units.add(unit)

    #fill blocked_squares and start_squares and stationary_units
    for coords, placeables in gamestate.gameboard.squares.items():
        for placeable in placeables:
            if placeable.is_unit():
                start_squares[placeable] = placeable.coords
                if placeable not in moving_units:
                    stationary_units.add(placeable)
                    blocked_squares.add(coords)
                    continue
            if placeable.is_wall():
                blocked_squares.add(coords)

    def path_clear():
        return True # TODO

    # move all units to their destination if not blocked
    for player in turn_dict:
        for unit in turn_dict[player]:
            for part in turn_dict[player][unit]:
                action = turn_dict[player][unit][part]
                if action.is_locomotor() and unit in moving_units:
                    if path_clear():
                        gamestate.gameboard.remove_from_board(unit)
                        unit.coords = (unit.coords[0] + action.move_target[0],
                                       unit.coords[1] + action.move_target[1])
                        gamestate.gameboard.add_to_board(unit)

    while gamestate.gameboard.conflicts_exist():
        # while overlap exists, unmove everyone but the highest priority unit
        for coords, placeables in gamestate.gameboard.squares.items():
            units = [p for p in placeables if p.is_unit()]
            if len(units) <= 1:
                continue
            highest_priority = max(units,
                                   key=lambda unit: (unit in stationary_units,
                                                     unit.movement_priority()))
            units.remove(highest_priority) # the highest priority unit can stay
            for unit in units:
                # others' movements fail
                gamestate.gameboard.remove_from_board(unit)
                unit.coords = start_squares[unit]
                gamestate.gameboard.add_to_board(unit)
                moving_units.remove(unit)
                stationary_units.add(unit)
    ### end movement ###

    # energy leak
    for part in charged_parts:
        part.leak()

    return gamestate

