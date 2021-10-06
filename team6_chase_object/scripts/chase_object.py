#!/usr/bin/env python

############################################################
# chase_object: Subscribes to a topic with the distance and 
# relative angle to the object
############################################################

import sys
import rospy
from geometry_msgs.msg import Twist, Point

###################################
## VARIABLE DECLARATION AND SETUP
###################################

# System Parameters
location_topic='target_loc'
BURGER_MAX_ANG_VEL = 2.84
BURGER_MAX_LIN_VEL = 4
distance_setpoint = 5
max_distance_error = 100
angle_setpoint = 0
max_angle_error = 31

#PID Variables - Angular
kpA = 1.875	#Gains for PID controller
kiA = 0
kdA = 0.125
kA = [kpA, kiA, kdA]

integrated_errorA = 0 # Initialize some variables for PID controller
old_errorA = 0.0
old_timeA = 0

#PID Variables - Linear
kpL = 1.875	#Gains for PID controller
kiL = 0
kdL = 0.125
kL = [kpL, kiL, kdL]

integrated_errorL = 0 # Initialize some variables for PID controller
old_errorL = 0.0
old_timeL = 0

twist = Twist()
pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)


###################################
## Function Declaration
###################################

def PID_method(error,delta_t,k,old_error,integrated_error):
	global old_time
    kp=k[0]; ki=k[1]; kd=k[2]
	integrated_error = integrated_error+delta_t*error
	derivative_error = kd*(error-old_error)/delta_t
	proportional_error = kp*error
	old_error=error
	return integrated_error+derivative_error+proportional_error, old_error, integrated_error

def callback(data):
    angle = data.x
    distance = data.y

	# Get the new time and compute the delta_t 
	new_time = rospy.get_time()
	delta_t = new_time - old_time
	if delta_t < 0.001:
		delta_t = 0.001
	
	# Data>100 indicates the tracked object has left the camera frame and no motion will occur
	# Otherwise, we use the PID to generate velocity commands from the distance error

	if distance > 100:

		twist.linear.x = 0.0
        twist.angular.z = 0.0
	
	else:		

        angle_error = angle - angle_setpoint
		angle_velocity, old_errorA, integrated_errorA = \
            PID_method(-angle_error/max_angle_error, delta_t, kA, old_errorA, integrated_errorA)

		if vel_out>BURGER_MAX_ANG_VEL:
			vel_out=BURGER_MAX_ANG_VEL
		elif vel_out<-BURGER_MAX_ANG_VEL:
			vel_out=-BURGER_MAX_ANG_VEL

        distance_error = distance - distance_setpoint
        linear_velocity, old_errorL, integrated_errorL = \
            PID_method(distance_error/max_distance_error, delta_t, kL, old_errorL, integrated_errorL) 

        if vel_out>BURGER_MAX_LIN_VEL:
			vel_out=BURGER_MAX_LIN_VEL
		elif vel_out<-BURGER_MAX_LIN_VEL:
			vel_out=-BURGER_MAX_LIN_VEL

		twist.linear.x = linear_velocity
        twist.angular.z = angle_velocity

	pub.publish(twist)
	old_time=new_time

def shutdown_hook():
	twist.angular.z = 0.0
    twist.linear.x = 0.0
	pub.publish(twist)

def Init():
	rospy.init_node('move_robot', anonymous=True)
	old_time = rospy.get_time()
	sub = rospy.Subscriber(location_topic, Point, callback,queue_size=10)
    
###################################
## MAIN
###################################

if __name__=='__main__':
	Init()
	rospy.on_shutdown(shutdown_hook)
	rospy.spin()
