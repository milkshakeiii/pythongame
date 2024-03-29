import os

from gameplay import *
from uuid import uuid4

def player_from_team(team_name):

    unit_filenames = os.listdir("teams/"+team_name)

    unit_names = []
    for unit_filename in unit_filenames:
        if unit_filename[-5:] != ".unit":
            raise Exception("Unexpected filetype: " + unit_filename)
        unit_names.append(unit_filename[:-5])
    
    prototypes = [unit_prototype_from_file(team_name, unit_name) for
                  unit_name in unit_names]

    player = Player(uuid=uuid4(),
                    player_number=0,
                    team_number=0,
                    unit_prototypes=prototypes,
                    resource_amount=20,
                    research_amount=0)

    return player
    

def unit_prototype_from_file(team_name, unit_name):
    filename = "teams/"+team_name+"/"+unit_name+".unit"
    entries = []
    try:
        with open(filename) as file:
            lines = file.read().split('\n')
            split_lines = [line.split(':') for line in lines]
            entries = [(line[0].strip(),
                        line[1].strip()) for line in split_lines]
    except:
        raise Exception("Error parsing file: " + filename)

    image_name = None
    size = None
    production_cost = None
    research_threshhold = None
    part_names = []
    part_sizes = []
    part_qualities = []
    part_shape_names = []

    for key, value in entries:
        if key == "image":
            image_name = value
        elif key == "size":
            try:
                size = int(value)
            except:
                raise Exception("Error parsing size value.")
        elif key == "production_cost":
            try:
                production_cost = int(value)
            except:
                raise Exception("Error parsing production_cost value.")
        elif key == "research_threshhold":
            try:
                research_threshhold = float(value)
            except:
                raise Exception("Error parsing research_threshhold value.")
        elif key == "part":
            part_names.append(value)
        elif key == "part_size":
            part_size = None
            try:
                part_size = int(value)
            except:
                raise Exception("Error parsing part_size value.")
            part_sizes.append(part_size)
        elif key == "part_quality":
            part_quality = None
            try:
                part_quality = float(value)
            except:
                raise Exception("Error parsing part_quality value.")
            part_qualities.append(part_quality)            
        elif key == "part_shape":
            part_shape_names.append(value)
        else:
            raise Exception("Unrecognized key in unit file: " + key)

    parts = []
    for part_name in part_names:
        part_size = part_sizes.pop(0)
        part_quality = part_qualities.pop(0)
        part_shape = None
        if part_name in ["locomotor", "armament"]:
            part_shape_name = part_shape_names.pop(0)
            part_shape = None
            if part_shape_name == "bishop":
                part_shape = ShapeTypeEnum.BISHOP
            elif part_shape_name == "rook":
                part_shape = ShapeTypeEnum.ROOK
            elif part_shape_name == "knight":
                part_shape = ShapeTypeEnum.KNIGHT
            elif part_shape_name == "king":
                part_shape = ShapeTypeEnum.KING
            elif part_shape_name == "queen":
                part_shape = ShapeTypeEnum.QUEEN
            else:
                raise exception("Unrecognized part_shape value: " + part_shape_name)
        part = None
        if part_name == "locomotor":
            part = Locomotor(uuid=uuid4(),
                             size=part_size,
                             quality=part_quality,
                             damage=0,
                             shape_type=part_shape)
        elif part_name == "collector":
            part = Collector(uuid=uuid4(),
                             size=part_size,
                             quality=part_quality,
                             damage=0,
                             spot_1_decoy=0,
                             spot_2_decoy=0,)
        elif part_name == "armament":
            part = Armament(uuid=uuid4(),
                            size=part_size,
                            quality=part_quality,
                            damage=0,
                            shape_type=part_shape,
                            spot_2_decoy=0,
                            spot_3_decoy=0,)
        elif part_name == "researcher":
            part = Researcher(uuid=uuid4(),
                              size=part_size,
                              quality=part_quality,
                              damage=0,
                              spot_1_decoy=0,
                              spot_2_decoy=0,
                              spot_3_decoy=0,
                              spot_4_decoy=0,)
        elif part_name == "core":
            part = EnergyCore(uuid=uuid4(),
                              size=part_size,
                              quality=part_quality,
                              damage=0,
                              current_energy=0,
                              spot_2_decoy=0,
                              spot_3_decoy=0,
                              spot_4_decoy=0,
                              spot_5_decoy=0,)
        elif part_name == "armor":
            part = Armor(uuid=uuid4(),
                         size=part_size,
                         quality=part_quality,
                         damage=0)
        elif part_name == "producer":
            part = Producer(uuid=uuid4(),
                            size=part_size,
                            quality=part_quality,
                            damage=0,
                            under_production=None,
                            current_production_points=0,
                            evolved_uuids_counter=0,
                            spot_4_decoy=0,
                            spot_5_decoy=0,
                            spot_6_decoy=0,)
        else:
            raise Exception("Unrecognized part name: " + part_name)
        parts.append(part)
    
    prototype = Unit(uuid=uuid4(),
                     image_name=image_name,
                     coords=(-1, -1),
                     size=size,
                     parts=parts,
                     owner_player_number=0,
                     owner_team_number=0,
                     unit_name=unit_name,
                     production_cost=production_cost,
                     research_threshhold=research_threshhold)
    return prototype

def resource_pile_factory(coords, amount):
    image_name = "big_resource"
    if amount < 60:
        image_name = "medium_resource"
    if amount < 30:
        image_name = "small_resource"
    return ResourcePile(uuid=uuid4(),
                        image_name=image_name,
                        coords=coords,
                        size=1,
                        amount=amount)
