#!/usr/bin/env python

###############
# ROS IMPORTS #
###############
import rospy
import tf
import tf.transformations as tr
from geometry_msgs.msg import Twist, Pose2D

###################
# NON ROS IMPORTS #
###################
import numpy as np


####################
# GLOBAL CONSTANTS #
####################
PARENT_FRAME = "odom"
CHILD_FRAME = "robot_1"
INTEGRATION_FREQ = 250 # Hz
INITIAL_POSE = np.array([0, 0, 0.])


# CREATE MAIN CLASS:
class DiffDriveIntegrator( object ):
    def __init__(self):
        rospy.loginfo("Creating DiffDriveIntegrator class!")

        # read all parameters:
        self.parent = rospy.get_param("~parent", PARENT_FRAME)
        self.child = rospy.get_param("~child", CHILD_FRAME)
        self.freq = rospy.get_param("~freq", INTEGRATION_FREQ)

        # create random variables that we are going to need:
        self.current_pose = INITIAL_POSE
        self.current_vel = np.zeros(2)

        # create all subscribers, timers, publishers, listeners, broadcasters,
        # etc.
        self.br = tf.TransformBroadcaster()
        self.pos_pub = rospy.Publisher("pose_est", Pose2D, queue_size=10)
        self.cmd_sub = rospy.Subscriber("cmd_vel", Twist, self.twist_callback)
        self.int_timer = rospy.Timer(rospy.Duration(1/float(self.freq)), self.integrate_callback)
        return

    def integrate_callback(self, tdat):
        v = self.current_vel[0]
        w = self.current_vel[1]

        self.current_pose += (1/float(self.freq))*np.array([
            v*np.cos(self.current_pose)[2],
            v*np.sin(self.current_pose)[2],
            w])

        #publish current estimated pose to diffdrive_velocity controller via pose_est topic
        p_est = Pose2D()
        p_est.x = self.current_pose[0]
        p_est.y = 0
        p_est.theta = self.current_pose[2]

        self.pos_pub.publish(p_est)

        # now let's send that pose data out as a tf message:
        pos, quat = self.pose_arr_to_tf(self.current_pose)
        self.br.sendTransform(pos, quat, rospy.Time.now(), self.child, self.parent)

        return

    def twist_callback(self, command):
        self.current_vel = self.twist_to_vel_arr(command)
        return

    def pose_arr_to_tf(self, pose):
        pos = [pose[0], pose[1], 0]
        quat = tr.quaternion_from_euler(0, 0, pose[2], 'sxyz')
        return pos, quat

    def twist_to_vel_arr(self, twist):
        vel = np.array([twist.linear.x, twist.angular.z])
        return vel


def main():
    rospy.init_node('diff_drive_integrator', log_level=rospy.INFO)

    try:
        integrator = DiffDriveIntegrator()
    except rospy.ROSInterruptException:
        pass

    rospy.spin()


if __name__=='__main__':
    main()


