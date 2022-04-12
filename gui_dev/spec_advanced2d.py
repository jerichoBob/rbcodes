from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit
from PyQt5.QtCore import Qt

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
import copy

class ShowAdvanced(QWidget):
	def __init__(self, img, name=None):
		super().__init__()
		# stored variables
		self.img = img
		self.scale = 0
		self.normalization = 0
		self.name = name
		self.img_lim = [0., 1.]
		self.namebox = ['STAMP', 'CONTAMINATION']

		# overall widget layout
		layout = QVBoxLayout()

		# scaling widgets layout
		scale_layout = QHBoxLayout()
		# Scaling label
		s_label = QLabel('Scale:')
		s_label.setFixedWidth(50)
		scale_layout.addWidget(s_label)
		# scaling dropbox
		self.s_combobox = QComboBox()
		self.s_combobox.setFixedWidth(100)
		self.s_combobox.setMaxCount(4)
		self.s_combobox.addItems(['Linear', 'Log', 'Sqrt', 'Square'])
		self.s_combobox.setCurrentIndex(0)
		self.s_combobox.currentIndexChanged.connect(self._scaling_changed)
		scale_layout.addWidget(self.s_combobox)

		# normalization dropbox
		self.n_combobox = QComboBox()
		self.n_combobox.setFixedWidth(100)
		self.n_combobox.setMaxCount(12)
		self.n_combobox.addItems(['None','MinMax', '99.5%', '99%', '98%', '97%', '96%', '95%', '92.5%', '90%', 'Z-Score', 'Manual'])
		self.n_combobox.setCurrentIndex(0)
		self.n_combobox.currentIndexChanged.connect(self._normalization_changed)
		scale_layout.addWidget(self.n_combobox)

		# normalization range
		self.min_range = QLineEdit()
		self.min_range.setFixedWidth(100)
		scale_layout.addWidget(self.min_range)
		self.min_range.setPlaceholderText('Min')
		self.min_range.returnPressed.connect(self._return_pressed)
		self.max_range = QLineEdit()
		self.max_range.setFixedWidth(100)
		self.max_range.setPlaceholderText('Max')
		self.max_range.returnPressed.connect(self._return_pressed)
		scale_layout.addWidget(self.max_range)
		scale_layout.setAlignment(Qt.AlignLeft)
		layout.addLayout(scale_layout)

		
		self.advobj = Advanced2dCanvas()
		self.img_lim = self.advobj._imshow(img, name=self.name)
		self._scale_limits_changed(self.img_lim)
		mpl_toolbar = NavigationToolbar(self.advobj, self)
		layout.addWidget(mpl_toolbar)
		layout.addWidget(self.advobj)
		self.setLayout(layout)
		self.setMinimumSize(600,600)
		self.setWindowTitle(name + ' Inspection')

	def _scaling_changed(self, i):
		self.scale = i
		self.img_lim = self.advobj._imshow(self.img, 
							scale=self.scale,
							normalization=self.normalization,
							name=self.name)
		self._scale_limits_changed(self.img_lim)

	def _normalization_changed(self, i):
		if i < 11:
			self.normalization = i
			self.img_lim = self.advobj._imshow(self.img, 
								scale=self.scale,
								normalization=self.normalization,
								name=self.name)
			self._scale_limits_changed(self.img_lim)

	def _scale_limits_changed(self, limits):
		precision = 3
		self.min_range.setText(str(round(limits[0], precision)))
		self.max_range.setText(str(round(limits[1], precision)))

	def _return_pressed(self):
		# min,max current values
		manual_range = [float(self.min_range.text()), float(self.max_range.text())]
		# sort and assign min,max values to avoid user errors
		manual_range.sort()
		self.min_range.setText(str(manual_range[0]))
		self.max_range.setText(str(manual_range[-1]))


		self.n_combobox.setCurrentIndex(11)
		_ = self.advobj._imshow(self.img,
							scale=self.scale,
							normalization=manual_range,
							name=self.name)


