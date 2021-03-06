#!/usr/bin/env python
#coding:utf-8

import argparse

import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from progressbar import ProgressBar

import copy
import pickle
import time

import tf

#  from envs.multi_agent_grid_world import Gridworld
#  from envs.multi_agent_object_world import Objectworld
#  from envs.multi_agent_object_world_with_orientation import Objectworld
from envs.multi_agent_object_world_with_orientation_velocity import Objectworld
#  from agents.a_star_agent import AstarAgent
from agents.a_star_agent_with_orientation import AstarAgent


def grid2image(array):
    #  print "array : "
    #  print array
    image = copy.deepcopy(array)

    index = np.where(image == 1)
    for i in xrange(len(index[0])):
        image[index[0][i], index[1][i]] = 0

    index = np.where(image == -1)
    for i in xrange(len(index[0])):
        image[index[0][i], index[1][i]] = 1
    #  print "image : "
    #  print image

    return image

def euler2quaternion(roll, pitch, yaw):
    q = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
    return q

def quaternion2euler(q):
    e = tf.transformations.euler_from_quaternion(q)
    return e

def create_input_image_and_relative_orientation_velocity\
        (env, state_list, orientation_list, action_list, n_agents, n_trajs):
    #  print "state_list : ", state_list
    #  print "orientation_list : ", orientation_list
    #  print "action_list : ", action_list
    domain_grid_list = {}
    domain_agent_grid_list = {}
    domain_another_agent_position_with_grid_list = {}

    
    domain_relative_orientation_list = {}
    domain_relative_velocity_vector_list = {}
    for agent_id in xrange(n_agents):
        domain_grid_list[agent_id] = []
        domain_agent_grid_list[agent_id] = []
        domain_another_agent_position_with_grid_list[agent_id] = []

        domain_relative_orientation_list[agent_id] = []
        domain_relative_velocity_vector_list[agent_id] = []


    start_position = {}
    goal_position = {}
    start_orientation = {}
    action = {}
    for i_traj in xrange(n_trajs):
        #  print "++++++++++++++++++++++++++++++++++++++++++++++++++"
        #  print "i_traj : ", i_traj
        traj_grid_list = {}
        traj_agent_grid_list = {}
        traj_another_agent_position_with_grid_list = {}

        traj_relative_orientation_list = {}
        traj_relative_velocity_vector_list = {}
        for agent_id in xrange(n_agents):
            traj_grid_list[agent_id] = []
            traj_agent_grid_list[agent_id] = []
            traj_another_agent_position_with_grid_list[agent_id] = []

            traj_relative_orientation_list[agent_id] = []
            traj_relative_velocity_vector_list[agent_id] = []


        max_step = len(state_list[0][i_traj])
        #  print "max_step : ", max_step
        for agent_id in xrange(n_agents):
            start_position[agent_id] = state_list[agent_id][i_traj][0]
            goal_position[agent_id] = state_list[agent_id][i_traj][max_step-1]
            start_orientation[agent_id] = \
                    quaternion2euler(orientation_list[agent_id][i_traj][0])[2]
        #  print "start_position : ", start_position
        #  print "goal_position : ", goal_position
        observation = env.reset(start_position=start_position, \
                goal_position=goal_position, start_orientation=start_orientation)
        #  print "env._state : ", env._state
        #  print "env.grid : "
        #  print env.grid
        #  for agent_id in xrange(n_agents):
            #  print "env.agent_grid[", agent_id, "] : "
            #  print env.agent_grid[agent_id]
        #  for agent_id in xrange(n_agents):
            #  print "env.another_agent_position_with_grid[", agent_id, "] : "
            #  print env.another_agent_position_with_grid[agent_id]
        for i_step in xrange(max_step):
            #  print "-----------------------------"
            #  print "step : ", i_step
            #  print "env.goal : ", env.goal
            #  print "state : ", observation
            #  print "env._orientation : ", env._orientation
            #  print "env._orientation(quat) : ", euler2quaternion(0,0,env._orientation[0])
            #  env.show_objectworld_with_state()
            #  print "env.grid : "
            #  print env.grid
            #  for agent_id in xrange(n_agents):
                #  print "env.agent_grid[", agent_id, "] : "
                #  print env.agent_grid[agent_id]
            #  for agent_id in xrange(n_agents):
                #  print "env.another_agent_position_with_grid[", agent_id, "] : "
                #  print env.another_agent_position_with_grid[agent_id]
            for agent_id in xrange(n_agents):
                traj_grid_list[agent_id].append(grid2image(env.grid))
                traj_agent_grid_list[agent_id].append(grid2image(env.agent_grid[agent_id]))
                traj_another_agent_position_with_grid_list[agent_id].append(\
                        grid2image(env.another_agent_position_with_grid[agent_id]))

                traj_relative_orientation_list[agent_id].append(\
                        euler2quaternion(0.0, 0.0, env.relative_orientation[agent_id]))

            #  print "env.relative_orientation : ", env.relative_orientation

            for agent_id in xrange(n_agents):
                action[agent_id] = int(action_list[agent_id][i_traj][i_step])
            #  print "action : ", action
            env.get_relative_velocity_vector(action)
            for agent_id in xrange(n_agents):
                traj_relative_velocity_vector_list[agent_id].append(\
                        env.relative_velocity_vector[agent_id])
            #  print "env.relative_velocity_vector : ", env.relative_velocity_vector
            observation, reward, episode_end, info = env.step(action)
            #  print "env.relative_orientation_ : ", env.relative_orientation
            #  print "next_state : ", observation
            #  print "reward : ", reward
            #  print "episode_end : ", episode_end
        #  print "traj_grid_list[0] : "
        #  print traj_grid_list[0]
        for agent_id in xrange(n_agents):
            domain_grid_list[agent_id].append(traj_grid_list[agent_id])
            domain_agent_grid_list[agent_id].append(traj_agent_grid_list[agent_id])
            domain_another_agent_position_with_grid_list[agent_id].append(\
                    traj_another_agent_position_with_grid_list[agent_id])

            domain_relative_orientation_list[agent_id].append(\
                    traj_relative_orientation_list[agent_id])
            domain_relative_velocity_vector_list[agent_id].append(\
                    traj_relative_velocity_vector_list[agent_id])

    #  print "domain_grid_list[0] : "
    #  print domain_grid_list[0]
    #  print len(domain_grid_list[0])
    #  print "domain_relative_orientaiton_list[0] : "
    #  print domain_relative_orientation_list[0]
    #  print "domain_relative_velocity_vector_list[0] : "
    #  print domain_relative_velocity_vector_list[0]

    grid_list = []
    agent_grid_list = []
    another_agent_position_with_grid_list = []

    relative_orientation_list = []
    relative_velocity_vector_list = []

    for agent_id in xrange(n_agents):
        grid_list.append(domain_grid_list[agent_id])
        agent_grid_list.append(domain_agent_grid_list[agent_id])
        another_agent_position_with_grid_list.append(\
                domain_another_agent_position_with_grid_list[agent_id])

        relative_orientation_list.append(domain_relative_orientation_list[agent_id])
        relative_velocity_vector_list.append(domain_relative_velocity_vector_list[agent_id])

    #  print "grid_list : "
    #  print grid_list
    #  print len(grid_list)
    #  print "agent_grid_list : "
    #  print len(agent_grid_list)
    #  print "another_agent_position_with_grid_list : "
    #  print len(another_agent_position_with_grid_list[0][0])
    #  print another_agent_position_with_grid_list[0][0]
    #  print "relative_orientation_list : "
    #  print relative_orientation_list
    
    return grid_list, agent_grid_list, another_agent_position_with_grid_list, \
            relative_orientation_list, relative_velocity_vector_list
    

