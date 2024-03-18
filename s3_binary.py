import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
import cv2
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button
from numba import jit

max_iter = 16  # Number of iterations to perform for both MS and JS

# Image size and extent for MS and JS
mandelbrot_width, mandelbrot_height = 601, 601
mandelbrot_extent = (-2.0, 1.0, -1.5, 1.5)

julia_width, julia_height = 601, 601
julia_extent = (-2, 2, -2, 2)

# Black reprents the set, white represents the non-set
colors = [(1, 1, 1, 0), (0, 0, 0)]
bin_cmap = LinearSegmentedColormap.from_list("bin_cmap", colors, N=2)

last_circle = None
mouse_pressed = False
mpl.rcParams['font.family'] = 'Cambria'


@jit(nopython=True)
def generate_mandelbrot(mandelbrot_extent, width, height, max_iter=256):

    # Define the complex plane
    x = np.linspace(mandelbrot_extent[0], mandelbrot_extent[1], width)
    y = np.linspace(mandelbrot_extent[2], mandelbrot_extent[3], height)

    # Initial values for z0=0 and constant c
    c = x + 1j * y[:, None]
    z = np.zeros_like(c, dtype=np.complex64)

    img = np.full(c.shape, max_iter, dtype=np.int32)
    for i in range(width):
        for j in range(height):
            n = 0
            # Iterate until the sequence diverges or max_iter is reached
            while n <= max_iter and np.abs(z[j, i]) < 2:
                z[j, i] = z[j, i] ** 2 + c[j, i]    # z(n+1) = z(n)^2 + c
                n += 1
            img[j, i] = n

    # If still not diverged, set to 1
    img = np.where(img == max_iter+1, 1, 0)  # Convert to binary image
    return img


@jit(nopython=True)
def generate_julia(c, julia_extent, width, height, max_iter=256):

    # Same logic as the Mandelbrot set, but with a constant c
    x = np.linspace(julia_extent[0], julia_extent[1], width)
    y = np.linspace(julia_extent[2], julia_extent[3], height)

    # Initial values for different z0 and constant c
    z = x + 1j * y[:, None]
    img = np.full(z.shape, max_iter, dtype=np.int32)

    for i in range(width):
        for j in range(height):
            n = 0
            while n <= max_iter and np.abs(z[j, i]) < 2:
                z[j, i] = z[j, i] ** 2 + c
                n += 1
            img[j, i] = n

    img = np.where(img == max_iter+1, 1, 0)  # Convert to binary image
    return img


def onclick(event):
    global last_circle, mouse_pressed
    if event.inaxes == ax1:
        mouse_pressed = True
        update_circle_and_julia(event)


def onrelease(event):
    global mouse_pressed
    mouse_pressed = False


def onmotion(event):
    global last_circle, mouse_pressed
    if event.inaxes == ax1 and mouse_pressed:
        update_circle_and_julia(event)


def update_circle_and_julia(event):
    global last_circle, julia_img_binary, c_js
    if last_circle:
        last_circle.remove()
    last_circle, = ax1.plot(event.xdata, event.ydata,
                            'o', mfc='none', mec='red', mew=2, markersize=10)
    c_js = complex(event.xdata, event.ydata)
    julia_img_binary = generate_julia(
        c_js, julia_extent, julia_width, julia_height, max_iter)
    ax2.clear()
    ax2.imshow(julia_img_binary, extent=(-2, 2, -2, 2),
               cmap=bin_cmap, zorder=2)
    ax2.set_title(f"Julia Set for c = {c_js:.2f}")
    ax2.set_xticks(np.arange(-2, 2.1, 1))
    ax2.set_yticks(np.arange(-2, 2.1, 1))
    ax2.grid(True, color='white', linewidth=0.5, zorder=1)

    fig.canvas.draw_idle()


def save_image(event):
    filename = f"{c_js.real:.2f}_{c_js.imag:.2f}.png"
    cv2.imwrite(filename, np.where(julia_img_binary == 1, 0, 1)*255)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))

# Plot the Mandelbrot set
mandelbrot_img_binary = np.flipud(generate_mandelbrot(mandelbrot_extent,
                                                      mandelbrot_width, mandelbrot_height, max_iter))
cv2.imwrite('ms_%d.png' % max_iter, np.where(
    mandelbrot_img_binary == 1, 0, 1) * 255)

ax1.imshow(mandelbrot_img_binary, extent=(-2.0, 1.0, -1.5, 1.5),
           cmap=bin_cmap, vmin=0, vmax=1, zorder=2)
ax1.set_title("Mandelbrot Set")
ax1.set_xticks(np.arange(-2, 1.1, 1))
ax1.set_yticks(np.arange(-1.5, 1.6, 1))


# Plot the Julia set
c_js = complex(-0.8, 0.156)  # Initial value for c
julia_img_binary = np.flipud(generate_julia(c_js, julia_extent,
                                            julia_width, julia_height, max_iter))
ax2.imshow(julia_img_binary, extent=(-2, 2, -2, 2),
           cmap=bin_cmap, vmin=0, vmax=1, zorder=2)

ax2.set_title(f"Julia Set for {c_js:.2f}")
ax2.set_xticks(np.arange(-2, 2.1, 1))
ax2.set_yticks(np.arange(-2, 2.1, 1))


for ax in [ax1, ax2]:
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_facecolor((233/255, 233/255, 241/255))
    ax.grid(True, color='white', linewidth=0.5, zorder=1)
    ax.tick_params(axis='both', which='both', bottom=False, top=False,
                   left=False, right=False, labelbottom=False, labelleft=False)

ax_button = plt.axes([0.8, 0.05, 0.1, 0.075])
btn = Button(ax_button, 'Save JS')

fig.canvas.mpl_connect('button_press_event', onclick)
fig.canvas.mpl_connect('button_release_event', onrelease)
fig.canvas.mpl_connect('motion_notify_event', onmotion)
btn.on_clicked(save_image)

plt.show()