class Advanced2dCanvas(FigureCanvasQTAgg):
	def __init__(self, parent=None, width=6, height=6, dpi=100):
		self.fig = Figure(figsize=(width, height), dpi=dpi)
		self.fig.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)
		super().__init__(self.fig)
		self.fig.canvas.setFocusPolicy(Qt.ClickFocus)
		self.fig.canvas.setFocus()

	def _imshow(self, img, scale=0, normalization=0, name=''):
		self.fig.clf()
		self.ax = self.fig.add_subplot(111)
		#self.ax.cla()

		if scale == 0:
			# Linear.. nothing happened
			#scaled2d = self.flux2d.copy()
			scaled2d = img.copy()
		elif scale == 1:
			# log transformation.. scaled = log(1+ img)/log(1+img_max)
			#if self.flux2d.min() < 0:
			#	scaled2d = np.log(-self.flux2d.min() + self.flux2d) / np.log(-self.flux2d.min() + self.flux2d.max())
			if img.min() < 0:
				scaled2d = np.log(-img.min() + img) / np.log(-img.min() + img.max())
			else:
				#scaled2d = np.log(1 + self.flux2d) / np.log(1 + self.flux2d.max())
				scaled2d = np.log(1 + img) / np.log(1 + img.max())
		elif scale == 2:
			# square root transformation.. 
			# pixel values > 0 ==> regular sqrt; pixel values <0 ==> 1.absolute value 2.sqrt 3.add minus sign
			#scaled2d = copy.deepcopy(self.flux2d)
			scaled2d = copy.deepcopy(img)
			scaled2d[scaled2d>=0] = np.sqrt(scaled2d[scaled2d>=0])
			scaled2d[scaled2d<0] = -np.sqrt(-scaled2d[scaled2d<0])
		elif scale == 3:
			#scaled2d = self.flux2d**2
			scaled2d = img**2

		# normalization next
		# send scaling limits back to toolbar
		if type(normalization) is int:
			#print(scaled2d)
			if normalization == 0:
				pass
				#self.send_scale_limits.emit([scaled2d.min(), scaled2d.max()])
			elif normalization == 1:
				# minmax 100% range
				scaled2d = (scaled2d - scaled2d.min()) / (scaled2d.max() - scaled2d.min())
			elif normalization < 10: # this magic num from n_combobox in toolbar
				if normalization == 2: # 99.5%
					low, up = np.percentile(scaled2d, [0.25, 99.75])
				elif normalization == 3: # 99%
					low, up = np.percentile(scaled2d, [0.5, 99.5])
				elif normalization == 4: # 98%
					low, up = np.percentile(scaled2d, [1., 99.])
				elif normalization == 5: # 97%
					low, up = np.percentile(scaled2d, [1.5, 98.5])
				elif normalization == 6: # 96%
					low, up = np.percentile(scaled2d, [2., 98.])
				elif normalization == 7: # 95%
					low, up = np.percentile(scaled2d, [2.5, 97.5])
				elif normalization == 8: # 92.5%
					low, up = np.percentile(scaled2d, [3.75, 96.25])
				elif normalization == 9: # 90%
					low, up = np.percentile(scaled2d, [5., 95.])

				scaled2d = (scaled2d - low) / (up - low)

			elif normalization == 10: # Z-score
				scaled2d = (scaled2d - scaled2d.mean()) / scaled2d.std()

		elif type(normalization) == list:
			tmp = (scaled2d - scaled2d.min()) / (scaled2d.max() - scaled2d.min())
			scaled2d = tmp*(normalization[1] - normalization[0]) + normalization[0]
			
		if scale == 1:
			pos_ax = self.ax.imshow(scaled2d, origin='lower', 
									vmin=scaled2d.min(), vmax=scaled2d.max() * 0.01)
		else:
			pos_ax = self.ax.imshow(scaled2d, origin='lower', 
									vmin=scaled2d.min(), vmax=scaled2d.max() * 1.0)
		

		self.ax_cb = self.fig.colorbar(pos_ax, ax=self.ax, location='right')
		ax_xlim = self.ax.get_xlim()
		#self.ax.tick_params(labelbottom=False)
		#self.ax2d.set_xlim(xlim_spec1d)
		self.ax.set_aspect('auto')
		if len(name) > 1:
			self.ax.set_title(name + ' of Current Object')		
		self.draw()

		return [scaled2d.min(), scaled2d.max()]