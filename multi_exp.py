#!/usr/bin/python

import Image
import numpy
import time
import picamera
import picamera.array

def init_cam(cam):
	#Setup static camera setings
	cam.resolution = (1280, 720)
	cam.framerate = 30
	# Wait for the automatic gain control to settle
	time.sleep(2)
	# Now fix the values
	cam.shutter_speed = cam.exposure_speed
	cam.exposure_mode = 'off'
	g = cam.awb_gains
	cam.awb_mode = 'off'
	cam.awb_gains = g
	cam.hflip = True
	cam.vflip = True


def smooth_cap(cam, exp, fn):
	raw = numpy.empty([exp, 720, 1280, 3], dtype=numpy.uint8)

	for ex in range(0, exp):
		time.sleep(2)
		cam.capture(output, 'rgb')
		print(output.array.shape)
		print('Captured %dx%d image R%d G%d B%d' % ( output.array.shape[1], output.array.shape[0],
			output.array[700, 1200, 0],
			output.array[700, 1200, 1],
			output.array[700, 1200, 2],
			))
		raw[ex] = output.array
		output.truncate(0)


	smoothed = numpy.average(raw, axis=0).astype(numpy.uint8)
	print(smoothed.shape)
	print('Smoothed %dx%d image R%d G%d B%d' % ( smoothed.shape[1], smoothed.shape[0],
			smoothed[700, 1200, 0],
			smoothed[700, 1200, 1],
			smoothed[700, 1200, 2],
			))

	im = Image.fromarray(smoothed, 'RGB')
	im.save(fn)




with picamera.PiCamera() as camera:
	with picamera.array.PiRGBArray(camera) as output:
		init_cam(camera)
		smooth_cap(camera, 4, 'todd2.jpg')
