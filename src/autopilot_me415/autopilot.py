#!/usr/bin/env python
import rospy
from rosflight_msgs.msg import GPS, Command
import numpy as np


class autopilot:

    def __init__(self):
        # GPS update rate (also command update rate)
        self.update_rate = 10  # Hz

        # defile floor/ceiling
        self.elevation = 1508.0
        ft2m = 0.3048
        alt_tolerance = 25*ft2m
        self.floor = self.elevation + 100*ft2m
        self.ceiling = self.elevation + 400*ft2m
        self.floorwarn = self.floor + alt_tolerance
        self.ceilingwarn = self.ceiling - alt_tolerance

        # define boundary
        self.bdy_center = [40.2672305, -111.635524]
        self.bdy_R = [98.353826748828595, 127.49653449395105]
        self.bdy_theta = -15*np.pi/180.0

        # define waypoints
        self.wp1 = [40.26702297859316, -111.63508476781465]
        self.wp2 = [40.267641059243935, -111.63587333726502]
        self.wp3 = [40.26658909078882, -111.6358518795929]
        self.wp4 = [40.26778432216462, -111.63506331014253]
        self.wp_state_machine = 0
        self.wp_tolerance = 10.0  # m

        # subscripte to GPS
        self.gps_subscriber = rospy.Subscriber("/fixedwing/gps", GPS, self.gpsCallback, queue_size=10)
        self.currentGPS = GPS()

        # set timer and command publisher
        rospy.Timer(rospy.Duration(1./self.update_rate), self.control)
        rospy.Timer(rospy.Duration(1./self.update_rate), self.check_status)
        self.command_publisher = rospy.Publisher("/fixedwing/command", Command, queue_size=1)



    def gpsCallback(self, msg):
        if msg.fix and msg.NumSat > 3:
            self.currentGPS = msg

    def control(self, event):

        command = Command()
        command.mode = command.MODE_PASS_THROUGH
        command.ignore = command.IGNORE_NONE

        # edit starting right here!!!!

        # you can get GPS sensor information:
        # self.currentGPS.latitude # Deg
        # self.currentGPS.longitude # Deg
        # self.currentGPS.altitude # m
        # self.currentGPS.speed # m/s
        # self.currentGPS.ground_course # rad clockwise from the north

        command.F = 0.75  # throttle command 0.0 to 1.0
        command.x = 0.0  # aileron servo command -1.0 to 1.0  positive rolls to right
        command.y = -0.03  # elevator servo command -1.0 to 1.0  positive pitches up
        command.z = 0.0  # rudder servo command -1.0 to 1.0  positive yaws to left

        self.command_publisher.publish(command)

    def check_status(self, event):

        # ---- altitude checks -----
        alt = self.currentGPS.altitude

        if alt < self.floor:
            print "ALERT!  Altitude too low! Resume manual control!"
            return
        elif alt < self.floorwarn:
            print "WARNING!  Altitude approaching floor! Ready pilot."
            return
        elif alt > self.ceiling:
            print "ALERT!  Altitude too high! Resume manual control!"
            return
        elif alt > self.ceilingwarn:
            print "WARNING!  Altitude approaching ceiling! Ready pilot."
            return


        # ---- boundary checks ----
        pos = [self.currentGPS.latitude, self.currentGPS.longitude]

        ell = self.ellipse(pos)
        if ell > 1.0:
            print "ALERT!  Out of bounds! Resume manual control!"
            return
        elif ell > 0.7:
            print "WARNING!  Close to boundary! Ready pilot."
            return


        # ---- waypoint checks -----

        if self.wp_state_machine == 0 and self.distance(pos, self.wp1) < self.wp_tolerance:
            self.wp_state_machine = 1
            print "YES!  Achieved waypoint 1!"
        elif self.wp_state_machine == 1 and self.distance(pos, self.wp2) < self.wp_tolerance:
            self.wp_state_machine = 2
            print "YES!  Achieved waypoint 2!"
        elif self.wp_state_machine == 2 and self.distance(pos, self.wp3) < self.wp_tolerance:
            self.wp_state_machine = 3
            print "YES!  Achieved waypoint 3!"
        elif self.wp_state_machine == 3 and self.distance(pos, self.wp4) < self.wp_tolerance:
            self.wp_state_machine = 4
            print "YES!  Achieved waypoint 4!"
            print "CONGRATULATIONS! All waypoints achieved!!!"


    def distance(pt1, pt2):
        """pt = [lat, long]"""
        EARTH_RADIUS = 6371000.0
        distN = EARTH_RADIUS*(pt2[0] - pt1[0])*np.pi/180.0
        distE = EARTH_RADIUS*np.cos(pt1[0]*np.pi/180.0)*(pt2[1] - pt1[1])*np.pi/180.0
        return distE, distN, np.linalg.norm([distN, distE])


    def ellipse(pt):
        """check if point is outside of boundary ellipse (ell > 1)"""

        center = self.bdy_center
        R = self.bdy_R
        theta = self.bdy_theta

        dx, dy, _ = distance(center, pt)
        ct = np.cos(theta)
        st = np.sin(theta)
        ell = ((dx*ct + dy*st)/R[0])**2 + ((dx*st - dy*ct)/R[1])**2

        return ell

if __name__ == '__main__':
    rospy.init_node('autopilot_py', anonymous=True)
    ap = autopilot()
    rospy.spin()