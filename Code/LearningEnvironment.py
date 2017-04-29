from game import Simulator
from collections import OrderedDict
import random
import time


class Signal(object):

    valid_states = [True, False]  # North-South traffic open, East-West traffic open

	
    def __init__(self, state=None, duration=None):
        if duration is None:
            self.duration = random.choice([3, 4, 5])
		# average time the signal remains in the same state (red/green)
        else:
            self.duration = duration
        self.last_updated = 0
        if state is None:
            self.state = random.choice(self.valid_states)
        else:
            self.state = state 

    def update(self, t):
        if t >= self.duration + self.last_updated:
			self.last_updated = t
			if self.state==0:
				self.state=1
			else:
				self.state=0
			# switiching traffic signal-from red to green or green to red
            
    def reset(self):
        self.last_updated = 0


class learn_environ(object):
    hard_time_limit = -100  
    valid_directions = [(0, -1),(1, 0),(0, 1),(-1, 0)]  
	# North, East, South, West
    valid_actions = [None,'forward','left','right'] # actions taken by the smart car at a given state
    valid_inputs = {'left': valid_actions,'right': valid_actions,'oncoming': valid_actions,'signal_color': Signal.valid_states}

    def __init__(self, num_clientcars=4):
        self.num_clientcars = num_clientcars  
        
        # Initialize simulation variables
        self.t = 0
        self.status_text = ""
        self.done = False
        self.car_states = OrderedDict()

        # Roads and traffic signal_colors at junctions
        self.roads = []
        self.junctions = OrderedDict()
        self.block_size = 100
        self.bounds = (1,1,8,6)
        
        for x in xrange(1,self.bounds[2] + 1):
            for y in xrange(1,self.bounds[3] + 1):
                self.junctions[(x, y)] = Signal()  

        for a in self.junctions:
            for b in self.junctions:
                if a != b and (abs(a[1] - b[1])+abs(a[0] - b[0])) == 1:  
                    self.roads.append((a, b))
                    
        # Trial data (updated at the end of each trial)
        self.trial_data = {
            'final_deadline': None,  # time left
            'net_reward': 0.0,  # rewards that are added up to the current trial
            'success': 0,  # success = 1, if the car has reached destination within the deadline
        }

        # Step data (updated after each environment step)
        self.step_data = {
            'reward': 0.0,
            'inputs': None,
            'action': None,
            'waypoint': None,
            'deadline': 0,
            't': 0
        }
		
        # Smart car
        self.primary_car = None  
        self.enforce_deadline = False        

        # Client cars
        for i in xrange(self.num_clientcars):
            self.create_car(Clientcar)

    def set_primary_car(self,car, enforce_deadline=False):
        self.enforce_deadline = enforce_deadline		
        self.primary_car = car
			
    def create_car(self, car_class, *args, **kwargs):
		car = car_class(self, *args, **kwargs)
		self.car_states[car]={'direction': (0, 1),'position': random.choice(self.junctions.keys())}
		return car


    def reset(self):
	# choose random source and destination such that the distance between them is at least 4 units
        source = random.choice(self.junctions.keys())
        destination = random.choice(self.junctions.keys())
        while (abs(destination[1] - source[1])+abs(destination[0] - source[0]))< 4:
            source = random.choice(self.junctions.keys())
            destination = random.choice(self.junctions.keys())
        deadline = (abs(destination[1] - source[1])+abs(destination[0] - source[0]))* 5
		
        source_direction = random.choice(self.valid_directions)
		
        for traffic_signal_color in self.junctions.itervalues():
            traffic_signal_color.reset()

        self.done = False
        self.t = 0

        # Initialize car(s)
        for car in self.car_states.iterkeys():
			if car is self.primary_car:
				self.car_states[car]['position']= source
				self.car_states[car]['direction']= source_direction
				self.car_states[car]['destination']= destination
				self.car_states[car]['deadline']= deadline
				car.reset(destination=destination)
                # Reset values for this trial (step data will be set during the step)
				self.trial_data['net_reward'] = 0.0
				self.trial_data['final_deadline'] = deadline
				self.trial_data['success'] = 0
				self.trial_data['negative_reward']=0.0
			else:
				self.car_states[car]['position']= random.choice(self.junctions.keys())
				self.car_states[car]['direction']=random.choice(self.valid_directions)
				self.car_states[car]['destination']=None
				self.car_states[car]['deadline']=None
				car.reset(destination=None)

    def step(self):
        for intersection, traffic_signal_color in self.junctions.iteritems():
            traffic_signal_color.update(self.t)

        # Update cars
        for car in self.car_states.iterkeys():
            car.update(self.t)

        if self.done:
            return  # primary car might have reached destination

        if self.primary_car is not None:
            car_deadline = self.car_states[self.primary_car]['deadline']
            if (car_deadline <= 0 and self.enforce_deadline) or self.hard_time_limit >= car_deadline :
                self.done = True
            self.car_states[self.primary_car]['deadline'] = car_deadline - 1
        self.t += 1

    def sense(self, car):
        assert car in self.car_states, "Unknown car!"
        right = None
        left = None
        oncoming = None

        direction = self.car_states[car]['direction']
        position = self.car_states[car]['position']

        # Detect the direction of other cars at each intersection
		
        for other_car,other_state in self.car_states.iteritems():
            if other_car==car or other_state['position'] !=position:
				continue
            elif other_state['direction'][0]==direction[0] and other_state['direction'][1]==direction[1]:
                continue
            other_direction = other_car.get_next_direction()
            if (other_state['direction'][0]*direction[0]  + other_state['direction'][1]*direction[1]) == -1:
                if oncoming != 'left':  # we don't want to override oncoming == 'left'
                    oncoming = other_direction
            elif (other_state['direction'][0]==direction[1] and other_state['direction'][1]==-direction[0]):
                if right != 'left' and right != 'forward':  # we don't want to override right == 'forward or 'left'
                    right = other_direction
            else:
                if left != 'forward':  # we don't want to override left == 'forward'
                    left = other_direction

        if (direction[0] != 0 and self.junctions[position].state==0):
		    signal_color = 'green'
        elif (direction[1] != 0 and self.junctions[position].state==1):
		    signal_color = 'green'
        else:
            signal_color = 'red'

        return { 'oncoming': oncoming, 'right': right,'left': left,'signal_color': signal_color}

    def get_deadline(self, car):
		if car is self.primary_car:
			return self.car_states[car]['deadline']
		else:
			return None

    def take_action(self, car, action):
        assert car in self.car_states, "Unknown car!"
        assert action in self.valid_actions, "Invalid action!"
        inputs = self.sense(car)
        state = self.car_states[car]
        position = state['position']
        direction = state['direction']
        if (direction[0] != 0 and self.junctions[position].state==0):
		    signal_color = 'green'
        elif (direction[1] != 0 and self.junctions[position].state==1):
		    signal_color = 'green'
        else:
            signal_color = 'red'


        # Deciding the next direction of the car by obeying the traffic rules
        obey_traffic_rule = True
        reward = 0  
        if action == 'forward':
            if signal_color == 'red':
                obey_traffic_rule = False
        elif action == 'left':
            if signal_color != 'red' and inputs['oncoming'] == None:
                direction = (direction[1], -direction[0])
            elif signal_color != 'red' and inputs['oncoming'] == 'left':
				direction = (direction[1], -direction[0])
            else:
                obey_traffic_rule = False
        elif action == 'right':
            if signal_color != 'red':
				direction = (-direction[1], direction[0])
            elif (inputs['oncoming'] != 'left' and inputs['left'] != 'forward'):
                direction = (-direction[1], direction[0])
            else:
                obey_traffic_rule = False

		#Assign rewards
        if obey_traffic_rule==0:		#traffic rule not obeyed
            reward = -1.0
        else:					#traffic rule obeyed
            if action is None:	#No movement of car
                reward = 0.0
            else:				#Car moves to next position
                position = ((position[0] + direction[0] - self.bounds[0]) % (self.bounds[2] - self.bounds[0] + 1) + self.bounds[0],
                            (position[1] + direction[1] - self.bounds[1]) % (self.bounds[3] - self.bounds[1] + 1) + self.bounds[1])  
				#circular movement -> if the car reaches boundary the next position of the car will be the opposite boundary
				#Meaning that if the car is in position (1,8) moving towards east the next position of the car will be (1,1) direction east
                #if self.bounds[0] <= position[0] <= self.bounds[2] and self.bounds[1] <= position[1] <= self.bounds[3]:  # bounded
                state['position'] = position
                state['direction'] = direction
                if action != car.get_next_direction():		#Car not direction towards destination
					reward = -0.5
                else:										#Car direction towards destination
					reward =2.0

        if car is self.primary_car:
            if state['destination'] == state['position']:
                self.done = True
                if state['deadline'] >= 0:
                    self.trial_data['success'] = 1
                    reward += 10  # Car has reached destination within the deadline
            self.status_text = "state: {}\naction: {}\nreward: {}".format(car.get_state(), action, reward)
            # Update values
            self.step_data['t'] = self.t
            self.trial_data['final_deadline'] = self.step_data['deadline'] = state['deadline']
            self.step_data['waypoint'] = car.get_next_direction()
            self.step_data['reward'] = reward
            self.trial_data['net_reward'] += reward
            self.step_data['inputs'] = inputs
            self.step_data['action'] = action

        return reward


