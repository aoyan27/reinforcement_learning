#!/usr/bin/env python
#coding:utf-8

import numpy as np
np.set_printoptions(suppress=True, threshold=np.inf)
import copy
import math


class AstarAgent:
    def __init__(self, env, agent_id=1):
        self.env = env

        self.agent_id = agent_id

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
        self.shortest_action_list = []

        self.found = False
        self.resign = False

        self.f_list = []
    
    def create_heuristic(self):
        self.heuristic = np.zeros([self.env.rows, self.env.cols])
        #  print "self.heuristic : "
        #  print self.heuristic
        #  print "self.env.goal[self.agent_id] : "
        #  print self.agent_id
        #  print self.env.goal[self.agent_id]
        self.heuristic[tuple(self.env.goal[self.agent_id])] = 0
        for i in xrange(self.env.n_state):
            state = self.env.index2state(i)
            #  print "state : ", state
            diff_y = math.fabs(self.env.goal[self.agent_id][0] - state[0])
            diff_x = math.fabs(self.env.goal[self.agent_id][1] - state[1])
            #  print "diff_y, diff_x : ", diff_y, diff_x
            self.heuristic[tuple(state)] = diff_y + diff_x

        #  print "self.heuristic : "
        #  print self.heuristic

    def a_star(self, start_position, grid):

        g = 0
        h = self.heuristic[tuple(start_position)]
        f = g + h

        self.open_list.append([f, g, h, start_position[0], start_position[1]])
        self.closed_list[tuple(start_position)] = 1

        self.f_list.append([f])

        found = False
        resign = False

        n = 0
        
        while not found and not resign:
            if len(self.open_list) == 0:
                #  print "resign!!!"
                resign = True
                self.resign = resign
            else:
                #  print "self.open_list : ", self.open_list
                #  print "self.f_list : ", self.f_list
                self.open_list.sort()
                self.f_list.sort()
                #  print "self.open_list(sort) : ", self.open_list
                #  print "self.f_list(sort) : ", self.f_list

                min_f_value = self.f_list[0][0]
                #  print "min_f_value : ", min_f_value

                self.open_list.reverse()
                self.f_list.reverse()
                #  print "self.open_list(reverse) : ", self.open_list
                #  print "self.f_list(reverse) : ", self.f_list

                min_index = np.where(self.f_list == min_f_value)
                #  print "min_index : ", min_index
                #  print "len(min_index[0]) : ", len(min_index[0])
                pick_up_index = len(self.f_list)-1
                if len(min_index[0]) !=  1:
                    pick_up_index = np.random.choice(min_index[0])
                    #  print "pick_up_index : ", pick_up_index

                current = self.open_list[pick_up_index]
                del self.open_list[pick_up_index]
                current_f = self.f_list[pick_up_index]
                del self.f_list[pick_up_index]
                #  print "current : ", current
                f = current[0]
                g = current[1]
                h = current[2]
                

                state = [current[3], current[4]]
                #  print "state : ", state

                self.expand_list[tuple(state)] = n
                n += 1
            
                #  print "self.env.goal[self.agent_id] : ", self.env.goal[self.agent_id]
                if state == self.env.goal[self.agent_id]:
                    found = True
                    self.found = found

                for a in xrange(len(self.env.action_list)):
                    #  print "state : ", state
                    #  print "a : ", a
                    next_state, out_of_range, collision = \
                            self.env.move(state, a, grid=grid)
                    #  print "next_state : ", next_state
                    #  print "out_of_range : ", out_of_range
                    #  print "collision : ", collision
                    
                    if not out_of_range:
                        if not collision and self.closed_list[tuple(next_state)] == 0:
                            #  print "next_state(ok) : ", next_state
                            next_g = g + self.cost
                            next_h = self.heuristic[tuple(next_state)]
                            next_f = next_g + next_h
                            self.open_list.append\
                                    ([next_f, next_g, next_h, next_state[0], next_state[1]])
                            self.f_list.append([next_f])
                            self.closed_list[tuple(next_state)] = 1
                            # self.action_listは、その状態に最初に訪れるときに、
                            # 直前の状態において実行した行動が格納される
                            # (self.closed_listでその状態に訪問したかをカウントされているため、
                            # その状態への２回目の訪問はないから)
                            self.action_list[tuple(next_state)] = a 
        #  print "self.action_list : "
        #  print self.action_list
        #  print "self.expand_list : "
        #  print self.expand_list

    def get_shortest_path(self, start_position, grid):
        self.a_star(start_position, grid)
        stay_action = len(self.env.action_list) - 1
        #  print "self.found : ", self.found
        
        if self.found:
            self.policy = np.empty([self.env.rows, self.env.cols])
            self.policy.fill(stay_action)
            state = self.env.goal[self.agent_id]
            #  print "state : ", state
            self.state_list.append(state)
            self.shortest_action_list.append(self.policy[tuple(state)])
            
            while state != start_position:
                before_state, _, _ = \
                        self.env.move(state, self.action_list[tuple(state)], \
                        grid=grid, reflect=-1)
                #  print "before_state : ", before_state
                self.policy[tuple(before_state)] = self.action_list[tuple(state)]
                self.state_list.append(before_state)
                self.shortest_action_list.append(self.policy[tuple(before_state)])
                state = before_state
            self.state_list.reverse()
            self.shortest_action_list.reverse()
        else:
            self.shortest_action_list.append(stay_action)
            self.state_list.append(start_position)


    def show_path(self):
        n_local_state = self.env.grid.shape[0] * self.env.grid.shape[1]
        vis_path = np.array(['-']*n_local_state).reshape(self.env.grid.shape)
        index = np.where(self.env.grid == -1)
        vis_path[index] = '#'
        state_list = np.asarray(self.state_list)
        for i in xrange(len(state_list)):
            vis_path[tuple(state_list[i])] = '@'
            if tuple(state_list[i])==tuple(self.env.goal[self.agent_id]):
                vis_path[tuple(self.env.goal[self.agent_id])] = 'G'

        vis_path[tuple(state_list[0])] = '$'
        #  if len(state_list[state_list==self.env.goal[self.agent_id]) == 2:
            #  vis_path[tuple(self.env.goal[self.agent_id])] = 'G'

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
    from envs.multi_agent_object_world import Objectworld
    from envs.multi_agent_grid_world import Gridworld
    rows = cols = 50
    goal = [rows-1, cols-1]
    #  goal = [23, 28]

    R_max = 1.0
    noise = 0.0
    n_objects = 500
    seed = 1
    num_agent = 2
    mode = 1
    
    object_list = [
                (0, 1), (1, 1), (2, 1), (3, 1)
            ]

    #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, object_list=object_list, random_objects=False, mode=0)
    #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, object_list=object_list, random_objects=False, mode=1)
    #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, mode=1)
    #  env = Objectworld(rows, cols, goal, R_max, noise, n_objects, seed, mode=1)
    #  env = Gridworld(rows, cols, num_agent, noise, seed=seed, mode=mode)
    env = Objectworld(rows, cols, n_objects, num_agent, noise, seed=seed, mode=mode)

    #  print "env.grid : "
    #  env.show_objectworld()

    i = 0

    #  a_agent = AstarAgent(env)

    #  start_position = [0, 0]
    #  a_agent.a_star(start_position)
    while i < 10:
        print "i : ", i
        env.set_start_random()
        env.set_goal_random()
        #  env.set_objects()
        #  print "env.grid : "
        #  env.show_objectworld()
        #  print "env.start[1] : "
        #  print env.start[1]

        a_agent = AstarAgent(env)

        #  a_agent.a_star(start_position)
        a_agent.get_shortest_path(env.start[1], env.grid)
        #  print "a_agent.expand_list : "
        #  print a_agent.expand_list
        #  print "a_agent.action_list : "
        #  print a_agent.action_list
        
        if a_agent.found:
            #  print "a_agent.state_list : "
            #  print a_agent.state_list
            #  print "a_agent.shrotest_action_list : "
            #  print a_agent.shortest_action_list
            #  env.show_policy(a_agent.policy.transpose().reshape(-1))
            path_data = a_agent.show_path()
            print "view_path : "
            a_agent.view_path(path_data['vis_path'])
            #  print "state_list : ", list(path_data['state_list'])
            #  print "action_list : ", path_data['action_list']
            i += 1
