#!/usr/bin/env python
#coding : utf-8

import numpy as np
np.set_printoptions(precision=1, suppress=True, threshold=np.inf)

import chainer 
from chainer import cuda, Variable, optimizers, serializers
from chainer import Chain
import chainer.functions as F
import chainer.links as L

class MultiAgentValueIterationNetwork(Chain):
    def __init__(self, n_in=2, l_h=150, l_q=9, n_out=9, k=10, net=None):
        super(MultiAgentValueIterationNetwork, self).__init__(
            conv1 = L.Convolution2D(n_in, l_h, 3, stride=1, pad=1, \
                    initialW=net.conv1.W.data, initial_bias=net.conv1.b.data), 
            conv2 = L.Convolution2D(l_h, 1, 1, stride=1, pad=0, \
                    initialW=net.conv2.W.data, nobias=True),

            conv3a = L.Convolution2D(1, l_q, 3, stride=1, pad=1, \
                    initialW=net.conv3a.W.data, nobias=True),
            conv3b = L.Convolution2D(1, l_q, 3, stride=1, pad=1, \
                    initialW=net.conv3b.W.data, nobias=True),

            l4 = L.Linear(None, 128, nobias=True),
            l5 = L.Linear(128, 128, nobias=True),
            l6 = L.Linear(128, n_out, nobias=True),
        )

        self.k = k
    
    def attention(self, q, state_list):
        #  print "q.data : ",
        #  print q.data[0]
        w = np.zeros(q.data.shape)
        #  print "w : ", w.shape
        for i in xrange(len(state_list)):
            #  print "state_list : ", state_list[i]
            w[i, :, int(state_list[i][0]), int(state_list[i][1])] = 1.0
            #  print "w : "
            #  print w[i]

        if isinstance(q.data, cuda.ndarray):
            w = cuda.to_gpu(w)

        #  print q.data.shape
        #  print w.shape
        
        w = Variable(w.astype(np.float32))
        #  print "state_list : "
        #  print state_list[0]
        a = q * w
        #  print "a : "
        #  print a.shape
        a = F.reshape(a, (a.data.shape[0], a.data.shape[1], -1))
        #  print "a() : "
        #  print a.shape

        q_out = F.sum(a, axis=2)
        #  print "q_out : "
        #  print q_out
        #  print q_out.shape
        return q_out


    def __call__(self, input_data, state_list, position_list):
        input_data = Variable(input_data.astype(np.float32))

        h = F.relu(self.conv1(input_data))
        #  print "h : ", h
        self.r = self.conv2(h)
        #  print "self.r : ", self.r
        #  print "self.r : ", self.r.data.shape

        q = self.conv3a(self.r)
        #  print "q : ", q.data.shape
        
        self.v = F.max(q, axis=1, keepdims=True)
        #  print "self.v : ", self.v.shape

        for i in xrange(self.k):
            q = self.conv3a(self.r) + self.conv3b(self.v)
            self.v = F.max(q, axis=1, keepdims=True)

        #  print "q(after k) : ", q.shape
        #  print "q(after k) : ", q
        #  print "self.v : ", self.v
        
        q = self.conv3a(self.r) + self.conv3b(self.v)
        q_out = self.attention(q, state_list)

        position_ = position_list.astype(np.float32)

        concat_1 = F.concat((q_out, position_), axis=1)

        #  h1 = self.l4(concat_1)
        #  h2 = self.l5(h1)
        #  y = self.l6(h2)
        h1 = F.relu(self.l4(concat_1))
        h2 = F.relu(self.l5(h1))
        y = self.l6(h2)

        return y

    def forward(self, input_data, state_list, position_list, action_list):
        y = self.__call__(input_data, state_list, position_list)
        #  print "y : ", y
        
        t = Variable(action_list.astype(np.int32))

        return F.softmax_cross_entropy(y, t), F.accuracy(y, t)



