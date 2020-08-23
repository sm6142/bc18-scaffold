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
directions = [bc.Direction.North, bc.Direction.Northeast, bc.Direction.East, bc.Direction.Southeast, bc.Direction.South, bc.Direction.Southwest, bc.Direction.West, bc.Direction.Northwest]
tryRotate = [0,-1,1,-2,2]
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

def invert(loc): # find where enemy likely to be, assumes Earth
    newx = earth_map.width-loc.x
    newy = earth_map.height-loc.y
    return bc.MapLocation(bc.Planet.Earth,newx,newy)

def locToStr(loc):
    return '('+str(loc.x)+','+str(loc.y)+')'

if gc.planet() == bc.Planet.Earth:
    oneLoc = gc.my_units()[0].location.map_location()
    earth_map = gc.starting_map(bc.Planet.Earth)
    enemyStart = invert(oneLoc)
    print('worker starts at '+locToStr(oneLoc))
    print('enemy worker presumably at '+locToStr(enemyStart))

def rotate(dir,amount):
    ind = directions.index(dir)
    return directions[(ind+amount)%8]

def goto(unit,dest):
    d = unit.location.map_location().direction_to(dest)
    if gc.can_move(unit.id, d):
        gc.move_robot(unit.id, d)

def fuzzygoto(unit,dest):
    toward = unit.location.map_location().direction_to(dest)
    for tilt in tryRotate:
        d = rotate(toward,tilt)
        if gc.can_move(unit.id,d):
            gc.move_robot(unit.id,d)
            break

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

def try_build(d, unit, unitType, numUnits=0, maxCount=1000):
    if numUnits < maxCount and gc.karbonite() > unitType.blueprint_cost():
        if gc.can_blueprint(unit.id, unitType, d):
            gc.blueprint(unit.id, unitType, d)
            print('id:',unit.id,'started a ',unitType)
            return True
    return False

def try_factory(d, unit):
    return try_build(d, unit, bc.UnitType.Factory, numUnits=numFactories)

def try_rocket(unit):
    for dir in directions:
        if try_build(d, unit, bc.UnitType.Rocket, numUnits=numRockets, maxCount=2):
            return True
    return False

def try_replicate(unit, direction):
    if numWorkers > 5:
        return false
    if not unit.unit_type == bc.UnitType.Worker:
        return False
    if gc.can_replicate(unit.id, direction):
        gc.replicate(unit.id, direction)
        print('id:',unit.id,'Replicated!')
        return True
    return False
    


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
        # count stuff
        numWorkers = 0
        blueprintLocation = None
        bluprintWaiting = False
        for unit in gc.my_units():
            if unit.unit_type == bc.UnitType.Factory or unit.unit_type == bc.UnitType.Rocket:
                if not unit.structure_is_built():
                    ml = unit.location.map_location()
                    blueprintLocation = ml
                    blueprintWaiting = True
            if unit.unit_type == bc.UnitType.Worker:
                numWorkers += 1
            if unit.unit_type == bc.UnitType.Rocket:
                rocketCount += 1
            if unit.unit_type == bc.UnitType.Factory:
                factoryCount += 1

        # walk through our units:
        for unit in gc.my_units():
            location = unit.location
                if !location.is_on_map(): # don't do anything while flying or in a factory, should handle factories first
                    continue
            # first, factory logic
            if unit.unit_type == bc.UnitType.Factory:
                garrison = unit.structure_garrison()
                if len(garrison) > 0:
                    for d in directions:
                        if gc.can_unload(unit.id, d):
                            new_unit = gc.unload(unit.id, d)
                            print('id:',unit.id,'unloaded a ',new_unit.unit_type)
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
            # third, everybody else
            d = random.choice(directions)
            if try_replicate(unit, d):
                continue
            
            adjacentUnits = gc.sense_nearby_units(location.map_location(), 2)
            for adjacent in adjacentUnits:
                if gc.can_build(unit.id, adjacent.id):
                    gc.build(unit.id, adjacent.id)
                    continue
                if adjacent.unit_type == bc.UnitType.Rocket and gc.can_load(adjacent.id, unit.id):
                    gc.load(other.id, unit.id)
                    print("id:",unit.id,"loaded into rocket",other.id,"total",len(other.structure_garrison()))
                    continue
                if adjacent.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, adjacent.id):
                    print('id:',unit.id,'attacked a thing!')
                    gc.attack(unit.id, adjacent.id)
                    continue
            if unit.unit_type == bc.UnitType.Worker:
                if blueprintWaiting:
                    if gc.is_move_ready(unit.id):
                        ml = unit.location.map_location()
                        bdist = ml.distance_squared_to(blueprintLocation)
                        if bdist <= 5:
                            fuzzygoto(unit,blueprintLocation)
                            continue
                if try_factory(unit, d):
                    continue
                if try_harvest(unit):
                    continue
            # and if that fails, try to move
            # pick a random direction:
            d = random.choice(directions)
            elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
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
