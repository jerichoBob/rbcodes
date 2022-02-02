from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from astropy.convolution import convolve, Box1DKernel
from astropy.modeling import models, fitting
from scipy.interpolate import splrep, splev
import numpy as np


# not necessary if not displaying images
import matplotlib.image as mpimg

matplotlib.use('Qt5Agg')

class MplCanvas(FigureCanvasQTAgg):
	def __init__(self, parent=None, width=5, height=4, dpi=100):
		self.fig = Figure(figsize=(width, height), dpi=dpi)
		self.axes = self.fig.add_subplot(111)

		# initialize some plotting parameters
		self.wave, self.flux, self.error = [],[],[]
		self.init_xlims, self.init_ylims = [],[]
		self.fxval, self.fyval = [], []
		self.scale = 1.
		super().__init__(self.fig)

		# connect funcitons to events
		self.fig.canvas.setFocusPolicy(Qt.ClickFocus)
		self.fig.canvas.setFocus()
		self.cid = self.fig.canvas.mpl_connect('key_press_event', self.ontype)
		#self.fig.canvas.mpl_connect('button_press_event', self.onclick)
		#self.fig.canvas.mpl_connect('pick_event', self.onpick)


	def plot_spec(self, wave, flux, error):
		self.axes.cla()
		self.axes.plot(wave, flux, color='black')#, label='Flux')
		self.axes.plot(wave, error, color='red')# label='Error')
		#self.axes.legend(loc='upper right')
		self.axes.set_ylim([-1e-13, 0.01])
		self.axes.set_xlabel('Wavelength')
		self.axes.set_ylabel('Flux')
		self.draw()

		# update intiial plotting parameters
		self.wave, self.flux, self.error = wave, flux, error
		self.init_xlims = self.axes.get_xlim()
		self.init_ylims = self.axes.get_ylim()

	def ontype(self, event):
		'''Interactivae keyboard events
		Note:
			Always Update to help mannual for new keyboard events
		'''
		print(event.key)
		if event.key == 'r':
			# reset flux/err and clear all lines
			del self.axes.lines[2:]	# delete everything except flux/err
			self.line_xlim, self.line_ylim = [], []
			self.fxval, self.fyval = [], []
			
			#self.axes.texts = []
			self.axes.set_ylim(self.init_ylims)
			self.axes.set_xlim(self.init_xlims)
			self.draw()

		elif event.key == 't':
			# set y axis max value
			ylim = self.axes.get_ylim()
			self.axes.set_ylim([ylim[0], event.ydata])
			self.draw()

		elif event.key == 'b':
			# set y axis min value
			ylim = self.axes.get_ylim()
			self.axes.set_ylim([event.ydata, ylim[-1]])
			self.draw()

		elif event.key == 'X':
			# set x axis max value
			xlim = self.axes.get_xlim()
			self.axes.set_xlim([xlim[0], event.xdata])
			self.draw()

		elif event.key == 'x':
			# set x axis min value
			xlim = self.axes.get_xlim()
			self.axes.set_xlim([event.xdata, xlim[-1]])
			self.draw()

		elif event.key == '[':
			# pan window to the left
			xlim = self.axes.get_xlim()
			delx = (xlim[-1] - xlim[0])
			self.axes.set_xlim([xlim[0] - delx, xlim[0]])
			self.draw()

		elif event.key == ']':
			# pan window to the right
			xlim = self.axes.get_xlim()
			delx = (xlim[-1] - xlim[0])
			self.axes.set_xlim([xlim[1], xlim[1] + delx])
			self.draw()

		elif event.key == 'S':
			# smooth ydata
			self.scale += 2
			self.new_spec = convolve(self.flux, Box1DKernel(self.scale))
			self.new_err = convolve(self.error, Box1DKernel(self.scale))
			self.replot(self.new_spec, self.new_err)
			self.draw()

		elif event.key == 'U':
			# unsmooth ydata
			self.scale -= 2
			if self.scale < 0:
				self.scale = 1
			self.new_spec = convolve(self.flux, Box1DKernel(self.scale))
			self.new_err = convolve(self.error, Box1DKernel(self.scale))
			self.replot(self.new_spec, self.new_err)
			self.draw()

		elif event.key == 'Y':
			# set y-axis limits with precise values
			ylimdialog = CustomLimDialog(axis='y')
			if ylimdialog.exec_():
				ylim = ylimdialog._getlim()
				self.axes.set_ylim(ylim)
				self.draw()

		elif event.key == 'W':
			# set y-axis limits with precise values
			xlimdialog = CustomLimDialog(axis='x')
			if xlimdialog.exec_():
				xlim = xlimdialog._getlim()
				self.axes.set_xlim(xlim)
				self.draw()


		elif event.key == 'G':
			# fit a Gaussian profile
			self.fxval.append(event.xdata)
			self.fyval.append(event.ydata)

			fclick = len(self.fxval)
			self.axes.plot(event.xdata, event.ydata, 'rs', ms=5)
			self.draw()

			if fclick == 1:
				message = 'You need 3 points to model a Gaussian. Please click 2 more points.'
			elif fclick == 2:
				message = 'Please click 1 more point to model a Gaussian.'
			elif fclick == 3:
				# fit a Gaussian with 3 data points
				g_init = models.Gaussian1D(amplitude=self.fyval[1],
										   mean=self.fxval[2],
										   stddev=0.5*(self.fxval[2]-self.fxval[0]))
				g_fit = fitting.LevMarLSQFitter()

				# 1. fit a local continuum
				c_range = np.where((self.wave>=self.fxval[0]) & (self.wave <= self.fxval[2]))
				g_wave = self.wave[c_range]
				g_flux = self.flux[c_range]
				spline = splrep([self.fxval[0], self.fxval[2]],
								[self.fyval[0], self.fyval[2]],
								k=1)
				cont = splev(g_wave, spline)
				# 2. check if it is an absorption or emission line
				if ((self.fyval[1] < self.fyval[0]) & (self.fyval[1] < self.fyval[2])):
					ydata = 1. - (g_flux / cont)
					g = g_fit(g_init, g_wave, ydata)
					g_final = (1. - g(g_wave)) * cont
				else:
					ydata = g_flux / cont
					g = g_fit(g_init, g_wave, ydata)
					g_final = g(g_wave) * cont

				model_fit = self.axes.plot(g_wave, g_final, 'r-')
				self.draw()
				message = (f'Amplitude: {g.parameters[0]:.3f}\n'
						   f'Mean: {g.parameters[1]:.3f}\n'
						   f'Sigma: {g.parameters[2]:.3f}')

				self.fxval, self.fyval = [], []
				print(message)


	def replot(self, new_spec, new_err):
		'''Re-plot smoothed/unsmoothed spectrum
		'''
		axes = self.figure.gca()
		xlim = axes.get_xlim()
		ylim = axes.get_ylim()
		self.axes.lines[0] = axes.plot(self.wave, self.new_spec, color='black')#, label='Flux')
		self.axes.lines[1] = axes.plot(self.wave, self.new_err, color='red')# label='Error')
		#self.axes.legend(loc='upper right')
		del self.axes.lines[-2:]


