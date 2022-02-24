import game_io
import gameplay

team_name = input("Welcome to the valuator.  Please input a team name to calculate a team value: ")
player = game_io.player_from_team(team_name)
mothership = gameplay.get_mothership_prototype(player)
other_units = [unit for unit in player.unit_prototypes if unit != mothership]

def indented_print(message, indentation):
    print(" "*indentation + message)

def base_cost(unit, indentation):
    total_cost = 0
    size_cost = 10*(unit.size**(1.5))
    total_cost += size_cost
    indented_print("Size: " + str(unit.size) + ". Cost: " + str(size_cost),
                   indentation)
    for part in unit.parts:
        part_message = part.display_name()
        if part.is_locomotor() or part.is_armament():
            shape_type = gameplay.shape_enum_to_object(part.shape_type)
            part_message += " (" + shape_type.display_name() + ")"
        part_message += " Size: " + str(part.size)
        part_message += " Quality: " + str(part.quality)
        cost = 10 + max(0, (part.size - unit.size) * 4)
        cost *= (part.quality + 0.5)
        part_message += " Cost: " + str(cost)
        indented_print(part_message, indentation+2)
        total_cost += cost
    indented_print("Base cost: " + str(total_cost), indentation)
    return total_cost

print("Valuating " + mothership.unit_name + " (mother unit)...")
base_mothership_cost = base_cost(mothership, 2)
adjusted_mothership_cost = base_mothership_cost + (base_mothership_cost-100) * 0.5
print("After mother adjustment: " + str(adjusted_mothership_cost))

print("Valuating regular units...")
others_sum = 0
for unit in other_units:
    print("Valuating " + unit.unit_name + "...")
    unchanged_cost = base_cost(unit, 2)
    cost = unchanged_cost
    expected_research_threshhold = 1 - 0.95**cost
    cost *= (expected_research_threshhold / (unit.research_threshhold+1))
    print("After research threshhold adjustment: " + str(cost))
    expected_production_cost = (unit.size
                                + sum([part.size for part in unit.parts]))
    cost += (expected_production_cost / unit.production_cost) * unchanged_cost
    print("After production cost adjustment: " + str(cost))
    others_sum += cost

print("Sum of other units' costs: " + str(others_sum))
unit_count_factor = 11 / (6 + len(other_units))
print("Final team value after unit count adjustment: "
      + str(others_sum * unit_count_factor))
    
