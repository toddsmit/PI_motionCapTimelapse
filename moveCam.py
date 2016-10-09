#!/usr/bin/python
#import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_Stepper 
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor

import os
import time
import atexit
import Image
import numpy
import picamera
import picamera.array

#####
# Stepper motor helper functions
#
# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
	mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
	mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
	mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
	mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

def convert_to_secs(s):
	l = s.split(':')
	val = (int(l[0]) * 3600) + (int(l[1]) * 60) + int(l[2])
	print 'secs = {:d}'.format(val)
	return val




#####
# Camera helper functions
#
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


def smooth_cap(cam, exp, fn, steps):
	t0 = time.time()
	raw = numpy.empty([exp, 720, 1280, 3], dtype=numpy.uint8)
	steps_per_cap = steps / exp / 2
	steps_final = steps - (steps_per_cap * exp)
	print("Steps cap {} fin {}".format(steps_per_cap, steps_final))

	for ex in range(0, exp):
		time.sleep(0.5) #Allow some time after stepper movement to remove camera shake
		cam.capture(output, 'rgb')
		###print(output.array.shape)
		###print('Captured %dx%d image R%d G%d B%d' % ( output.array.shape[1], output.array.shape[0],
		###	output.array[700, 1200, 0],
		###	output.array[700, 1200, 1],
		###	output.array[700, 1200, 2],
		###	))
		raw[ex] = output.array
		output.truncate(0)
		###print ("S1 {}".format(time.time()-t0))
		#myStepper.step(steps_per_cap, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
		myStepper.step(steps_per_cap, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.MICROSTEP)


	smoothed = numpy.average(raw, axis=0).astype(numpy.uint8)
	###print ("S2 {}".format(time.time()-t0))
	###print(smoothed.shape)
	###print('Smoothed %dx%d image R%d G%d B%d' % ( smoothed.shape[1], smoothed.shape[0],
	###		smoothed[700, 1200, 0],
	###		smoothed[700, 1200, 1],
	###		smoothed[700, 1200, 2],
	###		))

	im = Image.fromarray(smoothed, 'RGB')
	im.save(fn)
	print ("DONE {}".format(time.time()-t0))
	#myStepper.step(steps_final, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
	myStepper.step(steps_final, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.MICROSTEP)



#####
# Init filepaths
#
#get CWD and define where the captures will be saved
home_dir = os.path.expanduser("~")
capture_dir = home_dir + "/timelapse"
print capture_dir
os.chdir(capture_dir)


#####
# Init stepper motors
#
# create a default object, no changes to I2C address or frequency
mh = Adafruit_MotorHAT()
atexit.register(turnOffMotors)
myStepper = mh.getStepper(200, 2)  	# 200 steps/rev, motor port #2
myStepper.setSpeed(30)  		# 60 RPM


#####
# Get user input
#
capture_ET = convert_to_secs(raw_input('real ET in HH:MM:SS ') or "3:0:0")
movie_secs = convert_to_secs(raw_input('movie time in HH:MM:SS ') or "0:0:5")
movie_FPS = int(raw_input('Enter movie FPS: ') or "24")
movie_num = int(raw_input('Enter movie number: ') or "1")
stepper_revs = int(raw_input('Enter total stepper revs for cap: ') or "12")
movie_frames = movie_secs * movie_FPS
steps_per_frame = int((stepper_revs * 200) / movie_frames)
sleep_sec = float(capture_ET / movie_frames)
pre_position = int(raw_input('Enter +- initial steps: ') or "0")

print 'Capturing movie {} with {} frames using {} stepper movement sleeping {} sec between frames'.format(movie_num, movie_frames, steps_per_frame, sleep_sec)


#####
# Initial positioning
#
if (pre_position > 0):
	myStepper.step(pre_position, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
elif (pre_position < 0):
	myStepper.step(-pre_position, Adafruit_MotorHAT.BACKWARD,  Adafruit_MotorHAT.DOUBLE)
else:
	print 'Starting capture from current position'

#####
# Capture loop
#
with picamera.PiCamera() as camera:
	with picamera.array.PiRGBArray(camera) as output:
		init_cam(camera)

		start_time = time.time()
		for frame in range(0, (movie_frames - 1)):
			# Capture image
			fname = "M{}_F{:04d}.jpg".format(movie_num, frame)
			#camera.capture(fname)
			smooth_cap(camera, 4, fname, steps_per_frame)

			# Move camera
			#print("{} Microsteps".format(steps_per_frame))
			#myStepper.step(steps_per_frame, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.SINGLE)
			#myStepper.step(steps_per_frame, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
			#myStepper.step(steps_per_frame, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.MICROSTEP)

			# Sleep until time for next frame
			next_sleep = start_time + ((frame + 1) * sleep_sec) - time.time()
			if (next_sleep > 0):
				print("sleeping {}".format(next_sleep))
				time.sleep(next_sleep)


#####
# Create movie from still images
#
movie_cmd = "gst-launch-1.0 multifilesrc location=M{0}_F%04d.jpg index=1 caps='image/jpeg,framerate=24/1' ! jpegdec ! omxh264enc ! avimux ! filesink location=timelapse_{0}.avi".format(movie_num)
os.system(movie_cmd)


#####
# Cleanup still images
#
cleanup_cmd = "rm -f {0}/M{1}_*.jpg".format(capture_dir, movie_num)
os.system(cleanup_cmd)

raw_input("Hit ENTER to rewind stepper ")
myStepper.setSpeed(30) #RPM
myStepper.step((steps_per_frame * movie_frames), Adafruit_MotorHAT.BACKWARD,  Adafruit_MotorHAT.SINGLE)
