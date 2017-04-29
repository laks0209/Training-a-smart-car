from plotting import Recorder
import random
import os
import importlib
import time
import numpy as np

#environment is simulated using pygame
class Simulator(object):

    colors = {
        'white'   : (255, 255, 255),
        'black'   : (  0,   0,   0),
        'red'     : (255,   0,   0),
        'orange'  : (255, 128,   0),
        'mcara' : (200,   0, 200),
        'blue'    : (  0,   0, 255),
        'cyan'    : (  0, 200, 200),
        'yellow'  : (255, 255,   0),
        'green'   : (  0, 255,   0)
    }

    def __init__(self, environ,size=None, update_delay=1.0, display=True, live_plot=False):
        self.environ = environ
        if size is not None:
	        self.size = size
        else:
		    self.size=((self.environ.bounds[2] + 1) * self.environ.block_size, (self.environ.bounds[3] + 1) * self.environ.block_size)
        self.width, self.height = self.size

        self.road_width = 5 # width of road is 5 units
        self.road_color = self.colors['black']  # color of road is black
        self.bg_color = self.colors['white'] # background color is white

        self.initial_time = None
        self.current_time = 0.0
        self.last_updated = 0.0
        self.quit = False
        self.update_delay = update_delay  # time gap between consecutive steps in seconds

        self.display = display
        if self.display: # if the simualator is selected to display in the program(car.py)
            try:
                self.pygame = importlib.import_module('pygame') # importing pygame module
                self.pygame.init() # initializing 
                self.screen = self.pygame.display.set_mode(self.size)  #size of the display screen

                self.frame_delay = max(1, int(self.update_delay * 1000))  # time gap between frames
                self.car_sprite_size = (32, 32) # size of the car
                self.car_circle_radius = 10  # Traffic junctions are represented as circles of radius 10
                for car in self.environ.car_states:
                    car._sprite = self.pygame.transform.smoothscale(self.pygame.image.load(os.path.join("images", "car-{}.png".format(car.color))), self.car_sprite_size)
                    # resize to an arbitrary new resolution smoothly
                    car._sprite_size = (car._sprite.get_width(), car._sprite.get_height())
					# length and breadth of the car
                self.font = self.pygame.font.Font(None, 25)
				# the font size of the actions of the moving cars
                self.paused = False
			# throwing exceptions
            except ImportError as e:
                self.display = False
                print "Simulator.__init__(): Unable to import pygame; display disabled.\n{}: {}".format(e.__class__.__name__, e)
            except Exception as e:
                self.display = False
                print "Simulator.__init__(): Error initializing GUI objects; display disabled.\n{}: {}".format(e.__class__.__name__, e)

        # Setup values to report
        self.live_plot = live_plot
		# the plots in the graph
        self.rep = Recorder(values=['net_reward', 'avg_net_reward', 'final_deadline', 'success'], live_plot=self.live_plot)
        self.avg_net_reward_window = 10
		
    def run(self, n_trials=1):
        self.rep.reset()
        self.quit = False

        for trial in xrange(n_trials):
            print "Simulator.run(): Trial {}".format(trial)  # prints the trial number -> used for debugging the code
            self.initial_time = time.time()
            self.current_time = 0.0
            self.last_updated = 0.0
            self.environ.reset()
            while True:
                try:
                    # Updating environment step
                    self.current_time = time.time() - self.initial_time
                    if self.current_time - self.last_updated >= self.update_delay:
                        self.environ.step()
                        self.last_updated = self.current_time

                    # Events
                    if self.display:
                        if self.paused:
                            self.pause()
                        for event in self.pygame.event.get():      
						# for all the events that happens
						# eg. pressing a key in keyboard or actions of mouse
                            if event.type == self.pygame.QUIT:		
							# the program quits if the user closes the window
                                self.quit = True
                            elif event.type == self.pygame.KEYDOWN:
                                if event.unicode == u' ':
                                    self.paused = True
                                elif event.key == 27:  
                                    self.quit = True

                    # Render GUI and sleep
                    if self.display:
                        self.render()
                        self.pygame.time.wait(self.frame_delay)
                except KeyboardInterrupt:
                    self.quit = True
                finally:
                    if self.quit or self.environ.done:
                        break

            if self.quit:
                break
            
            # Updating the values
            self.rep.collect('success', trial, self.environ.trial_data['success'])	# if the car has reached destination within the deadline
            self.rep.collect('final_deadline', trial, self.environ.trial_data['final_deadline'])  # time left for the car to reach the destination
            self.rep.collect('net_reward', trial, self.environ.trial_data['net_reward'])  # Reward for the current trial
            self.rep.collect('avg_net_reward', trial, np.mean(self.rep.values['net_reward'].ydata[-self.avg_net_reward_window:]))  # average rewards
            if self.live_plot:
                self.rep.refresh_plot()  

        if self.display:
            self.pygame.display.quit()  # at the end of all trials pygame closes and only the graph plot remains

        if self.live_plot:
            self.rep.show_plot()  

    def render(self):
		# screen becones white in color(background)	
        self.screen.fill(self.bg_color)


		#Roads are drawn with lines of thickness 5 units
        for road in self.environ.roads:
            self.pygame.draw.line(self.screen, self.road_color, (road[0][0] * self.environ.block_size, road[0][1] * self.environ.block_size), (road[1][0] * self.environ.block_size, road[1][1] * self.environ.block_size), self.road_width)

		# Traffic junctions are drawn using circles of radius 10 units
        for intersection, traffic_signal_color in self.environ.junctions.iteritems():
            self.pygame.draw.circle(self.screen, self.road_color, (intersection[0] * self.environ.block_size, intersection[1] * self.environ.block_size), 10)
			# Draw green signal_colors to represent the state of traffic signal_color
            if traffic_signal_color.state==False:  # East-West traffic is open
                self.pygame.draw.line(self.screen, self.colors['green'],
				# Draw horizontal line
                    (intersection[0] * self.environ.block_size - 15, intersection[1] * self.environ.block_size),
                    (intersection[0] * self.environ.block_size + 15, intersection[1] * self.environ.block_size), self.road_width)
            else:  # North-South traffic is open
                self.pygame.draw.line(self.screen, self.colors['green'],
				# Draw vertical line
                    (intersection[0] * self.environ.block_size, intersection[1] * self.environ.block_size - 15),
                    (intersection[0] * self.environ.block_size, intersection[1] * self.environ.block_size + 15), self.road_width)


        # * Dynamic elements
        for car, state in self.environ.car_states.iteritems():
            # Compute precise car position here (back from the intersection some)
            car_offset = (2 * state['direction'][0] * self.car_circle_radius, 2 * state['direction'][1] * self.car_circle_radius)
            car_pos = (state['position'][0] * self.environ.block_size - car_offset[0], state['position'][1] * self.environ.block_size - car_offset[1])
            car_color = self.colors[car.color]
            if hasattr(car, '_sprite') and car._sprite is not None:
                # Draw car sprite (image), properly rotated
                rotated_sprite = car._sprite if state['direction'] == (1, 0) else self.pygame.transform.rotate(car._sprite, 180 if state['direction'][0] == -1 else state['direction'][1] * -90)
                self.screen.blit(rotated_sprite,
                    self.pygame.rect.Rect(car_pos[0] - car._sprite_size[0] / 2, car_pos[1] - car._sprite_size[1] / 2,
                        car._sprite_size[0], car._sprite_size[1]))
            else:
                # Draw simple car (circle with a short line segment poking out to indicate direction)
                self.pygame.draw.circle(self.screen, car_color, car_pos, self.car_circle_radius)
                self.pygame.draw.line(self.screen, car_color, car_pos, state['position'], self.road_width)
            if car.get_next_direction() is not None:
                self.screen.blit(self.font.render(car.get_next_direction(), True, car_color, self.bg_color), (car_pos[0] + 10, car_pos[1] + 10))
            if state['destination'] is not None:
                self.pygame.draw.circle(self.screen, car_color, (state['destination'][0] * self.environ.block_size, state['destination'][1] * self.environ.block_size), 6)
                self.pygame.draw.circle(self.screen, car_color, (state['destination'][0] * self.environ.block_size, state['destination'][1] * self.environ.block_size), 15, 2)

        # Legend in pygame simulator
        text_y = 10
        for text in self.environ.status_text.split('\n'):
            self.screen.blit(self.font.render(text, True, self.colors['red'], self.bg_color), (100, text_y))
            text_y += 20


        self.pygame.display.flip()

    def pause(self):
	# if the simulator is paused
        abs_pause_time = time.time()
        pause_text = "Press any key to continue.... The simulator is paused"
        self.screen.blit(self.font.render(pause_text, True, self.colors['cyan'], self.bg_color), (100, self.height - 40))
        self.pygame.display.flip()
        print pause_text  
        while self.paused:
            for event in self.pygame.event.get():
                if event.type == self.pygame.KEYDOWN:
                    self.paused = False
            self.pygame.time.wait(self.frame_delay)
        self.screen.blit(self.font.render(pause_text, True, self.bg_color, self.bg_color), (100, self.height - 40))
        self.initial_time += (time.time() - abs_pause_time)
