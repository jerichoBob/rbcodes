import sys


# ------------- Utility classes ------------------------
# define as many classes we want that are not classified in other classes

class FitsObj():
	def __init__(self, wave=None, flux=None, error=None, 
				ra=None, dec=None, z_est=None, flag=None,
				flux2d=None, error2d=None, stamp=None):
		self.wave = wave
		self.flux = flux
		self.error = error
		self.ra = ra
		self.dec = dec
		self.z_est = z_est
		self.flag = flag

		# if fits file contains an image
		self.flux2d = flux2d
		self.error2d = error2d
		self.stamp = stamp

class Fits_2dAux():
	def __init__(self, stamp=None, contamination=None):
		self.stamp = stamp
		self.contamination = contamination