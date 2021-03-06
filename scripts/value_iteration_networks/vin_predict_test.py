#!/usr/bin/env python
#coding:utf-8

import argparse

import numpy as np
np.set_printoptions(suppress=True, threshold=np.inf)
import matplotlib.pyplot
import cv2 as cv
import matplotlib.pyplot as plt
from progressbar import ProgressBar

import chainer 
from chainer import cuda, Variable, optimizers, serializers
from chainer import Chain
import chainer.functions as F
import chainer.links as L

import copy
import pickle
import time

from networks.vin import ValueIterationNetwork
from envs.object_world import Objectworld


def grid2image(array):
    image = copy.deepcopy(array)

    index = np.where(image == 1)
    for i in xrange(len(index[0])):
        image[index[0][i], index[1][i]] = 0

    index = np.where(image == -1)
    for i in xrange(len(index[0])):
        image[index[0][i], index[1][i]] = 1
    #  print image
    return image

def view_image(array, title):
    image = cv.cvtColor(array.astype(np.uint8), cv.COLOR_GRAY2RGB)
    #  print image
    plt.imshow(255 - 255*image, interpolation="nearest")
    plt.title(title)
    plt.show()

def load_dataset(path):
    with open(path, mode='rb') as f:
        data = None
        data = pickle.load(f)
    image_data = data['image']
    reward_map_data = data['reward']
    state_list_data = data['state']
    action_list_data = data['action']
    print "Load %d data!!!" % len(image_data)
    return image_data, reward_map_data, state_list_data, action_list_data

def cvt_input_data(image, reward_map):
    input_data = \
            np.concatenate((np.expand_dims(image, 0), np.expand_dims(reward_map, 0)), axis=0)
    #  print input_data.shape
    input_data = np.expand_dims(input_data, 0)
    return input_data

def load_model(model, filename):
    print "Load {}!!".format(filename)
    serializers.load_npz(filename, model)

def create_input_data(image, reward_map):
    input_data = \
            np.concatenate((np.expand_dims(image, 0), np.expand_dims(reward_map, 0)), axis=0)
    #  print input_data.shape
    input_data = np.expand_dims(input_data, 0)
    #  print "input_data.shape : ", input_data.shape
    return input_data

def create_map_data(env, start, goal):
    #  print "start : ", start
    #  print "goal : ", goal
    env.set_start(start)
    env.set_goal(goal)

    env.set_objects()
    #  print "env.grid : "
    #  env.show_objectworld()
    image = grid2image(env.grid)
    #  print "image : "
    #  print image
    #  view_image(image, 'Gridworld')
    reward_map = get_reward_map(env)
    return image, reward_map

def get_reward_map(env):
    reward_map = np.zeros([env.rows, env.cols])
    reward_map[tuple(env.goal)] = env.R_max
    return reward_map

def set_start_and_goal(env):
    goal = [np.random.randint(1, env.rows-1), np.random.randint(1, env.cols-1)]

    while 1:
        start = [np.random.randint(1, env.rows-1), np.random.randint(1, env.cols-1)]
        if start != goal and env.grid[tuple(start)] != -1:
            break

    #  print "start : ",  start
    #  print "goal : ", goal
    return start, goal

def view_traj(env, state_list):
    vis_traj = np.array(['-']*env.n_state).reshape(env.grid.shape)
    object_index = np.where(env.grid==-1)
    vis_traj[object_index] = "#"
    
    #  print "state_list : ", state_list
    for i in xrange(len(state_list)):
        vis_traj[tuple(state_list[i])] = '*'

    vis_traj[tuple(state_list[0])] = '$'
    end_index = len(state_list) - 1
    vis_traj[tuple(state_list[end_index])] = 'G'
    
    print "vis_tarj : "
    print vis_traj

def view_obs_world(array):
    for row in array:
        print "|",
        for i in row:
            print "%.0f" % i,
        print "|"

    



