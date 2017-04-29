import time
from collections import OrderedDict
import numpy as np
import matplotlib.pyplot as plt

class Parameter(object):

    def __init__(self, name):
        self.reset()
        self.name = name

    def reset(self):
        self.xdata = []
        self.ydata = []

    def collect(self, x, y):
        self.xdata.append(x)
        self.ydata.append(y)

    def plot(self, ax):
        self.plot_obj, = ax.plot(self.xdata, self.ydata, 'o-', label=self.name)

    def refresh(self):
        self.plot_obj.set_data(self.xdata, self.ydata)



class Recorder(object):

    def __init__(self, values=[], live_plot=False):
        self.values = OrderedDict()

        for name in values:

            self.values[name] = Parameter(name)
        self.live_plot = live_plot

        if self.live_plot==1:
            if not plt.isinteractive():
                plt.ion()
            self.plot()



    def collect(self, name, x, y):
        if not name in self.values:
            self.values[name] = Parameter(name)
            self.values[name].plot(self.ax)
            self.ax.legend()  
        self.values[name].collect(x, y)
        if self.live_plot:
            self.values[name].refresh()

    def plot(self):
        if not hasattr(self, 'fig') or not hasattr(self, 'ax'):
            self.fig, self.ax = plt.subplots()
            for name in self.values:
                self.values[name].plot(self.ax)
            self.ax.grid()
            self.ax.legend()
        else:
            for name in self.values:
                self.values[name].refresh()
        self.refresh_plot()

    def refresh_plot(self):
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.draw()

    def show_plot(self):
	# the plot window will remain until the user closes the window
        if plt.isinteractive():
            plt.ioff()
        self.plot()
        plt.show()

    def reset(self):
        for name in self.values:
            self.values[name].reset()
            if self.live_plot:
                self.values[name].refresh()


def test_record():
    plt.ion()
    rep = Recorder(values=['reward', 'flubber'], live_plot=True)
    for i in xrange(100):
        rep.collect('reward', i, np.random.random())
        if i % 10 == 1:
            rep.collect('flubber', i, np.random.random() * 2 + 1)
            rep.refresh_plot()
        time.sleep(0.01)
    rep.plot()
    plt.ioff()
    plt.show()


if __name__ == '__main__':
    test_record()
