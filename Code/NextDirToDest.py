import random

class HeadDestination(object):
# Decides the next direction that the car needs to move towards the destination

    def __init__(self, environ, car):
        self.destination = None
        self.environ = environ
        self.car = car

    def route_to(self, destination=None):
		if destination is None:
			self.destination = random.choice(self.environ.junctions.keys())
		else:
			self.destination = destination

    def next_direction(self):
        direction = self.environ.car_states[self.car]['direction']
        position = self.environ.car_states[self.car]['position']
        difference = (self.destination[0] - position[0], self.destination[1] - position[1])
		
        if difference[0] == 0 and difference[1] == 0:
		# Car's position is same as destination (Car has reached the destination)
            return None
        elif difference[1] != 0:  
		# Difference in y axis
            if difference[1] * direction[1] > 0:  
			# Car is moving towards south and destination is also in south OR
			# Car is moving towards north and destination is also in north
			# then the car should take forward action
                return 'forward'
            elif difference[1] * direction[1] < 0:  
			# Car is moving towards south and destination is in north OR
			# Car is moving towards north and destination is in south
			# then the car should take a U turn
                return 'right'  
            elif difference[1] * direction[0] > 0:
			# Car is moving towards south and destination is in west OR
			# Car is moving towards north and destination is in east
			# then the car should take right action
                return 'right'
            else:
			# Car is moving towards south and destination is in east OR
			# Car is moving towards north and destination is in west
			# then the car should take left action
                return 'left'

        elif difference[0] != 0:  
		# Difference in x axis
            if difference[0] * direction[0] > 0:  
			# Car is moving towards west and destination is also in west OR
			# Car is moving towards east and destination is also in east
			# then the car should take forward action
                return 'forward'
            elif difference[0] * direction[0] < 0:  
			# Car is moving towards west and destination is in east OR
			# Car is moving towards east and destination is in west
			# then the car should take U-turn
                return 'right'  
            elif difference[0] * direction[1] > 0:
			# Car is moving towards west and destination is in south OR
			# Car is moving towards east and destination is in north
			# then the car should take left action
                return 'left'
            else:
			# Car is moving towards west and destination is in north OR
			# Car is moving towards east and destination is in south
			# then the car should take right action
                return 'right'
