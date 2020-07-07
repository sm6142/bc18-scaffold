import battlecode as bc
import random
import sys
import traceback
import time

import os
print(os.getcwd())

print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
directions = list(bc.Direction)
mars_map = gc.starting_map(bc.Planet.Mars)
earth_map = gc.starting_map(bc.Planet.Earth)

print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Healer)

my_team = gc.team()

def try_produce_robot(factory_id):
    rangers = 0
    healers = 0
    for unit in gc.my_units():
        if unit.unit_type == bc.UnitType.Healer:
            healers += 1
        elif unit.unit_type == bc.UnitType.Ranger:
            rangers += 1
    # We want to make some workers, and then ranger/healer pairs
    if rangers > healers:
        unitType = bc.UnitType.Healer
    elif random.randrange(10) < 2:
        unitType = bc.UnitType.Worker
    elif random.randrange(10) < 10:
        unitType = bc.UnitType.Knight
    else:
        unitType = bc.UnitType.Ranger
    if gc.can_produce_robot(factory_id, unitType):
        gc.produce_robot(factory_id, unitType)
        print('id:',factory_id,'produced a', str(unitType)[9:], '!')
    else:
        return None
    return unitType

def try_harvest(unit):
    if not unit.unit_type == bc.UnitType.Worker:
        return False
    if random.randrange(10) < 8:
        return
    for direction in directions:
        if gc.can_harvest(unit.id, direction):
            gc.harvest(unit.id, direction)
            print('id:',unit.id,'Harvested!')
            return True
    return False

def try_rocket(unit):
    if gc.karbonite() > bc.UnitType.Rocket.blueprint_cost() and rocketCount() < 2:
        for dir in directions:
            if gc.can_blueprint(unit.id, bc.UnitType.Rocket, d):
                gc.blueprint(unit.id, bc.UnitType.Rocket, d)
                print('id:',unit.id,'started a ROCKET ROCKET!')
                return True
    return False

def try_replicate(unit):
    if not unit.unit_type == bc.UnitType.Worker:
        return False
    if random.randrange(100) < 80 or gc.karbonite() < 260:
        return
    for direction in directions:
        if gc.can_replicate(unit.id, direction):
            gc.replicate(unit.id, direction)
            print('id:',unit.id,'Replicated!')
            return True
    return False
    

def unitCount(unitType=None):
    count = 0
    for unit in gc.my_units():
        if unitType == None or unit.unit_type == unitType:
            count += 1
    return count

def factoryCount():
    return unitCount(unitType=bc.UnitType.Factory)

def rocketCount():
    return unitCount(unitType=bc.UnitType.Rocket)

# return a navigable location on mars
def get_launch_dest():
    while True:
        x = random.randrange(0,mars_map.width)
        y = random.randrange(0,mars_map.height)
        location = bc.MapLocation(bc.Planet.Mars, x, y)
        if mars_map.is_passable_terrain_at(location):
            print("Found a landing spot:",location)
            return location

while True:
    # We only support Python 3, which means brackets around print()
    print('pyround:', gc.round(), 'k:', gc.karbonite())

    # frequent try/catches are a good idea
    try:
        # walk through our units:
        for unit in gc.my_units():

            # first, factory logic
            if unit.unit_type == bc.UnitType.Factory:
                garrison = unit.structure_garrison()
                if len(garrison) > 0:
                    for d in directions:
                        if gc.can_unload(unit.id, d):
                            new_unit = gc.unload(unit.id, d)
                            print('id:',unit.id,'unloaded a unit!')
                            break
                else:
                    if unit.structure_is_built and unit.health == unit.max_health:
                        try_produce_robot(unit.id)
                continue
            # second, rocket logic
            if unit.unit_type == bc.UnitType.Rocket:
                if gc.planet == 'mars':
                    if len(unit.structure_garrison()) > 0:
                        for d in directions:
                            if gc.can_unload(unit.id, d):
                                new_unit = gc.unload(unit.id, d)
                                print('MARS id:',unit.id,'unloaded a unit!')
                                break
                elif unit.structure_is_built and unit.health == unit.max_health and len(unit.structure_garrison()) == 8:
                    dest = get_launch_dest()
                    if gc.can_launch_rocket(unit.id, dest):
                        gc.launch_rocket(unit.id, dest)
                        print("Launched ROCKET!!!!")
                continue

            # first, let's look for nearby blueprints to work on
            location = unit.location
            building = False
            if location.is_on_map():
                nearby = gc.sense_nearby_units(location.map_location(), 2)
                for other in nearby:
                    if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
                        print('id:',unit.id,'attacked a thing!')
                        gc.attack(unit.id, other.id)
                        continue
                    if other.unit_type == bc.UnitType.Rocket and gc.can_load(other.id, unit.id):
                        gc.load(other.id, unit.id)
                        print("id:",unit.id,"loaded into rocket",other.id,"total",len(other.structure_garrison()))
                        continue
                    if gc.can_build(unit.id, other.id):
                        gc.build(unit.id, other.id)
                        print('id:',unit.id,'built',other.id,'health',other.health)
                        building = True
                        # move onto the next neighboring unit
                        continue

            # okay, there weren't any dudes around
            # pick a random direction:
            d = random.choice(directions)

            # or try to harvest
            if try_harvest(unit):
                continue
            # try to build a rocket:
            elif try_rocket(unit):
                continue
            # try to build a factory:
            elif gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d) and not building:
                gc.blueprint(unit.id, bc.UnitType.Factory, d)
                print('id:',unit.id,'blueprinted a new factory! next research:',gc.research_info().next_in_queue(),'left:',gc.research_info().rounds_left())
            elif try_replicate(unit):
                continue
            # and if that fails, try to move
            elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, d) and not building:
                gc.move_robot(unit.id, d)

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()
