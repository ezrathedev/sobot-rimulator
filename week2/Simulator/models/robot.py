#!/usr/bin/python
# -*- Encoding: utf-8 -*

from math import *
from differential_drive_dynamics import *
from polygon import *
from pose import *
from proximity_sensor import *
from supervisor import *
from wheel_encoder import *

# Khepera3 Properties (copied from Sim.I.Am by J.P. de la Croix)
K3_WHEEL_RADIUS = 0.021         # meters
K3_WHEEL_BASE_LENGTH = 0.0885   # meters
K3_WHEEL_TICKS_PER_REV = 2765
K3_SPEED_FACTOR = 6.2953e-6     
K3_TRANS_VEL_LIMIT = 0.3148     # m/s
K3_ANG_VEL_LIMIT = 2.2763       # rad/s

# Khepera3 Dimensions (copied from Sim.I.Am by J.P. de la Croix)
K3_BOTTOM_PLATE = [ [ -0.024, 0.064 ],
                    [ 0.033, 0.064 ],
                    [ 0.057, 0.043 ],
                    [ 0.074, 0.010 ],
                    [ 0.074, -0.010 ],
                    [ 0.057, -0.043 ],
                    [ 0.033, -0.064 ],
                    [ -0.025, -0.064 ],
                    [ -0.042, -0.043 ],
                    [ -0.048, -0.010 ],
                    [ -0.048, 0.010 ],
                    [ -0.042, 0.043 ] ]

K3_SENSOR_MIN_RANGE = 0.02
K3_SENSOR_MAX_RANGE = 0.2
K3_SENSOR_POSES = [ [-0.038, 0.048, 128], # x, y, theta_degrees
                    [0.019, 0.064, 75],
                    [0.050, 0.050, 42],
                    [0.070, 0.017, 13],
                    [0.070, -0.017, -13],
                    [0.050, -0.050, -42],
                    [0.019, -0.064, -75],
                    [-0.038, -0.048, -128],
                    [-0.048, 0.00, 180] ]

class Robot: # Khepera3 robot 
  
  def __init__( self ):
    # geometry
    self.geometry = Polygon( K3_BOTTOM_PLATE )
    self.global_geometry = Polygon( K3_BOTTOM_PLATE ) # actual geometry in world space

    # wheel arrangement
    self.wheel_radius = K3_WHEEL_RADIUS             # meters
    self.wheel_base_length = K3_WHEEL_BASE_LENGTH   # meters
    
    # wheel speed factor
    self.speed_factor = K3_SPEED_FACTOR

    # pose
    self.pose = Pose( 0.0, 0.0, 0.0 )

    # wheel encoders
    self.left_wheel_encoder = WheelEncoder( K3_WHEEL_RADIUS, K3_WHEEL_TICKS_PER_REV )
    self.right_wheel_encoder = WheelEncoder( K3_WHEEL_RADIUS, K3_WHEEL_TICKS_PER_REV )
    self.wheel_encoders = [ self.left_wheel_encoder, self.right_wheel_encoder ]
    
    # IR sensors
    self.ir_sensors = []
    for _pose in K3_SENSOR_POSES:
      ir_pose = Pose( _pose[0], _pose[1], radians( _pose[2] ) )
      self.ir_sensors.append(
          ProximitySensor( self, ir_pose, K3_SENSOR_MIN_RANGE, K3_SENSOR_MAX_RANGE, radians( 20 ) ) )

    # dynamics
    self.dynamics = DifferentialDriveDynamics( self.wheel_radius, self.wheel_base_length )

    # supervisor
    self.supervisor = Supervisor( self )
    
    ## initialize state
    # set wheel drive rates (rad/s)
    self.left_wheel_drive_rate = 0.0
    self.right_wheel_drive_rate = 0.0

  # simulate the robot's motion over the given time interval
  def step_motion( self, dt ):
    v_l = self.left_wheel_drive_rate
    v_r = self.right_wheel_drive_rate

    # step robot pose
    self.dynamics.apply_dynamics( self.pose, v_l, v_r, dt )

    # update wheel encoders
    self.left_wheel_encoder.step_ticks( v_l, dt )
    self.right_wheel_encoder.step_ticks( v_r, dt )

    # update global geometry
    self.global_geometry = self.geometry.get_transformation_to_pose( self.pose )
    
    # update all of the sensors
    for ir_sensor in self.ir_sensors:
      ir_sensor.update_position()
  
  # read the proximity sensors
  def read_proximity_sensors( self ):
    return [ s.read() for s in self.ir_sensors ]

  # read the wheel encoders
  def read_wheel_encoders( self ):
    return [ e.read() for e in self.wheel_encoders ]
  
  # set the drive rates (angular velocities) for this robot's wheels in rad/s 
  def set_wheel_drive_rates( self, v_l, v_r ):
    # limit the speeds:
    v, w = self.dynamics.diff_to_uni( v_l, v_r )
    v = max( min( v, K3_TRANS_VEL_LIMIT ), -K3_TRANS_VEL_LIMIT )
    w = max( min( w, K3_ANG_VEL_LIMIT ), -K3_ANG_VEL_LIMIT )
    v_l, v_r = self.dynamics.uni_to_diff( v, w )
    
    # set drive rates
    self.left_wheel_drive_rate = v_l
    self.right_wheel_drive_rate = v_r