class CustomLimDialog(QtWidgets.QDialog):
	def __init__(self, axis='y'):
		super().__init__()

		self.setWindowTitle('Set precise limits on flux range')
		QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
		self.buttonbox = QtWidgets.QDialogButtonBox(QBtn)

		self.layout = QtWidgets.QGridLayout()
		if axis == 'x':
			lb_min = QtWidgets.QLabel('X-Axis Min')
			lb_max = QtWidgets.QLabel('X-Axis Max')
		if axis == 'y':
			lb_min = QtWidgets.QLabel('Y-Axis Min')
			lb_max = QtWidgets.QLabel('Y-Axis Max')
		else:
			pass

		self.le_min = QtWidgets.QLineEdit()
		self.le_min.setPlaceholderText('Desired minimum value')
		self.le_max = QtWidgets.QLineEdit()
		self.le_max.setPlaceholderText('Desired maximum value')

		self.layout.addWidget(lb_min, 0, 0)
		self.layout.addWidget(lb_max, 1, 0)
		self.layout.addWidget(self.le_min, 0, 1)
		self.layout.addWidget(self.le_max, 1, 1)
		self.layout.addWidget(self.buttonbox, 2, 1)

		self.setLayout(self.layout)

		self.buttonbox.accepted.connect(self.accept)
		self.buttonbox.rejected.connect(self.reject)
		
		
	def _getlim(self):
		return [float(self.le_min.text()), float(self.le_max.text())]