def main(rows, cols, n_objects, seed, gpu, model_path):
    model = ValueIterationNetwork(l_q=9, n_out=9, k=20)
    #  model = ValueIterationNetwork(l_h=200, l_q=9, n_out=9, k=20)
    load_model(model, model_path)
    if gpu >= 0:
        cuda.get_device(gpu).use()
        model.to_gpu()

    dataset = "datasets/map_dataset.pkl"
    image_data, reward_map_data, state_list_data, action_list_data = load_dataset(dataset)
    input_data = None
    count = 0
    for i in xrange(len(image_data)):
        print "i : ", i
        input_data = cvt_input_data(image_data[i], reward_map_data[i])
        #  view_obs_world(input_data[0][0])
        #  print "----------------------------"
        #  view_obs_world(input_data[0][1])
        #  print "input_data : "
        #  print input_data
        #  print "state_list_data : ", state_list_data[i]
        #  print "action_list_data : ", action_list_data[i]

        #  loss, acc = model.forward(input_data, np.expand_dims(state_list_data[i], 0), np.expand_dims(action_list_data[i], 0))
        p = model(input_data, np.expand_dims(state_list_data[i], 0))
        print "p : ", p
        print "argmax : ", np.argmax(p.data)

        print "action : ", np.expand_dims(action_list_data[i], 0)

        if np.argmax(p.data) == action_list_data[i]:
            count+=1
            print "correct!!"
    print "acc : ", float(count)/float(len(image_data))

    
    #  n_state = rows * cols
    #  goal = [rows-1, cols-1]
    #  R_max = 1.0
    #  noise = 0.0

    #  #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, mode=0)
    #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, mode=1)
    
    #  # start, goal = set_start_and_goal(env)
    #  # print "start : ", start
    #  # print "goal : ", goal
    #  # image, reward_map = create_map_data(env, start, goal)
    #  # input_data = create_input_data(image, reward_map)
    #  #  print "input_data : "
    #  #  print input_data
    #  # print "input_data.shape : ", input_data.shape
    #  # state_data = np.expand_dims(np.asarray(start), 0)
    #  # print "state_data : ", state_data
    #  # print "state_data.shape : ", state_data.shape
    #  # if gpu >= 0:
    #  #     input_data = cuda.to_gpu(input_data)
    #  #
    #  # print "env.grid : "
    #  # env.show_objectworld()

    #  success_times = 0
    #  failed_times = 0
    
    #  max_episode = 100
    #  max_step = rows + cols
    #  prog = ProgressBar(0, max_episode)
    
    
    #  for i_episode in xrange(max_episode):
        #  state_list = []
        #  prog.update(i_episode)
        #  print "=============================="
        #  print "episode : ", i_episode
        #  start, goal = set_start_and_goal(env)
        #  state_data = np.expand_dims(np.asarray(start), 0)
        #  state_data[0] = start
        
        #  state_list.append(start)
        #  #  print "state_list : ", state_list

        #  env.set_goal(goal)

        #  image, reward_map = create_map_data(env, start, goal)
        #  #  env.grid = np.zeros((rows, cols), dtype=np.float32)
        #  #  image = env.grid
        #  input_data = create_input_data(image, reward_map)

        #  #  env.show_objectworld()

        #  if gpu >= 0:
            #  input_data = cuda.to_gpu(input_data)
        #  #  print "start : ", start
        #  env.reset(start)
        #  for i_step in xrange(max_step):
            #  #  print "-----------------------------------"
            #  #  print "step : ", i_step
            #  #  print "state : ", state_data, ", goal : ", goal
            #  #  env.show_objectworld_with_state()
            #  p = model(input_data, state_data)
            #  print "p : ", p
            #  action = np.argmax(p.data)
            #  #  print "action : ",action
            #  next_state, reward, done, _ = env.step(action, reward_map.transpose().reshape(-1))
            #  #  print "next_state : ", next_state
            #  #  print "reward : ", reward
            #  #  print "done : ", done, " (collisions : ", env.collisions_[action], ")"

            #  state_data[0] = next_state

            #  state_list.append(next_state)
            #  #  print "state_list : ", state_list

            #  if done:
                #  if reward == R_max:
                    #  success_times += 1
                #  break
        #  if reward != R_max:
            #  failed_times += 1
        #  view_traj(env, state_list)
    
    #  print "success_times : ", success_times
    #  print "failed_times : ", failed_times




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This script is predict vin ...')
    
    parser.add_argument('-r', '--rows', default=16, type=int, help='row of global gridworld')
    parser.add_argument('-c', '--cols', default=16, type=int, help='column of global gridworld')

    parser.add_argument('-o', '--n_objects', default=40, type=int, help='number of objects')
    parser.add_argument('-s', '--seed', default=0, type=int, help='number of random seed')
    parser.add_argument('-g', '--gpu', default=-1, type=int, help='number of gpu device')

    parser.add_argument('-m', '--model_path', default='models/vin_model_1.model', type=str, help="load model path")

    args = parser.parse_args()
    print args
    
    main(args.rows, args.cols, args.n_objects, args.seed, args.gpu, args.model_path)

