#! /usr/bin/env python

import rospy
import quadruped_msgs.msg
from tf.transformations import *
import geometry_msgs.msg

def load_from_file(file_path, source_frame_id):
    import os
    import tf
    from rosparam import load_file
    if not os.path.isfile(file_path):
        rospy.logerr('File with path "' + file_path + '" does not exists.')
        return None
    
    is_adapt = False
    position = [0, 0, 0]
    orientation = [0, 0, 0, 1]
    
    parameters = load_file(file_path)
    if 'adapt_coordinates' in parameters[0][0]:
        adapt_parameters = parameters[0][0]['adapt_coordinates']
        is_adapt = True
        target_frame_id = adapt_parameters['frame']
        if 'pose' in adapt_parameters:
            position = adapt_parameters['pose']['position']
            orientation = adapt_parameters['pose']['orientation']

    if is_adapt:
        listener = tf.TransformListener()
        # Not working in current version of tf/tf2.
        #listener.waitForTransform(source_frame_id, target_frame_id, rospy.Time(0), rospy.Duration(10.0))
        rospy.sleep(1.0)
        try:
            (translation, rotation) = listener.lookupTransform(source_frame_id, target_frame_id, rospy.Time(0))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            rospy.logerr('Could not look up TF transformation from "' +
                         source_frame_id + '" to "' + target_frame_id + '".')
            return None

        position = translation + quaternion_matrix(rotation)[:3, :3].dot(position)
        orientation = quaternion_multiply(rotation, orientation)

    return get_from_yaml(parameters, position, orientation)

def load_from_file_and_transform(file_path, position = [0, 0, 0], orientation = [0, 0, 0, 1]):
    from rosparam import load_file
    import os
    
    if not os.path.isfile(file_path):
        rospy.logerr('File with path "' + file_path + '" does not exists.')
        return None

    return get_from_yaml(load_file(file_path), position, orientation)


def get_from_yaml(yaml_object, position = [0, 0, 0], orientation = [0, 0, 0, 1]):
    goal = quadruped_msgs.msg.StepGoal()
    step_number = 0
    
    # For each step.
    for step_parameter in yaml_object[0][0]['steps']:

        step_parameter = step_parameter['step']
        # Step.
        step = quadruped_msgs.msg.Step()
        
        # Step number
        step_number = step_number + 1
        step.step_number = step_number
        
        # Swing data.
        if 'swing_data' in step_parameter:
            for swing_data_parameter in step_parameter['swing_data']:
                swing_data = quadruped_msgs.msg.SwingData()
                
                # Name.
                swing_data.name = swing_data_parameter['name']
            
                # Profile.
                if 'profile' in swing_data_parameter:
                    # Profile target.
                    target_parameter = swing_data_parameter['profile']['target']
                    swing_data.profile.target.point.x = target_parameter[0]
                    swing_data.profile.target.point.y = target_parameter[1]
                    swing_data.profile.target.point.z = target_parameter[2]
                    # Profile target frame.
                    if 'target_frame' in swing_data_parameter['profile']:
                        swing_data.profile.target.header.frame_id = swing_data_parameter['profile']['target_frame']
                    # Profile height.
                    if 'height' in swing_data_parameter['profile']:
                        swing_data.profile.height = swing_data_parameter['profile']['height']
                    # Profile duration.
                    if 'duration' in swing_data_parameter['profile']:
                        swing_data.profile.duration = rospy.Duration(swing_data_parameter['profile']['duration'])
                    # Profile type.
                    if 'type' in swing_data_parameter['profile']:
                        swing_data.profile.type = swing_data_parameter['profile']['type']
                
                # Expect touchdown.
                if 'expect_touchdown' in swing_data_parameter:
                    swing_data.expect_touchdown = swing_data_parameter['expect_touchdown']
                # Surface normal.
                if 'surface_normal' in swing_data_parameter:
                    normal_parameter = swing_data_parameter['surface_normal']
                    swing_data.surface_normal.vector.x = normal_parameter[0]
                    swing_data.surface_normal.vector.y = normal_parameter[1]
                    swing_data.surface_normal.vector.z = normal_parameter[2] 
                
                step.swing_data.append(swing_data)
    
        # Base shift data.
        if 'base_shift_data' in step_parameter:
            for base_shift_data_parameter in step_parameter['base_shift_data']:
                
                base_shift_data = quadruped_msgs.msg.BaseShiftData()
                
                # Name.
                base_shift_data.name = base_shift_data_parameter['name']
            
                # Profile.
                if 'profile' in base_shift_data_parameter:
                    # Profile target.
                    if 'target' in base_shift_data_parameter['profile']:
                        target_parameter = base_shift_data_parameter['profile']['target']
                        # Profile target position.
                        if 'position' in target_parameter:
                            base_shift_data.profile.target.pose.position.x = target_parameter['position'][0]
                            base_shift_data.profile.target.pose.position.y = target_parameter['position'][1]
                            base_shift_data.profile.target.pose.position.z = target_parameter['position'][2]
                        # Profile target position.
                        if 'orientation' in target_parameter:
                            if len(target_parameter['orientation']) == 4:
                                base_shift_data.profile.target.pose.orientation.x = target_parameter['orientation'][0]
                                base_shift_data.profile.target.pose.orientation.y = target_parameter['orientation'][1]
                                base_shift_data.profile.target.pose.orientation.z = target_parameter['orientation'][2]
                                base_shift_data.profile.target.pose.orientation.w = target_parameter['orientation'][3]
                            if len(target_parameter['orientation']) == 3:
                                rpy = target_parameter['orientation']
                                quaternion = quaternion_from_euler(rpy[0], rpy[1], rpy[2])
                                base_shift_data.profile.target.pose.orientation.x = quaternion[0]
                                base_shift_data.profile.target.pose.orientation.y = quaternion[1]
                                base_shift_data.profile.target.pose.orientation.z = quaternion[2]
                                base_shift_data.profile.target.pose.orientation.w = quaternion[3]
                    # Profile target frame.
                    if 'target_frame' in base_shift_data_parameter['profile']:
                        base_shift_data.profile.target.header.frame_id = base_shift_data_parameter['profile']['target_frame']
                    # Profile height.
                    if 'height' in base_shift_data_parameter['profile']:
                        base_shift_data.profile.height = base_shift_data_parameter['profile']['height']
                    # Profile duration.
                    if 'duration' in base_shift_data_parameter['profile']:
                        base_shift_data.profile.duration = rospy.Duration(base_shift_data_parameter['profile']['duration'])
                    # Profile type.
                    if 'type' in base_shift_data_parameter['profile']:
                        base_shift_data.profile.type = base_shift_data_parameter['profile']['type']

                step.base_shift_data.append(base_shift_data)
                
        goal.steps.append(step)
    
    # Adapt to local coordinates if desired.
    if not (numpy.array_equal(position, [0, 0, 0]) and numpy.array_equal(orientation, [0, 0, 0, 1])):
        adapt_coordinates(goal, position, orientation)
            
    return goal