class car(object):
    """Base class for all cars."""

    def __init__(self, environ):
        self.color = 'cyan'
        self.next_direction = None
        self.state = None
        self.environ = environ

    def get_state(self):
        return self.state

    def update(self, t):
        pass
	
    def reset(self, destination=None):
        pass

    def get_next_direction(self):
        return self.next_direction


class Clientcar(car):

    def __init__(self, environ):
        super(Clientcar, self).__init__(environ)  # sets self.environ = environ, state = None, next_direction = None, and a default color
        self.color = random.choice(['orange' , 'green', 'blue','cyan'])
        self.next_direction = random.choice(learn_environ.valid_actions[1:])

    def update(self, t):
        actioncorrect = True
        inputs = self.environ.sense(self)

        if self.next_direction == 'forward':
            if inputs['signal_color'] != 'green':
                actioncorrect = False
        elif self.next_direction == 'left':
            if inputs['signal_color'] != 'green':
                actioncorrect = False
            elif inputs['oncoming'] == 'forward':
                actioncorrect = False
            elif inputs['oncoming'] == 'right':
                actioncorrect = False
        elif self.next_direction == 'right':
            if inputs['signal_color'] != 'green' and inputs['left'] == 'forward':
                actioncorrect = False

        action = None
        if actioncorrect:
            action = self.next_direction
            self.next_direction = random.choice(learn_environ.valid_actions[1:])
        reward = self.environ.take_action(self, action)
