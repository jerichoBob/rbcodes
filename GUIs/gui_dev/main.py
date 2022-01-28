import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStatusBar, QVBoxLayout, QLabel
from PyQt5 import QtCore
from menu_toolbars import Custom_ToolBar, Custom_MenuBar
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


from spec_plot import MplCanvas

class MainWindow(QMainWindow):
	'''This is the main window of this GUI
	This class only assembles different widgets from customed components.
	'''
	def __init__(self):
		super().__init__()

		# --------- Assembling All Widgets ------------------- 
		#placeholder to hold the central widget in main window
		widget = QWidget()
		widget.setMinimumSize(800, 600)

		self.sc = MplCanvas(self, width=10, height=8, dpi=100)
		mpl_toolbar = NavigationToolbar(self.sc, self)
		#self.sc.axes.imshow('cat.jpg')

		l_in = QLabel('User Input >> guess z')
		l_in.setAlignment(QtCore.Qt.AlignCenter)
		l_out = QLabel('GUI Output >> Gaussian profile, EW, etc')
		l_out.setAlignment(QtCore.Qt.AlignCenter)
		layout = QVBoxLayout()
		layout.addWidget(mpl_toolbar)
		layout.addWidget(self.sc)
		layout.addWidget(l_in)
		layout.addWidget(l_out)
		widget.setLayout(layout)

		# MainWindow parameters
		self.setCentralWidget(widget)
		self.setWindowTitle('Spectrum Analysis GUI')
		

		# --------- Menus and Toolbars -----------------------
		self.setStatusBar(QStatusBar(self))
		toolbar = Custom_ToolBar(self)
		self.addToolBar(toolbar)

		menubar = Custom_MenuBar(self)
		self.setMenuBar(menubar)



app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()