def view_image(array, title):
    image = cv.cvtColor(array.astype(np.uint8), cv.COLOR_GRAY2RGB)
    #  print image
    plt.imshow(255 - 255*image, interpolation="nearest")
    plt.title(title)
    plt.show()

def get_reward_map(env, n_agents):
    reward_map = np.zeros((n_agents, env.rows, env.cols))
    for i in xrange(n_agents):
        reward_map[i, env.goal[i][0], env.goal[i][1]] = env.R_max
    #  print "reward_map : "
    #  print reward_map
    return reward_map

def get_agent_state_and_action(env, agent_id):
    #  print "************************************************"
    #  print "agent_id : ", agent_id
    a_agent = AstarAgent(env, agent_id)
    #  print "env.agent_grid[agent_id] : "
    #  print env.agent_grid[agent_id]
    #  print "env._state[agent_id] : ", env._state[agent_id]
    #  a_agent.get_shortest_path(env._state[agent_id], env.grid)
    a_agent.get_shortest_path(env._state[agent_id], \
            env._orientation[agent_id], env.agent_grid[agent_id])
    #  print "a_agent.found : ", a_agent.found
    if a_agent.found:
        #  pass
        #  print "a_agent.state_list : "
        #  print a_agent.state_list
        #  print "a_agent.orientation_list : "
        #  print a_agent.orientation_list
        #  print "a_agent.shrotest_action_list : "
        #  print a_agent.shortest_action_list
        #  env.show_policy(a_agent.policy.transpose().reshape(-1))
        path_data = a_agent.show_path()
        #  print "agent_id : ", agent_id
        #  print "view_path_my : "
        #  a_agent.view_path(path_data['vis_path'])
    #  print "a_agent.shortest_action_list[0] : "
    #  print a_agent.shortest_action_list[0]
    state_list = a_agent.state_list
    orientation_list = a_agent.orientation_list
    action_list = a_agent.shortest_action_list
    #  print "state_list_ : ", state_list
    #  print "orientation_lsit_ : ", orientation_list
    #  print "action_list_ : ", action_list

    return state_list, orientation_list, action_list, a_agent.found

