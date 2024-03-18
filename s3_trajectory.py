import numpy as np
import matplotlib.pyplot as plt
from numba import jit
from matplotlib.patches import Circle


@jit(nopython=True)
def compute_trajectory(c_or_z, max_iter, predefined_c, for_mandelbrot):

    # MS z0 as 0, JS as clicked point
    z = 0 if for_mandelbrot else c_or_z
    # MS c as clicked point, JS as predefined value
    c = c_or_z if for_mandelbrot else predefined_c

    trajectory = np.zeros((max_iter, 2))
    for n in range(max_iter):
        z = z**2 + c    # z_n+1 = z_n^2 + c
        trajectory[n] = [z.real, z.imag]

    return trajectory


class MandelbrotJuliaApp:
    def __init__(self):
        self.mouse_pressed = False
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(15, 6))
        self.predefined_c = 0
        self.black_points = {'Mandelbrot': [], 'Julia': []}
        self.current_mandelbrot_trajectory = None
        self.current_julia_trajectory = None
        self.setup_plots()
        self.connect_events()

    def setup_plots(self):

        self.ax1.set_xlim(-2.5, 2.5)
        self.ax1.set_ylim(-2.5, 2.5)
        self.ax1.set_title("Mandelbrot Set")
        self.ax1.set_aspect('equal')
        # Threshold circle for boundness
        self.ax1.add_patch(Circle((0, 0), 2, edgecolor='blue',
                                  facecolor='none', linestyle='--'))

        self.ax2.set_xlim(-2.5, 2.5)
        self.ax2.set_ylim(-2.5, 2.5)
        self.ax2.set_title(f"Julia Set for c = {self.predefined_c}")
        self.ax2.set_aspect('equal')
        # Threshold circle for boundness
        self.ax2.add_patch(Circle((0, 0), 2, edgecolor='blue',
                                  facecolor='none', linestyle='--'))

    def connect_events(self):
        self.fig.canvas.mpl_connect(
            'button_press_event', self.on_press_release)
        self.fig.canvas.mpl_connect(
            'button_release_event', self.on_press_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press_release(self, event):
        if event.name == 'button_press_event':
            self.mouse_pressed = True
        else:
            self.mouse_pressed = False

    def on_motion(self, event):
        if not self.mouse_pressed or event.inaxes not in [self.ax1, self.ax2]:
            return

        ax = event.inaxes
        c_or_z = event.xdata + 1j * event.ydata
        max_iter = 50  # displayed iterations
        for_mandelbrot = ax == self.ax1
        trajectory = compute_trajectory(
            c_or_z, max_iter, self.predefined_c, for_mandelbrot)

        # Condition for boundness
        zn = trajectory[-1]
        convergence = ((zn[0]*zn[0] + zn[1]*zn[1]) < 2)

        if convergence:
            self.add_point(ax, event.xdata, event.ydata, 'black')

        self.draw_trajectory_and_check_divergence(
            ax, trajectory, convergence, event)

    def add_point(self, ax, x, y, color):
        ax.plot(x, y, '.', color=color, markersize=10)
        self.fig.canvas.draw_idle()

    def draw_trajectory_and_check_divergence(self, ax, trajectory, convergence, event):
        if ax == self.ax1:
            if self.current_mandelbrot_trajectory is not None:
                try:
                    self.current_mandelbrot_trajectory.remove()
                except ValueError:
                    pass
                self.current_mandelbrot_trajectory = None
        elif ax == self.ax2:
            if self.current_julia_trajectory is not None:
                try:
                    self.current_julia_trajectory.remove()
                except ValueError:
                    pass
                self.current_julia_trajectory = None

        color = 'r' if ax == self.ax1 else 'g'

        if convergence == False:
            color = '#cccccc'  # gray

        trajectory_line, = ax.plot(
            trajectory[:, 0], trajectory[:, 1], color=color, lw=1)
        if ax == self.ax1:
            self.current_mandelbrot_trajectory = trajectory_line
        else:
            self.current_julia_trajectory = trajectory_line

        self.fig.canvas.draw_idle()


app = MandelbrotJuliaApp()
plt.show()
