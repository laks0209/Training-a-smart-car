import random
from LearningEnvironment import car, learn_environ
from NextDirToDest import HeadDestination
from game import Simulator
from matplotlib import pyplot as plt

class Smartcar(car):

    def __init__(self, environ):
        super(Smartcar, self).__init__(environ)  # sets self.environ = environ, state = None, next_direction = None, and a default color
        self.color = 'red'  # override color
        self.NextDirToDest = HeadDestination(self.environ, self)  # simple route NextDirToDest to get next_direction
        # TODO: Initialize any additional variables here
        self.Q_initialial_value = 15
        self.Q_initial = {None : self.Q_initialial_value, 'forward' : self.Q_initialial_value, 'left' : self.Q_initialial_value, 'right' : self.Q_initialial_value}
        self.epsilon = 0.95
        self.gamma = 0.2
        self.alpha = 0.2
        self.state = None
        self.prev_state  = None
        self.prev_reward = None
        self.prev_action = None
        self.table1= []
        self.table2= []
        self.table3= []
        self.table4= []		
        self.Q_table = {}

    def reset(self, destination=None):
        self.NextDirToDest.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required

    def update(self, t):
        inputs = self.environ.sense(self)
        deadline = self.environ.get_deadline(self)
        self.next_direction = self.NextDirToDest.next_direction()  

        self.state = []
        self.state.append(self.next_direction)
        self.state.append(inputs['signal_color'])
        self.state.append(inputs['oncoming'])
        self.state.append(inputs['left'])
        state = tuple(self.state)
		
        if self.Q_table.has_key(state) : 
# if the state was previously encountered update the Q values and choose action with maximum Q value		
            if random.random() >= self.epsilon : 
                action = random.choice([None, 'forward', 'left', 'right'])
            else : 
                Q_max = max(self.Q_table[state].values())
                actions = {action:Q for action, Q in self.Q_table[state].items() if Q == Q_max}
				# action with maximum Q value
                action = random.choice(actions.keys())
        else :  
# if the state was not previously encountered add the state to the Q table and choose a random action
            self.Q_table[state] = self.Q_initial.copy() 
            action = random.choice([None, 'forward', 'left', 'right'])  

        # Execute action and get reward
        reward = self.environ.take_action(self, action)

        if self.prev_state is not None : 
# to ensure that in the trial, this one is not the initial one
			prev_state = tuple(self.prev_state)
			Qp = self.Q_table[prev_state][self.prev_action]
			Q_max = max(self.Q_table[state].values())
			Qp += self.alpha * (self.prev_reward + self.gamma * Q_max - Qp)
			self.Q_table[prev_state][self.prev_action] = Qp
        #Store actions, state and reward as _prev for use in the next cycle
        self.prev_state  = self.state
        self.prev_reward = reward
        self.prev_action = action			

        global G
        self.t=self.environ.t
        if self.t!=0:
		    
            G={}
            G=self.Q_table

        else:
            try:G
            except NameError:
                print "G was not defined"
            else:
			
                if G.has_key(('right','red','forward',None)):
                    J = G[('right','red','forward',None)]
                    J1=J[None]
                    J2=J['forward']
                    J3=J['right']
                    J4=J['left']
                    self.table1.append(J1)
                    self.table2.append(J2)
                    self.table3.append(J3)
                    self.table4.append(J4)
                else:
                    self.table1.append(0)
                    self.table2.append(0)
                    self.table3.append(0)
                    self.table4.append(0)


		
'''
        if len(self.table1)==100:
            f = open('Action1_state1_4','w')
            f.write('%s'%self.table1)
            f.close()
            f = open('Action2_state1_4','w')
            f.write('%s'%self.table2)
            f.close()
            f = open('Action3_state1_4','w')
            f.write('%s'%self.table3)
            f.close()
            f = open('Action4_state1_4','w')
            f.write('%s'%self.table4)
            f.close()
		
            plt.plot(self.table1,'r',label='None')
            plt.plot(self.table2,'g',label='Forward')
            plt.plot(self.table3,'b',label='Right')
            plt.plot(self.table4,'y',label='Left')
            plt.legend(loc='upper right')
            plt.xlabel('Trials')
            plt.ylabel('Q value')
            plt.title('Signal: Green, Next direction: Left, Oncoming: Forward, Left: None\n 5000 iterations, 4 client cars')
            plt.show()


'''
        

def run():


    # Create environment and car
    e = learn_environ()  
    a = e.create_car(Smartcar) 
    e.set_primary_car(a, enforce_deadline=True)  


    # Run it for n_trials number of times
    sim = Simulator(e, update_delay=0.0005, display=True, live_plot = True)  
    sim.run(n_trials=101)  # run for a specified number of trials
	
	#for validating Q table the Q_table is saved to a file
    f = open('Q_table_5000iter_24client','w')
    f.write('%s'%G)
    f.close()


if __name__ == '__main__':
    run()
