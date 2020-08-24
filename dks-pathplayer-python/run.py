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

enemyStart = None
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

def try_goto_blueprint(unit):
    if unit.unit_type != bc.UnitType.Worker:
        return False
    if len(blueprintLocations) == 0:
        return False
    if not gc.is_move_ready(unit.id):
        return False
    bestLocation = None
    bestDistance = 1000
    ml = unit.location.map_location()
    for blueprintLocation in blueprintLocations:
        bdist = ml.distance_squared_to(blueprintLocation)
        if bdist < bestDistance:
            bestDistance = bdist
            bestLocation = blueprintLocation
    if bestDistance <= 3:
        print('id:',unit.id,' will move to blueprint')
        fuzzygoto(unit,blueprintLocation)
        return True
    return False


def try_harvest(unit):
    if not unit.unit_type == bc.UnitType.Worker:
        return False
    currLocation = unit.location.map_location()
    bestDirection = None
    bestKarbonite = 0
    for direction in directions:
        if gc.can_harvest(unit.id, direction):
            k = gc.karbonite_at(currLocation.add(direction))
            if k > bestKarbonite:
                bestKarbonite = k
                bestDirection = direction
    if bestDirection:       
        gc.harvest(unit.id, bestDirection)
        print('id:',unit.id,'Harvested!')
        return True
    return False

def try_build(unit, unitType):
    if gc.karbonite() > unitType.blueprint_cost():
        for direction in directions:
            if gc.can_blueprint(unit.id, unitType, direction):
                gc.blueprint(unit.id, unitType, direction)
                print('BLUEPRINTED: id:',unit.id,'started a ',unitType)
                return True
    return False

def needs_building(unit):
    return not (unit.structure_is_built and unit.health == unit.max_health)


def try_factory(unit):
    return try_build(unit, bc.UnitType.Factory)

def try_rocket(unit):
    if gc.planet() == bc.Planet.Mars:
        return false
    return try_build(unit, bc.UnitType.Rocket)

def try_replicate(unit, direction):
    if numWorkers > 5:
        return False
    if not unit.unit_type == bc.UnitType.Worker:
        return False
    if gc.can_replicate(unit.id, direction):
        gc.replicate(unit.id, direction)
        print('id:',unit.id,'Replicated!')
        return True
    return False

def best_karbonite(unit):
    if not unit.unit_type == bc.UnitType.Worker:
        return False
    currLocation = unit.location.map_location()
    bestLocation = None
    bestKarbonite = 0
    for direction in directions:
        for i in range(1,5):
            loc = currLocation.add_multiple(direction, i)
            try:
                k = gc.karbonite_at(loc)
                if k > bestKarbonite:
                    bestKarbonite = k
                    bestLocation = loc
            except:
               continue
    if bestKarbonite == 0:
        print("No karbonite found, moving randomly")
        loc = currLocation.add(random.choice(directions))
    else:
        print("Moving towards square with ",bestKarbonite," karbonite")
    return loc
    
def best_opponent(unit):
    return enemyStart

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
        numFactories = 0
        numRockets = 0
        blueprintLocations = []
        blueprintWaiting = False
        for unit in gc.my_units():
            if unit.unit_type == bc.UnitType.Factory or unit.unit_type == bc.UnitType.Rocket:
                if needs_building(unit):
                    print("Unit id:", unit.id, " Type ", unit.unit_type, " needs building")
                    ml = unit.location.map_location()
                    blueprintLocations.append(ml)
            if unit.unit_type == bc.UnitType.Worker:
                numWorkers += 1
            if unit.unit_type == bc.UnitType.Rocket:
                numRockets += 1
            if unit.unit_type == bc.UnitType.Factory:
                numFactories += 1

        # walk through our units:
        for unit in gc.my_units():
            location = unit.location
            if not location.is_on_map(): # don't do anything while flying or in a factory, should handle factories first
                continue
            # first, factory logic
            if unit.unit_type == bc.UnitType.Factory:
                print("FACTORY: id:",unit.id," health:",unit.health)
                garrison = unit.structure_garrison()
                if len(garrison) > 0:
                    for d in directions:
                        if gc.can_unload(unit.id, d):
                            try:
                                new_unit = gc.unload(unit.id, d)
                                print('id:',unit.id,'unloaded a ')
                                break
                            except:
                                print('Could not unload factory')
                else:
                    if unit.structure_is_built and unit.health == unit.max_health:
                        try_produce_robot(unit.id)
                continue
            # second, rocket logic
            if unit.unit_type == bc.UnitType.Rocket:
                if gc.planet() == bc.Planet.Mars:
                    print('MARS id:',unit.id,' rocket on mars with ',len(unit.structure_garrison()),' units inside')
                    if len(unit.structure_garrison()) > 0:
                        for d in directions:
                            if gc.can_unload(unit.id, d):
                                try:
                                    gc.unload(unit.id, d)
                                    print('MARS id:',unit.id,'unloaded a unit!')
                                    break
                                except:
                                    print('MARS Could not unload rocket')
                elif gc.planet() == bc.Planet.Earth and not needs_building(unit) and len(unit.structure_garrison()) == 8:
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
            performedAction = False
            for adjacent in adjacentUnits:
                if (adjacent.unit_type == bc.UnitType.Rocket or adjacent.unit_type == bc.UnitType.Factory):
                    print("Unit:",unit.id," type ",unit.unit_type," adjacent unit ", adjacent.id, " is built ", adjacent.structure_is_built(), " health ", adjacent.health, "needs building", needs_building(adjacent))
                if gc.can_build(unit.id, adjacent.id) and needs_building(adjacent):
                    print("Unit:",unit.id," built unit ",adjacent.id," new health ", adjacent.health)
                    gc.build(unit.id, adjacent.id)
                    performedAction = true
                    break
                if adjacent.unit_type == bc.UnitType.Rocket and gc.can_load(adjacent.id, unit.id):
                    gc.load(adjacent.id, unit.id)
                    print("id:",unit.id,"loaded into rocket",adjacent.id,"total",len(adjacent.structure_garrison()))
                    performedAction = true
                    break
                if adjacent.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, adjacent.id):
                    print('id:',unit.id,'attacked a thing!')
                    gc.attack(unit.id, adjacent.id)
                    performedAction = true
                    break
            if performedAction:
                continue
            if unit.unit_type == bc.UnitType.Worker:
                if try_goto_blueprint(unit):
                    continue
                if (numRockets < 2 or random.randrange(10) < 2) and try_rocket(unit):
                    continue
                if try_factory(unit):
                    continue
                if try_harvest(unit):
                    continue
                if gc.is_move_ready(unit.id):
                    fuzzygoto(unit,best_karbonite(unit))
            else:
                if gc.is_move_ready(unit.id):
                    fuzzygoto(unit,best_opponent(unit))
 
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
