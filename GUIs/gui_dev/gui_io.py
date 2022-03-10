import sys
import os
from astropy.io import fits
import numpy as np

from utils import FitsObj
# use test.fits from rbcodes/example-data as testing example
'''
file = fits.open('test.fits')
file.info()
Filename: test.fits
No.    Name      Ver    Type      Cards   Dimensions   Format
  0  FLUX          1 PrimaryHDU      10   (19663,)   float32
  1  ERROR         1 ImageHDU         7   (19663,)   float32
  2  WAVELENGTH    1 ImageHDU         7   (19663,)   float64
  3  CONTINUUM     1 ImageHDU         7   (19663,)   float32


NEED TO FIND A BETTER WAY TO TELL IF A FITS FILE HAS 1D(spec) OR 2D(image) DATA
'''

# This class is used to load spectrum from fits (unknown format) and save spectrum to fits file (our format)
class LoadSpec():
	def __init__(self, filepath):
		self.filepath = filepath
		self.fitsobj = FitsObj(wave=[], flux=None, error=None)


	def _load_spec(self):
		# read fits file
		fitsfile = fits.open(self.filepath)

		# for a pair of fits files:
		# cal-2D, x1d-1D
		if fitsfile.filename().endswith('cal.fits'):
			self.fitsobj.flux2d = fitsfile['SCI'].data
			self.fitsobj.error2d = fitsfile['ERR'].data
			
			# search 1D file and open
			fits1d = fitsfile.filename()[:-8] + 'x1d.fits'
			if os.path.exists(fits1d):
				fitsfile1d = fits.open(fits1d)
				scale = self._scale_wave_unit(fitsfile1d['EXTRACT1D'].header)
				self.fitsobj.wave = fitsfile1d['EXTRACT1D'].data['WAVELENGTH'] * scale
				self.fitsobj.flux = fitsfile1d['EXTRACT1D'].data['FLUX']
				self.fitsobj.error = fitsfile1d['EXTRACT1D'].data['FLUX_ERROR']
				fitsfile1d.close()
			fitsfile.close()
			return self.fitsobj

		elif fitsfile.filename().endswith('x1d.fits'):
			scale = self._scale_wave_unit(fitsfile['EXTRACT1D'].header)
			self.fitsobj.wave = fitsfile['EXTRACT1D'].data['WAVELENGTH'] * scale
			self.fitsobj.flux = fitsfile['EXTRACT1D'].data['FLUX']
			self.fitsobj.error = fitsfile['EXTRACT1D'].data['FLUX_ERROR']

			# search 2D file and open
			fits2d = fitsfile.filename()[:-8] + 'cal.fits'
			print('prepare 2D spec')
			if os.path.exists(fits2d):
				fitsfile2d = fits.open(fits2d)
				self.fitsobj.flux2d = fitsfile2d['SCI'].data
				self.fitsobj.error2d = fitsfile2d['ERR'].data
				fitsfile2d.close()
			fitsfile.close()
			return self.fitsobj





		# CHECK IF FITS FILE HAS AN IMAGE
		if (fitsfile[0].header['NAXIS'] > 1) & (len(fitsfile) < 2):
			# example file: long_radd.fits
			# delete this condition if long_radd.fits is no longer used
			if 'long_radd' in fitsfile.filename().split('.')[0]:
				self.fitsobj.flux2d = np.transpose(fitsfile[0].data)
			else:
				self.fitsobj.flux2d = fitsfile[0].data
			wave0,wave1 = fitsfile[0].header['ADCWAVE0'], fitsfile[0].header['ADCWAVE1']
			self.fitsobj.wave = np.linspace(wave0, wave1, len(self.fitsobj.flux2d[0]))
			# fake error 2d spectrum
			self.fitsobj.error2d = self.fitsobj.flux2d * 0.05

			fitsfile.close()
			return self.fitsobj

		elif (fitsfile[0].header['NAXIS']==0) & (fitsfile[1].header['NAXIS']==2):
			if fitsfile[1].name in 'SCI':
	    		#Read in a specific format to account for EIGER emission line 2d spectrum
				# example file: spec2d_coadd_QSO_J0100_sID010242.fits
				self.fitsobj.flux2d = fitsfile['SCI'].data
				self.fitsobj.error2d = fitsfile['ERR'].data
				self.fitsobj.wave = self._build_wave(fitsfile['SCI'].header)
				# Set RA DEC
				self.fitsobj.ra = fitsfile['SCI'].header['RA']
				self.fitsobj.dec = fitsfile['SCI'].header['DEC']

				fitsfile.close()
				return self.fitsobj

			elif fitsfile[1].name in 'COADD':
				'''FITS format 2:
				file[i].data['<variable>']
				for multiple i HDU table/image
				example file: SDSS_spec.fits
				Note: sdss1.fits is okay; sdss2.fits has header PLUG_RA
				'''
				for i in range(len(fitsfile)):
					search_list = np.array(fitsfile[i].header.cards)
					if 'flux' in search_list:
						self.fitsobj.flux = fitsfile[i].data['flux']
					elif 'FLUX' in search_list:
						self.fitsobj.flux = fitsfile[i].data['FLUX']

					if 'loglam' in search_list:
						self.fitsobj.wave = 10**(fitsfile[i].data['loglam'])
					elif 'WAVELENGTH' in search_list:
						self.fitsobj.wave = fitsfile[i].data['WAVELENGTH']

					if 'ivar' in search_list:
						self.fitsobj.error = 1. / np.sqrt(fitsfile[i].data['ivar'])
					elif 'ERROR' in search_list:
						self.fitsobj.error = fitsfile[i].data['ERROR']

					if 'RA' in search_list:
						self.fitsobj.ra = fitsfile[i].header['RA']
					if 'DEC' in search_list:
						self.fitsobj.dec = fitsfile[i].header['DEC']

				fitsfile.close()
				return self.fitsobj

		# CHECK IF FITS FILE HAS 1D SPECTRAL INFO...
		# find wavelength, flux, error
		elif 'FLUX' in fitsfile:
			'''FITS format 1:
				file['<variable>'].data
			example file: test.fits
			'''
			self.fitsobj.wave = fitsfile['WAVELENGTH'].data
			self.fitsobj.flux = fitsfile['FLUX'].data
			self.fitsobj.error = fitsfile['ERROR'].data

			fitsfile.close()
			print(type(self.fitsobj))
			return self.fitsobj


	def _build_wave(self, header):
		'''Returns a NumPy array containing wavelength axis of a 2d specturm in Angstrom.
			Args:
				header (astropy.io.fits.Header): header that contains wavelength axis
				that is specified in 'CTYPE' keywords in NAXIS1 dimension.
			Returns:
				numpy.ndarray: Wavelength axis for this data.
		'''
		#Get keywords defining wavelength axis
		nwav = header['NAXIS1']
		wav0 = header['CRVAL1']
		dwav = header['CDELT1']
		pix0 = header['CRPIX1']
		wave=np.array([wav0 + (i - pix0) * dwav for i in range(nwav)])

		# Now check units to make sure everything is in angstrom
		card='CUNIT1'
		if not card in header:
			raise ValueError("Header must contain 'CUNIT1' keywords.")
			#micrometer to Angstrom
		if header[card] =='um':
			wave *=10000. 
		elif header[card]=='nm':
			wave *=10
		elif header[card]=='Angstrom':
		#elif header[card]=='AA':
			wave=wave
		else:
			raise ValueError("Predefined wavelength units are 'um','nm','AA'.")            
		return wave

	def _scale_wave_unit(self, header):
		# if wavelength array already existed,
		card = 'TUNIT1'
		if not card in header:
			raise ValueError("Header must contain 'TUNIT1' keywords.")
			#micrometer to Angstrom
		if header[card] =='um':
			scale = 10000. 
		elif header[card]=='nm':
			scale = 10.
		elif header[card]=='Angstrom':
		#elif header[card]=='AA':
			scale = 1.
		else:
			raise ValueError("Predefined wavelength units are 'um','nm','AA'.")            
		return scale