from gameplay import *

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
                research_threshhold = int(value)
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
                part_shape = Bishop()
            elif part_shape_name == "rook":
                part_shape = Rook()
            elif part_shape_name == "knight":
                part_shape = Knight()
            elif part_shape_name == "king":
                part_shape = King()
            elif part_shape_name == "queen":
                part_shape = Queen()
            else:
                raise exception("Unrecognized part_shape value: " + part_shape_name)
        part = None
        if part_name == "locomotor":
            part = Locomotor(size=part_size,
                             quality=part_quality,
                             damage=0,
                             shape_type=part_shape)
        elif part_name == "collector":
            part = Collector(size=part_size,
                             quality=part_quality,
                             damage=0)
        elif part_name == "armament":
            part = Armament(size=part_size,
                             quality=part_quality,
                             damage=0,
                             shape_type=part_shape)
        elif part_name == "researcher":
            part = Researcher(size=part_size,
                             quality=part_quality,
                             damage=0)
        elif part_name == "core":
            part = EnergyCore(size=part_size,
                            quality=part_quality,
                            damage=0,
                            current_energy=0)
        elif part_name == "armor":
            part = Armor(size=part_size,
                         quality=part_quality,
                         damage=0)
        elif part_name == "producer":
            part = Producer(size=part_size,
                            quality=part_quality,
                            damage=0,
                            under_production="",
                            points_to_produce=0,
                            current_production_points=0)
        else:
            raise Exception("Unrecognized part name: " + part_name)
        parts.append(part)
    
    prototype = Unit(image_name=image_name,
                     coords=(-1, -1),
                     size=size,
                     parts=parts,
                     owner_player_number=0,
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
    return ResourcePile(image_name=image_name,
                        coords=coords,
                        size=1,
                        amount=amount)
