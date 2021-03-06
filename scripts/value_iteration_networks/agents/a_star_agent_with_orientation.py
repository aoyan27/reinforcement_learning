#!/usr/bin/env python
#coding:utf-8

import numpy as np
np.set_printoptions(suppress=True, threshold=np.inf)
import copy
import math


import tf


class AstarAgent:
    def __init__(self, env):
        self.env = env

        self.cost = 1
        self.open_list = []
        self.closed_list = np.zeros([self.env.rows, self.env.cols])
        self.expand_list = np.empty([self.env.rows, self.env.cols])
        self.expand_list.fill(-1)
        
        self.heuristic = None
        self.create_heuristic()

        self.action_list = np.empty([self.env.rows, self.env.cols])
        self.action_list.fill(-1)
        self.policy = None
        self.state_list = []
        self.orientation_candidate = {}
        self.orientation_list = []
        self.shortest_action_list = []

        self.found = False
        self.resign = False
    
    #  def create_heuristic(self):
        #  self.heuristic = np.zeros([self.env.rows, self.env.cols])
        #  #  print "self.heuristic : "
        #  #  print self.heuristic
        #  self.heuristic[tuple(self.env.goal)] = 0
        #  for i in xrange(self.env.n_state):
            #  state = self.env.index2state(i)
            #  #  print "state : ", state
            #  diff_y = self.env.goal[0] - state[0]
            #  diff_x = self.env.goal[1] - state[1]
            #  #  print "diff_y, diff_x : ", diff_y, diff_x
            #  self.heuristic[tuple(state)] = diff_y + diff_x

        #  #  print "self.heuristic : "
        #  #  print self.heuristic

    def euler_to_quaternion(self, roll, pitch, yaw):
        q = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
        #  print "q : ", q, type(q)
        return q
    

    def create_heuristic(self):
        self.heuristic = np.zeros([self.env.rows, self.env.cols])
        #  print "self.heuristic : "
        #  print self.heuristic
        #  print self.env.goal
        self.heuristic[tuple(self.env.goal)] = 0
        for i in xrange(self.env.n_state):
            state = self.env.index2state(i)
            #  print "state : ", state
            diff_y = self.env.goal[0] - state[0]
            diff_x = self.env.goal[1] - state[1]
            #  print "diff_y, diff_x : ", diff_y, diff_x
            self.heuristic[tuple(state)] = diff_y**2 + diff_x**2

        #  print "self.heuristic : "
        #  print self.heuristic

    def a_star(self, start_position, start_orientation=0.0):

        g = 0
        h = self.heuristic[tuple(start_position)]
        f = g + h

        self.open_list.append([f, g, h, start_position[0], start_position[1], start_orientation])
        self.closed_list[tuple(start_position)] = 1

        found = False
        resign = False

        n = 0

        state = None
        next_state = None
        
        self.orientation_candidate[self.env.state2index(start_position)] = start_orientation

        while not found and not resign:
            #  print "========================================="
            if len(self.open_list) == 0:
                #  print "resign!!!"
                resign = True
                self.resign = resign
            else:
                #  print "self.open_list : ", self.open_list
                self.open_list.sort()
                self.open_list.reverse()
                current = self.open_list.pop()
                #  print "current : ", current
                f = current[0]
                g = current[1]
                h = current[2]

                state = [current[3], current[4]]
                #  print "state : ", state
                #  print "next_state : ", next_state
                orientation = current[5]
                #  print "orientation : ", math.degrees(orientation)

                self.expand_list[tuple(state)] = n
                n += 1

                #  print "self.env.goal : ", self.env.goal
                if state == self.env.goal:
                    found = True
                    self.found = found

                #  for a in self.env.action_list:
                #  for a in self.env.get_action_list_by_direction(state):
                for a in self.env.get_action_list_by_my_orientation(orientation):
                    #  print "-----------------------------------------------------"
                    next_state, out_of_range, collision = self.env.move(state, a)
                    next_orientation = self.env.get_next_orientation(state, orientation, a)
                    #  print "next_state : ", next_state
                    #  print "out_of_range : ", out_of_range
                    #  print "collision : ", collision
                    #  print "next_orientation : ", math.degrees(next_orientation)
                    
                    if not out_of_range:
                        if not collision and self.closed_list[tuple(next_state)] == 0:
                            #  print "next_state(ok) : ", next_state
                            #  print "next_orientation(ok) : ", math.degrees(next_orientation)
                            next_g = g + self.cost
                            next_h = self.heuristic[tuple(next_state)]
                            next_f = next_g + next_h
                            self.open_list.append([next_f, next_g, next_h, \
                                    next_state[0], next_state[1], next_orientation])
                            self.closed_list[tuple(next_state)] = 1
                            # self.action_listは、その状態に最初に訪れるときに、
                            # 直前の状態において実行した行動が格納される
                            # (self.closed_listでその状態に訪問したかをカウントされているため、
                            # その状態への２回目の訪問はないから)
                            self.action_list[tuple(next_state)] = a 
                            self.orientation_candidate[self.env.state2index(next_state)] \
                                    = next_orientation

        #  print "self.orientation_candidate : ", self.orientation_candidate

    def get_shortest_path(self, start_position, start_orientation=0.0):
        self.a_star(start_position, start_orientation=start_orientation)
        stay_action = len(self.env.action_list) - 1
        
        if self.found:
            self.policy = np.empty([self.env.rows, self.env.cols])
            self.policy.fill(stay_action)
            state = self.env.goal
            self.state_list.append(state)
            #  self.orientation_list.append(self.orientation_candidate[self.env.state2index(state)])
            q = self.euler_to_quaternion(\
                    0.0, 0.0, self.orientation_candidate[self.env.state2index(state)])
            self.orientation_list.append(q)
            self.shortest_action_list.append(self.policy[tuple(state)])
            
            while state != start_position:
                before_state, _, _ = \
                        self.env.move(state, self.action_list[tuple(state)], reflect=-1)
                #  print "before_state : ", before_state
                self.policy[tuple(before_state)] = self.action_list[tuple(state)]
                self.state_list.append(before_state)
                #  self.orientation_list.append(\
                        #  self.orientation_candidate[self.env.state2index(before_state)])
                q = self.euler_to_quaternion(\
                        0.0, 0.0, self.orientation_candidate[self.env.state2index(before_state)])
                self.orientation_list.append(q)
                self.shortest_action_list.append(self.policy[tuple(before_state)])
                state = before_state
            self.state_list.reverse()
            self.orientation_list.reverse()
            self.shortest_action_list.reverse()


    def show_path(self):
        n_local_state = self.env.grid.shape[0] * self.env.grid.shape[1]
        vis_path = np.array(['-']*n_local_state).reshape(self.env.grid.shape)
        index = np.where(self.env.grid == -1)
        vis_path[index] = '#'
        state_list = np.asarray(self.state_list)
        for i in xrange(len(state_list)):
            vis_path[tuple(state_list[i])] = '@'
            if tuple(state_list[i])==tuple(self.env.goal):
                vis_path[tuple(self.env.goal)] = 'G'

        vis_path[tuple(state_list[0])] = '$'
        #  if len(state_list[state_list==self.env.goal]) == 2:
            #  vis_path[tuple(self.env.goal)] = 'G'

        path_data = {}
        path_data['vis_path'] = vis_path
        path_data['state_list'] = state_list
        path_data['action_list'] = self.shortest_action_list
        
        return path_data

    def view_path(self, path):
        grid = copy.deepcopy(path)
        for row in grid:
            print "|",
            for i in row:
                print "%2c" % i,
            print "|"



