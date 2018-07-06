# Copyright 2018 Uber Technologies, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests for horovod.keras."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import keras
from keras import backend as K

import numpy as np
import os
import tempfile
import unittest

import horovod.keras as hvd


class KerasTests(unittest.TestCase):
    """
    Tests for ops in horovod.keras.
    """

    def __init__(self, *args, **kwargs):
        super(KerasTests, self).__init__(*args, **kwargs)

    def test_load_model(self):
        hvd.init()

        opt = keras.optimizers.RMSprop(lr=0.0001)
        opt = hvd.DistributedOptimizer(opt)

        model = keras.models.Sequential()
        model.add(keras.layers.Dense(2, input_shape=(3,)))
        model.add(keras.layers.RepeatVector(3))
        model.add(keras.layers.TimeDistributed(keras.layers.Dense(3)))
        model.compile(loss=keras.losses.MSE,
                      optimizer=opt,
                      metrics=[keras.metrics.categorical_accuracy],
                      sample_weight_mode='temporal')

        x = np.random.random((1, 3))
        y = np.random.random((1, 3, 3))
        model.train_on_batch(x, y)

        _, fname = tempfile.mkstemp('.h5')
        model.save(fname)

        new_model = hvd.load_model(fname)
        new_opt = new_model.optimizer
        os.remove(fname)

        self.assertEqual(type(new_opt).__module__, 'horovod.keras')
        self.assertEqual(type(new_opt).__name__, 'RMSprop')
        self.assertEqual(K.get_value(opt.lr), K.get_value(new_opt.lr))
        self.assertEqual(len(opt.get_weights()), len(new_opt.get_weights()))
        for weights, new_weights in zip(opt.get_weights(),
                                        new_opt.get_weights()):
            self.assertListEqual(weights.tolist(), new_weights.tolist())

    def test_load_model_custom_optimizers(self):
        hvd.init()

        class TestOptimizer(keras.optimizers.RMSprop):
            def __init__(self, **kwargs):
                super(TestOptimizer, self).__init__(**kwargs)

        opt = TestOptimizer(lr=0.0001)
        opt = hvd.DistributedOptimizer(opt)

        model = keras.models.Sequential()
        model.add(keras.layers.Dense(2, input_shape=(3,)))
        model.add(keras.layers.RepeatVector(3))
        model.add(keras.layers.TimeDistributed(keras.layers.Dense(3)))
        model.compile(loss=keras.losses.MSE,
                      optimizer=opt,
                      metrics=[keras.metrics.categorical_accuracy],
                      sample_weight_mode='temporal')

        x = np.random.random((1, 3))
        y = np.random.random((1, 3, 3))
        model.train_on_batch(x, y)

        _, fname = tempfile.mkstemp('.h5')
        model.save(fname)

        custom_optimizers = [TestOptimizer]
        new_model = hvd.load_model(fname, custom_optimizers=custom_optimizers)
        new_opt = new_model.optimizer
        os.remove(fname)

        self.assertEqual(type(new_opt).__module__, 'horovod.keras')
        self.assertEqual(type(new_opt).__name__, 'TestOptimizer')
        self.assertEqual(K.get_value(opt.lr), K.get_value(new_opt.lr))
        self.assertEqual(len(opt.get_weights()), len(new_opt.get_weights()))
        for weights, new_weights in zip(opt.get_weights(),
                                        new_opt.get_weights()):
            self.assertListEqual(weights.tolist(), new_weights.tolist())

    def test_load_model_custom_objects(self):
        hvd.init()

        class TestOptimizer(keras.optimizers.RMSprop):
            def __init__(self, **kwargs):
                super(TestOptimizer, self).__init__(**kwargs)

        opt = TestOptimizer(lr=0.0001)
        opt = hvd.DistributedOptimizer(opt)

        model = keras.models.Sequential()
        model.add(keras.layers.Dense(2, input_shape=(3,)))
        model.add(keras.layers.RepeatVector(3))
        model.add(keras.layers.TimeDistributed(keras.layers.Dense(3)))
        model.compile(loss=keras.losses.MSE,
                      optimizer=opt,
                      metrics=[keras.metrics.categorical_accuracy],
                      sample_weight_mode='temporal')

        x = np.random.random((1, 3))
        y = np.random.random((1, 3, 3))
        model.train_on_batch(x, y)

        _, fname = tempfile.mkstemp('.h5')
        model.save(fname)

        custom_objects = {
            'TestOptimizer': lambda **kwargs: hvd.DistributedOptimizer(
                TestOptimizer(**kwargs))
        }
        new_model = hvd.load_model(fname, custom_objects=custom_objects)
        new_opt = new_model.optimizer
        os.remove(fname)

        self.assertEqual(type(new_opt).__module__, 'horovod.keras')
        self.assertEqual(type(new_opt).__name__, 'TestOptimizer')
        self.assertEqual(K.get_value(opt.lr), K.get_value(new_opt.lr))
        self.assertEqual(len(opt.get_weights()), len(new_opt.get_weights()))
        for weights, new_weights in zip(opt.get_weights(),
                                        new_opt.get_weights()):
            self.assertListEqual(weights.tolist(), new_weights.tolist())