def adapt_coordinates(goal, position, orientation):
    # For each steps.
    translation = translation_matrix(position)
    z_axis = [0, 0, 1]
    (roll, pitch, yaw) = euler_from_quaternion(orientation)
    rotation = rotation_matrix(yaw, z_axis)
    transform = concatenate_matrices(translation, rotation)
    
    # TODO For base shift trajectories
    # TODO For multi-dof trajectories
    for step in goal.steps:
        for swing_data in step.swing_data:
            position = swing_data.profile.target.point;
            if check_if_position_valid(position):
                position = transform_position(transform, position)
                swing_data.profile.target.point = position
        for base_shift_data in step.base_shift_data:
            pose = base_shift_data.profile.target.pose;
            if check_if_pose_valid(pose):
                pose = transform_pose(transform, pose)
                base_shift_data.profile.target.pose = pose

def transform_position(transform, position):
    transformed_point = transform.dot([position.x, position.y, position.z, 1.0])
    return geometry_msgs.msg.Point(transformed_point[0], transformed_point[1], transformed_point[2])

def transform_orientation(transform, orientation):
    q1 = quaternion_from_matrix(transform)
    q2 = [orientation.x, orientation.y, orientation.z, orientation.w]
    q = quaternion_multiply(q1, q2)
    return geometry_msgs.msg.Quaternion(q[0], q[1], q[2], q[3])

def transform_pose(transform, pose):
    pose.position = transform_position(transform, pose.position)
    pose.orientation = transform_orientation(transform, pose.orientation)
    return pose

def check_if_position_valid(position):
    if (position.x == 0 and position.y == 0 and position.z == 0):
        return False
    else:
        return True
    
def check_if_orientation_valid(orientation):
    if (orientation.x == 0 and orientation.y == 0 and orientation.z == 0 and orientation.w == 0):
        return False
    else:
        return True
    
def check_if_pose_valid(pose):
    if check_if_position_valid(pose.position) and check_if_orientation_valid(pose.orientation):
        return True
    else:
        return False