if __name__ == "__main__":
    import sys
    sys.path.append('../')
    #  from envs.object_world import Objectworld
    from envs.object_world_with_orientation import Objectworld
    rows = cols = 5
    goal = [rows-1, cols-1]

    R_max = 1.0
    noise = 0.0
    n_objects = 5
    seed = 0
    
    object_list = [
                (0, 1), (1, 1), (2, 1), (3, 1)
            ]

    #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, object_list=object_list, random_objects=False, mode=0)
    #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, object_list=object_list, random_objects=False, mode=1)
    env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, mode=1)

    #  print "env.grid : "
    #  env.show_objectworld()

    i = 0

    #  a_agent = AstarAgent(env)

    #  start_position = [0, 0]
    #  a_agent.a_star(start_position)
    while i < 10:
        print "i : ", i
        #  env.reset(start_position=[3, 1], start_orientation=-0.75*math.pi)
        env.reset(random=True)
        env.set_objects()
        print "env.grid : "
        env.show_objectworld_with_state()
        print "env.state_ : ", env.state_
        env.set_orientation_random(orientation_list=[-180, -135, -90, -45, 0, 45, 90, 135, 180])
        print "env.orientation : ", env.orientation_
        print "env.orientation(deg) : ", math.degrees(env.orientation_)
        print "env.goal : ", env.goal

        print "=================================================="

        a_agent = AstarAgent(env)
        start_position = env.state_
        

        start_orientation = env.orientation_
        #  a_agent.a_star(start_position)
        a_agent.get_shortest_path(start_position, start_orientation=start_orientation)
        #  print "a_agent.expand_list : "
        #  print a_agent.expand_list
        #  print "a_agent.action_list : "
        #  print a_agent.action_list
        
        if a_agent.found:
            print "a_agent.state_list : "
            print a_agent.state_list
            print "a_agent.orientation_list : "
            print a_agent.orientation_list
            print "a_agent.shrotest_action_list : "
            print a_agent.shortest_action_list
            #  env.show_policy(a_agent.policy.transpose().reshape(-1))
            path_data = a_agent.show_path()
            print "view_path : "
            a_agent.view_path(path_data['vis_path'])
            #  print "state_list : ", list(path_data['state_list'])
            #  print "action_list : ", path_data['action_list']
            i += 1