def map_all(es):
    return all([e == es[0] for e in es[1:]]) if es else False

def get_trajs(env, n_agents, n_trajs):

    traj_state_list = {}
    traj_orientation_list = {}
    traj_action_list = {}
    for agent_id in xrange(n_agents):
        traj_state_list[agent_id] = []
        traj_orientation_list[agent_id] = []
        traj_action_list[agent_id] = []

    failed = False

    j = 0
    challenge_times = 0
    found = [False for i in xrange(n_agents)]
    for agent_id in xrange(n_agents):
        found[agent_id] = False
    while j < n_trajs:
        #  print "-----------------------------------------------"
        #  print "j : ", j
        #  print "challenge_times : ", challenge_times
        challenge_times += 1
        if challenge_times > 50:
            failed = True
            break


        env.set_start_random(check_goal=True)
        #  print "env.start_ : ", env.start
        #  print "env.goal_ : ", env.goal
        #  print "env.grid : "
        #  print env.grid
        #  env.show_objectworld_with_state()

        domain_state_list = {}
        domain_orientation_list = {}
        domain_action_list = {}
        step_count_list = []
        for agent_id in xrange(n_agents):
            #  print "agent_id : ", agent_id
            #  env.show_objectworld_with_state()
            domain_state_list[agent_id], domain_orientation_list[agent_id], \
                    domain_action_list[agent_id], found[agent_id] \
                    = get_agent_state_and_action(env, agent_id)
            #  print "found : ", found
            step_count_list.append(len(domain_state_list[agent_id]))
        #  print "all(found) : ", all(found)
        if not all(found):
            #  print "continue!!!!!!!!"
            continue

        #  print "step_count_list : ", step_count_list 
        max_step_count = max(step_count_list)
        #  print "max_step_count : ", max_step_count

        for agent_id in xrange(n_agents):
            diff_step = max_step_count - step_count_list[agent_id]
            for i_step in xrange(diff_step):
                domain_state_list[agent_id].append(\
                        domain_state_list[agent_id][step_count_list[agent_id]-1])
                domain_orientation_list[agent_id].append(\
                        domain_orientation_list[agent_id][step_count_list[agent_id]-1])
                domain_action_list[agent_id].append(\
                        domain_action_list[agent_id][step_count_list[agent_id]-1])

        
        for agent_id in xrange(n_agents):
            traj_state_list[agent_id].append(domain_state_list[agent_id])
            traj_orientation_list[agent_id].append(domain_orientation_list[agent_id])
            traj_action_list[agent_id].append(domain_action_list[agent_id])
        #  print "traj_state_list : "
        #  print traj_state_list
        #  print "traj_orientation_list : "
        #  print traj_orientation_list
        #  print "traj_action_list : "
        #  print traj_action_list

        j += 1
        challenge_times = 0

    state_list = []
    orientation_list = []
    action_list = []

    for agent_id in xrange(n_agents):
        state_list.append(traj_state_list[agent_id])
        orientation_list.append(traj_orientation_list[agent_id])
        action_list.append(traj_action_list[agent_id])
        
    #  print "state_list : "
    #  print state_list
    #  print "orientation_list : "
    #  print orientation_list
    #  print "action_list : "
    #  print action_list

    if failed:
        del state_list[:]
        del orientation_list[:]
        del action_list[:]
        return state_list, orientation_list, action_list

    return state_list, orientation_list, action_list


