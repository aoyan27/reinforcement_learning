#!/usr/bin/env python
#coding:utf-8

import numpy as np
import sys

import chainer 
from chainer import cuda, Variable, optimizers, serializers
from chainer import Chain
import chainer.functions as F
import chainer.links as L

import copy

from agents.value_iteration import ValueIterationAgent

class DeepIRLNetwork(Chain):
    def __init__(self, n_in, n_out):
        super(DeepIRLNetwork, self).__init__(
                l1 = L.Linear(n_in, 400),
                l2 = L.Linear(400, 300),
                l3 = L.Linear(300, n_out),
                )

    def __call__(self, x):
        h = F.relu(self.l1(x))
        h = F.relu(self.l2(h))
        y = self.l3(h)
        return y


class DeepMaximumEntropyIRL:
    def __init__(self, feat_map, P_a, gamma, trajs, learning_rate, n_itrs, env):
        self.feat_map = feat_map
        self.P_a = P_a
        self.gamma = gamma
        self.trajs = trajs
        self.lr = learning_rate
        self.n_itrs = n_itrs
        self.env = env
        
        self.model = DeepIRLNetwork(self.env.n_state, 1)
        self.optimizer = optimizers.SGD(self.lr)
        
        self.optimizer.setup(self.model)
    
    def get_reward(self):
        features = Variable(np.asarray(self.feat_map, dtype=np.float32))
        #  print "features.data : "
        #  print features.data
        reward = self.model(features)
        #  print "rewards__ : "
        #  print rewards
        reward = reward.data.reshape(-1)
        return reward

    def expart_state_visitation_frequencies(self):
        '''
        エキスパートの状態訪問回数を計算
        (すべてのデモの軌道に対して，自身が今どの状態にいるのかをカウントしてる)
        '''
        mu = np.zeros(self.env.n_state)
        for traj in self.trajs:
            #  print "traj : "
            #  print traj
            for i in xrange(len(traj["state"])):
                mu[self.env.state2index(traj["state"][i])] += 1
            #  print "mu : "
            #  print mu
        mu = mu / len(self.trajs)
        #  print "mu_ : "
        #  print mu
        return mu

    def expected_state_visitation_frequencies(self, policy ,deterministic=True):
        '''
        期待状態訪問回数を計算する
        (MaxEntIRLと同様に状態遷移確率と方策，直前の状態にいる確率，の積で計算される)
        '''
        n_state = self.env.n_state
        n_action = self.env.n_action

        T = len(self.trajs[0]["state"])
        
        mu = np.zeros([n_state, T])
        #  print mu

        for i in self.trajs:
            mu[self.env.state2index(i["state"][0]), 0] += 1
        mu[:, 0] = mu[:, 0] / len(self.trajs)

        for s in xrange(n_state):
            for t in xrange(T-1):
                if deterministic:
                    mu[s, t+1] = sum([mu[pre_s, t]*self.P_a[pre_s, s, int(policy[pre_s])] \
                            for pre_s in xrange(n_state)])  
                else:
                    mu[s, t+1] = sum([sum([mu[pre_s, t]*self.P_a[pre_s, s, a1]*policy[pre_s, a1] \
                            for a1 in xrange(n_action)]) for pre_s in xrange(n_state)])
        p = np.sum(mu, 1)
        return p

    def train(self):
        
        '''
        エキスパートのデモでの状態訪問回数を算出
        '''
        mu_D = self.expart_state_visitation_frequencies()
        print "mu_D : "
        print mu_D

        '''
        学習行程
        '''
        for itr in xrange(self.n_itrs):
            if itr % (self.n_itrs/10) == 0:
              print 'iteration: {}'.format(itr)

            '''
            現在のネットワークモデルに基づいて、報酬を計算...
            '''
            reward = self.get_reward()
            print "reward : "
            print reward

            '''
            推定された報酬を基に価値反復で方策を計算...
            '''
            agent = ValueIterationAgent(self.env, self.P_a, self.gamma)
            agent.train(reward)
            print "V : "
            print agent.V.reshape([self.env.rows, self.env.cols])
            agent.get_policy(reward)
            #  agent.get_policy(reward, deterministic=False)
            print "policy : "
            print agent.policy
            #  self.env.show_policy(agent.policy.reshape(-1))
            _, policy = agent.V, agent.policy
            #  print policy.reshape([self.env.rows, self.env.cols])

            '''
            期待状態訪問回数(expected state visitation frequencies)を計算する
                (dynamic programingで計算する)
            '''
            mu_exp = self.expected_state_visitation_frequencies(policy)
            #  mu_exp = self.expected_state_visitation_frequencies(policy, deterministic=False)
            print "mu_exp : "
            print mu_exp

            '''
            勾配の計算
            '''
            grad_r = mu_D - mu_exp
            print "grad_r : "
            print grad_r