def save_dataset(data, filename):
    print "Save %d-%d multi_agent_map_dataset.pkl!!!!!" \
			% (len(data['grid_image'][0]), len(data['grid_image'][1]))
    with open(filename, mode='wb') as f:
        pickle.dump(data, f)


def main(rows, cols, n_objects, n_agents, n_domains, n_trajs, seed, save_dirs):
    n_state = rows * cols
    
    goal = [rows-1, cols-1]
    R_max = 1.0
    noise = 0.0
    mode = 1

    env = Objectworld(rows, cols, n_objects, n_agents, noise, seed=seed, mode=mode)
    #  print env.grid

    #  print "env.n_state : ", env.n_state
    #  print "env.n_action : ", env.n_action

    #  print "env._state : ", env._state
    #  print "env.goal : ", env.goal
    
    #  start = {0: [0, 0], 1: [rows-1, 0]}
    #  goal = {0: [rows-1, cols-1], 1:[0, cols-1]}
    #  env.set_start(start)
    #  env.set_goal(goal)
    
    max_samples = (rows + cols) * n_domains * n_trajs
    print "max_samples : ", max_samples

    grid_image_data = np.zeros((n_agents, max_samples, rows, cols))
    agent_grid_image_data = np.zeros((n_agents, max_samples, rows, cols))
    another_agent_position_with_grid_image_data = np.zeros((n_agents, max_samples, rows, cols))
    reward_map_data = np.zeros((n_agents, max_samples, rows, cols))
    state_list_data = np.zeros((n_agents, max_samples, 2))
    action_list_data = np.zeros((n_agents, max_samples))
    orientation_list_data = np.zeros((n_agents, max_samples, 4))

    relative_orientation_list_data = np.zeros((n_agents, max_samples, 4))
    relative_velocity_vector_list_data = np.zeros((n_agents, max_samples, 2))
    #  print "image_data : ", image_data.shape
    #  print "reward_map_data : ", reward_map_data.shape
    #  print "state_list_data : ", state_list_data.shape
    #  print "action_list_data : ", action_list_data.shape

    prog = ProgressBar(0, n_domains)

    dom = 0

    num_sample = [0 for i in xrange(n_agents)]
    while dom < n_domains:
        #  print "===================================================="
        #  print "dom : ", dom
        env.set_goal_random(check_start=False)
        env.set_objects()
        #  print "env._state : ", env._state
        #  print "env.goal : ", env.goal
        #  print "env.grid_ : "
        #  print env.grid

        state_list, orientation_list, action_list = get_trajs(env, n_agents, n_trajs)

        if len(state_list) == 0:
            continue

        reward_map_list = get_reward_map(env, n_agents)
        #  print "reward_map_list : "
        #  print reward_map_list

        grid_image_list, agent_grid_image_list, another_agent_position_with_grid_image_list, \
                relative_orientation_list, relative_velocity_vector_list = \
                create_input_image_and_relative_orientation_velocity\
                (env, state_list, orientation_list, action_list, n_agents, n_trajs)
        #  for k in xrange(len(another_agent_position_with_grid_image_list[0][0])):
            #  view_image(agent_grid_image_list[0][0][k], 'Gridworld')


        ns = 0
        count = 0
        for j in xrange(n_agents):
            #  print "num_sample[j] : ", num_sample[j]
            #  print "j : ", j
            #  print "len(state_list) : ", len(state_list)
            
            for i in xrange(n_trajs):
                #  print "i : ", i
                ns = len(state_list[j][i])
                #  print "ns : ", ns
                grid_image_data[j][num_sample[j]:num_sample[j]+ns] = grid_image_list[j][i][:]
                agent_grid_image_data[j][num_sample[j]:num_sample[j]+ns] \
                        = agent_grid_image_list[j][i][:]
                another_agent_position_with_grid_image_data[j][num_sample[j]:num_sample[j]+ns] \
                        = another_agent_position_with_grid_image_list[j][i][:]
                reward_map_data[j][num_sample[j]:num_sample[j]+ns] = reward_map_list[j]
                #  print "state_list : "
                #  print state_list[j][i][:]
                state_list_data[j][num_sample[j]:num_sample[j]+ns] = state_list[j][i][:]
                orientation_list_data[j][num_sample[j]:num_sample[j]+ns] \
                        = orientation_list[j][i][:]
                action_list_data[j][num_sample[j]:num_sample[j]+ns] = action_list[j][i][:]

                relative_orientation_list_data[j][num_sample[j]:num_sample[j]+ns] = \
                        relative_orientation_list[j][i][:]
                relative_velocity_vector_list_data[j][num_sample[j]:num_sample[j]+ns] = \
                        relative_velocity_vector_list[j][i][:]

                num_sample[j] += ns
                count += ns
        
        #  print max_samples
        #  print num_sample
        #  print "grid_image_data : "
        #  print grid_image_data[0][0:num_sample[0]]
        #  print "agent_grid_image_data : "
        #  print agent_grid_image_data[0][0:num_sample[0]]
        #  print "another_agent_position_with_grid_image_data : "
        #  print another_agent_position_with_grid_image_data[0][0:num_sample[0]]
        #  print "reward_map_data : "
        #  print reward_map_data[0][0:num_sample[0]]
        #  print state_list_data[0][0:num_sample[0]]
        #  print action_list_data[0]
        #  print "relative_orientation_list_data : "
        #  print relative_orientation_list_data[0][0:num_sample[0]]
        #  print len(relative_orientation_list_data[0])
        #  print "relative_velocity_vector_list_data : "
        #  print relative_velocity_vector_list_data[0][0:num_sample[0]]
        #  print max_samples
        #  print num_sample

        prog.update(dom)
        dom += 1

    
    data = {'grid_image': [], 'agent_grid_image': [], \
            'another_agent_position': [], 'reward': [], \
            'state': [], 'orientation': [], 'action': [], \
            'relative_orientation': [], 'relative_velocity_vector': []}
    for i in xrange(n_agents):
        data['grid_image'].append(grid_image_data[i][0:num_sample[i]])
        data['agent_grid_image'].append(agent_grid_image_data[i][0:num_sample[i]])
        data['another_agent_position'].append(\
                another_agent_position_with_grid_image_data[i][0:num_sample[i]])
        data['reward'].append(reward_map_data[i][0:num_sample[i]])
        data['state'].append(state_list_data[i][0:num_sample[i]])
        data['orientation'].append(orientation_list_data[i][0:num_sample[i]])
        data['action'].append(action_list_data[i][0:num_sample[i]])

        data['relative_orientation'].append(relative_orientation_list_data[i][0:num_sample[i]])
        data['relative_velocity_vector'].append(relative_velocity_vector_list_data[i][0:num_sample[i]])

    #  print len(data['grid_image'][1])
    #  print "data : "
    #  print data['grid_image']
    #  print data['agent_grid_image']
    #  print data['another_agent_position']
    #  print data['reward']
    #  print data['state']
    #  print data['action']
    #  print data['relative_orientation']
    #  print data['relative_velocity_vector']
    
    dataset_name ='multi_agent_object_world_with_orientation_velocity_map_dataset.pkl'
    save_dataset(data, save_dirs+dataset_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This script is make_dataset_multi_agent ...')
    
    parser.add_argument('-r', '--rows', default=9, type=int, help='row of global gridworld')
    parser.add_argument('-c', '--cols', default=9, type=int, help='column of global gridworld')

    parser.add_argument('-o', '--n_objects', default=10, type=int, help='number of objects')
    parser.add_argument('-a', '--n_agents', default=2, type=int, help='number of agents')
    
    parser.add_argument('-d', '--n_domains', default=5000, type=int, help='number of domains')
    parser.add_argument('-t', '--n_trajs', default=10, type=int, help='number of trajs')
    

    parser.add_argument('-s', '--seed', default=0, type=int, help='number of seed')

    parser.add_argument('-m', '--dataset_dirs', default='datasets/', \
            type=str, help="save dataset directory")

    args = parser.parse_args()
    print args

    main(args.rows, args.cols, args.n_objects, args.n_agents, args.n_domains, \
            args.n_trajs, args.seed, args.dataset_dirs)
    
