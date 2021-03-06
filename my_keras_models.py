# from constants import *
from environments import *
import numpy as np
import keras
import os
import pdb
from keras.models import Sequential, Graph
from keras.layers.core import Dense, Dropout, Activation, Flatten, MaxoutDense
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import RMSprop, SGD
from keras.layers.normalization import BatchNormalization
from keras.constraints import maxnorm, nonneg
import time

import keras.regularizers

leakage = 0.1

#------------- Element functions ------------- #
def get_NIN_weights(num_layers):
	pool_sizes = [None]*num_layers
	if num_layers == 3:
		vgg_modi_weight = [[4, 2], [8, 4], [12, 8]] 
		pool_sizes[0] = (2,5)
		pool_sizes[1] = (4,5)
		pool_sizes[2] = (4,3) # --> output: (4x2)

	elif num_layers == 4: # so that height(128) becomes 2 
		vgg_modi_weight = [[2,2], [4,3], [6,4], [8,6]]  # similar to red_pig. 'rich' setting --> later!the most popular setting

		pool_sizes[0] = (2,4)
		pool_sizes[1] = (2,4)
		pool_sizes[2] = (2,2)
		pool_sizes[3] = (4,2) # --> output: 4x4=16 melgram -->  red_pig, the most popular setting

		# 09 Feb. more temporal pooling, add more feature maps

		vgg_modi_weight = [[2,2], [4,4], [8,8], [16,16]]  # 512 feature maps
		pool_sizes[0] = (2,4)
		pool_sizes[1] = (2,4)
		pool_sizes[2] = (2,4)
		pool_sizes[3] = (2,4) # --> output: 8x1=8 melgram -->  red_pig, the most popular setting

		# from 11 Feb. 03:33.
		vgg_modi_weight = [[2,2], [4,4], [8,8], [12,12]]  # 512 feature maps
		pool_sizes[0] = (1,4) # two 3x3 layers --> 5x5 
		pool_sizes[1] = (2,4) # four 3x3 --> 9x9
		pool_sizes[2] = (2,4) ##  six --> 13x13 patches! (not yet here)
		pool_sizes[3] = (2,4) # --> output: 16x1=16 melgram -->  red_pig, the most popular setting
		
		# or even?
		vgg_modi_weight = [[2,2], [4,4], [8,8], [12,12]]  # 512 feature maps
		pool_sizes[0] = (1,4) # two 3x3 layers --> 5x5 
		pool_sizes[1] = (1,4) # four 3x3 --> 9x9
		pool_sizes[2] = (2,4) ##  six --> 13x13 patches! (not yet here)
		pool_sizes[3] = (4,4) # --> output: 16x1=16 melgram -->  red_pig, the most popular setting
		# pool_sizes[0] = (1,4)
		# pool_sizes[1] = (2,4)
		# pool_sizes[2] = (2,4)
		# pool_sizes[3] = (4,2) # --> output: 8x2=16 melgram -->  more freq resolution. 
		
		# mp_strides[0] = (2,3)
		# mp_strides[1] = (2,3)
		# mp_strides[2] = (2,3)
		# mp_strides[3] = (3,3)
		
	elif num_layers == 5:
		vgg_modi_weight = [[3,2], [4,3], [6, 4], [8, 6], [12,8]] # final layer: 8x32=256 featue maps, 
		pool_sizes[0] = (2,4) # mel input: 128x252
		pool_sizes[1] = (2,2)
		pool_sizes[2] = (2,2)
		pool_sizes[3] = (2,2)
		pool_sizes[4] = (2,2) # --> 4x4 same as red_pig

		# tall thing.

		pool_sizes[0] = (1,4) # mel input: 128x252
		pool_sizes[1] = (1,4)
		pool_sizes[2] = (2,4)
		pool_sizes[3] = (2,2)
		pool_sizes[4] = (2,2) # --> 16x1
		# mp_strides[0] = (1,1)
		# mp_strides[1] = (1,1)
		# mp_strides[2] = (1,1)
		# mp_strides[3] = (1,2) #
	elif num_layers == 6:
		vgg_modi_weight = [[3,2], [4,3], [6, 4], [8, 6], [12,8], [16,12]] # final layer: 8x32=256 featue maps, 
		pool_sizes[0] = (2,2) # mel input: 128x252
		pool_sizes[1] = (2,2)
		pool_sizes[2] = (2,2)
		pool_sizes[3] = (2,2)
		pool_sizes[4] = (2,2) 
		pool_sizes[5] = (2,2) # --> 2x4 similar as red_pig
	elif num_layers == 7:
		vgg_modi_weight = [[3,2], [4,3], [6, 4], [8, 6], [12,8], [16,12], [20, 16]] # final layer: 8x32=256 featue maps, 
		pool_sizes[0] = (2,2) # mel input: 128x252
		pool_sizes[1] = (2,2)
		pool_sizes[2] = (2,2)
		pool_sizes[3] = (2,2)
		pool_sizes[4] = (2,2) 
		pool_sizes[5] = (2,2)
		pool_sizes[6] = (2,2)  # 1x2 output
	elif num_layers == 8:
		vgg_modi_weight = [[3,2], [4,3], [6, 4], [8, 8], [16,16], [32,32], [64, 64], [128, 128]] # final layer: 8x32=256 featue maps, 
		pool_sizes[0] = (2,2) # mel input: 128x252, output 64x128
		pool_sizes[1] = (2,2) # 32x64
		pool_sizes[2] = (2,2) # 16x32
		pool_sizes[3] = (2,2) # 8x16
		pool_sizes[4] = (2,2) # 4x8
		pool_sizes[5] = (2,2) # 2x4
		pool_sizes[6] = (2,2) # 1x2 output
		pool_sizes[7] = (1,2) # 1x1 output

	return vgg_modi_weight, pool_sizes
#-------------

def get_activation(activation_name):
	'''input: keras model, string.
	output: keras activation instance'''
	print ' ---->>%s activation is added.' % activation_name
	if activation_name == 'relu':
		return Activation('relu')
	elif activation_name == 'lrelu':
		return keras.layers.advanced_activations.LeakyReLU(alpha=leakage)
	elif activation_name == 'prelu':
		return keras.layers.advanced_activations.PReLU()
	elif activation_name == 'elu':
		return keras.layers.advanced_activations.ELU(alpha=1.0)

def get_regulariser(tuple_input):
	if tuple_input in [None, 0.0]:
		return None
	if None in tuple_input:
		print ' ---->> None is in tuple input, ', tuple_input
		return None
	name, value = tuple_input
	if value == 0.0:
		return None
	print ' ---->> prepare %s regulariser with %f' % (name, value)
	if name == 'l1':
		W_regularizer=keras.regularizers.l1(value)
	elif name == 'l2':
		W_regularizer=keras.regularizers.l2(value)
	elif name == 'l1l2':
		W_regularizer=keras.regularizers.l1l2(value, value)
	elif name == 'activity_l1':
		W_regularizer=keras.regularizers.activity_l1(value)
	elif name == 'activity_l2':
		W_regularizer=keras.regularizers.activity_l2(value)
	elif name == 'activity_l1l2':
		W_regularizer=keras.regularizers.activity_l1l2(value, value)
	return W_regularizer

def build_convnet_model(setting_dict):
	start = time.time()
	loss_function = setting_dict["loss_function"]
	optimizer_name = setting_dict["optimiser"].lower() # 'SGD', 'RMSProp', ..
	learning_rate = setting_dict['learning_rate']
	#------------------------------------------------------------------#
	model_type = setting_dict["model_type"]
	if model_type.startswith('vgg'):
		model = design_2d_convnet_model(setting_dict)
	elif model_type.startswith('gnu'):
		if model_type == 'gnu_1d':
			model = design_gnu_convnet_model(setting_dict)
		elif model_type == 'gnu_mfcc':
			model = design_mfcc_convnet_model(setting_dict)
	elif model_type == 'residual':
		model = design_residual_model(setting_dict)
	elif model_type == 'multi_task':
		model = design_2d_convnet_graph(setting_dict)
	elif model_type == 'multi_input':
		model = design_2d_convnet_graph(setting_dict)
	#------------------------------------------------------------------#
	if optimizer_name == 'sgd':
		optimiser = SGD(lr=learning_rate, momentum=0.9, decay=1e-5, nesterov=True)
	elif optimizer_name == 'rmsprop':
		optimiser = RMSprop(lr=learning_rate, rho=0.9, epsilon=1e-6)
	elif optimizer_name == 'adagrad':
		optimiser = keras.optimizers.Adagrad(lr=0.01, epsilon=1e-06)
	elif optimizer_name == 'adadelta':
		optimiser = keras.optimizers.Adadelta(lr=1.0, rho=0.95, epsilon=1e-06)
	elif optimizer_name == 'adam':
		optimiser = keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
	else:
		raise RuntimeError('no optimiser? no! - %s' % optimizer_name )
	print ' ---->>--- ready to compile keras model ---'
	if model_type not in ['multi_task', 'multi_input']:
		model.compile(loss=loss_function, optimizer=optimiser, class_mode='binary') 
	else:
		loss_dict = {}
		for dense_idx in xrange(setting_dict['dim_labels']):
			output_node_name = 'output_%d' % dense_idx
			loss_dict[output_node_name] = loss_function

		model.compile(loss=loss_dict, optimizer=optimiser) 
	until = time.time()
 	print "--- keras model was built, took %d seconds ---" % (until-start)
 	
	return model

def design_2d_convnet_model(setting_dict):

	is_test = setting_dict["is_test"]
	height = setting_dict["height_image"]
	width = setting_dict["width_image"]
	dropouts = setting_dict["dropouts"]
	num_labels = setting_dict["dim_labels"]
	num_layers = setting_dict["num_layers"]
	activations = setting_dict["activations"] #
	model_type = setting_dict["model_type"] # not used now.
	num_stacks = setting_dict["num_feat_maps"]

	num_fc_layers = setting_dict["num_fc_layers"]
	dropouts_fc_layers = setting_dict["dropouts_fc_layers"]
	nums_units_fc_layers = setting_dict["nums_units_fc_layers"]
	activations_fc_layers = setting_dict["activations_fc_layers"]
	# mp_strides = [(2,2)]*setting_dict['num_layers']
	#------------------------------------------------------------------#
	num_channels=1
	sigma = setting_dict['gn_sigma']	
	nb_maxout_feature = setting_dict['nb_maxout_feature']
	#-----------------------

	if model_type.startswith('vgg'):
		# layers = 4,5,6
		if model_type.startswith('vgg_'): # vgg_modi_1x1, vgg_modi_3x3, and even vgg_simple
			if setting_dict['tf_type'] in ['cqt', 'stft', 'melgram']:
				image_patch_sizes = [[3,3]]*num_layers
				pool_sizes = [(2,2)]*num_layers
				vgg_modi_weight, pool_sizes = get_NIN_weights(num_layers=num_layers)
				setting_dict['vgg_modi_weight'] = vgg_modi_weight
			
		else:
			if setting_dict['tf_type'] in ['cqt', 'stft', 'melgram']:
				image_patch_sizes = [[3,3]]*num_layers
				pool_sizes = [(2,2)]*num_layers

			elif setting_dict['tf_type'] == 'mfcc':
				image_patch_sizes = [[height,1]]*num_layers
				pool_sizes = [(1,2)]*num_layers
	elif model_type.startswith('flow'):
		pass # less layers, bigger filter.
	
	setting_dict['pool_sizes'] = pool_sizes

	#-------------------------------#
	# prepre modules
	model = Sequential()
	# zero-adding
	if setting_dict['tf_type'] == 'melgram':
		model.add(keras.layers.convolutional.ZeroPadding2D(padding=(0,3), dim_ordering='th', input_shape=(num_channels, height, width)))
	elif setting_dict['tf_type'] == 'cqt':
		model.add(keras.layers.convolutional.ZeroPadding2D(padding=(2,3), dim_ordering='th', input_shape=(num_channels, height, width)))
	elif setting_dict['tf_type'] == 'stft':
		model.add(keras.layers.convolutional.ZeroPadding2D(padding=(0,3), dim_ordering='th', input_shape=(num_channels, height, width)))
	else:
		raise RuntimeError('Unknown tf_type:%s' % setting_dict['tf_type'])

	# average pooling (down sample) for stft: 257 --> 128
	if setting_dict['tf_type'] == 'stft':
		print 'STFT --> downsampled by 2'
		model.add(keras.layers.convolutional.AveragePooling2D(pool_size=(2, 1), border_mode='valid', dim_ordering='th'))

	# additive gaussian noise
	if setting_dict['gaussian_noise']:
		print ' ---->>add gaussian noise '
		model.add(keras.layers.noise.GaussianNoise(sigma))

	#[Convolutional Layers]
	for conv_idx in xrange(num_layers):
		# prepare regularizer if needed.
		W_regularizer = get_regulariser(setting_dict['regulariser'][conv_idx])
			
		# add conv layer
		if model_type.startswith('vgg_'):
			n_feat_here = int(num_stacks[conv_idx]*vgg_modi_weight[conv_idx][0])
		else:
			n_feat_here = num_stacks[conv_idx]

		if conv_idx == 0 and not setting_dict['gaussian_noise']:
			print ' ---->>First conv layer is being added! wigh %d' % n_feat_here
			model.add(Convolution2D(n_feat_here, image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
									border_mode='same',  # no input shape after adding zero-padding
									W_regularizer=W_regularizer, init='he_normal'))

		else:
			print ' ---->>%d-th conv layer is being added with %d units' % (conv_idx, n_feat_here)
			model.add(Convolution2D(n_feat_here, image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
									border_mode='same',	W_regularizer=W_regularizer,
									init='he_normal'))
		# add BN
		if setting_dict['BN']:
			print ' ---->>BN is added for conv layer'
			model.add(BatchNormalization(axis=1))

		# add activation
		model.add(get_activation(activations[0]))
		
		# [second conv layers] for vgg_original or vgg_modi
		if model_type in ['vgg_original', 'vgg_modi_1x1', 'vgg_modi_3x3']:
			# add dropout
			if not dropouts[conv_idx] == 0.0:
				model.add(Dropout(dropouts[conv_idx]))
				print ' ---->>Add dropout of %f for %d-th conv layer' % (dropouts[conv_idx], conv_idx)

			if model_type.startswith('vgg_modi'):
				n_feat_here = int(num_stacks[conv_idx]*vgg_modi_weight[conv_idx][0])
			else:
				n_feat_here = num_stacks[conv_idx]

			W_regularizer = get_regulariser(setting_dict['regulariser'][conv_idx])

			if model_type == 'vgg_original':
				print ' ---->>  additional conv layer is added for vgg_original, %d' % (n_feat_here)
				model.add(Convolution2D(n_feat_here, image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
										border_mode='same',	W_regularizer=W_regularizer, init='he_normal'))
			elif model_type == 'vgg_modi_1x1':
				print ' ---->>  additional conv layer is added for vgg_modi_1x1, %d' % (n_feat_here)
				model.add(Convolution2D(n_feat_here, 1, 1, 
										border_mode='same',	W_regularizer=W_regularizer, init='he_normal'))
			elif model_type == 'vgg_modi_3x3':
				print ' ---->>  additional conv layer is added for vgg_modi_3x3, %d' % (n_feat_here)
				model.add(Convolution2D(n_feat_here, image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
										border_mode='same',	W_regularizer=W_regularizer, init='he_normal'))

			if setting_dict['BN']:
				print ' ---->>  and BN,'
				model.add(BatchNormalization(axis=1))
			# add activation
			model.add(get_activation(activations[0]))
					# add dropout
			if not dropouts[conv_idx] == 0.0:
				model.add(Dropout(dropouts[conv_idx]))
				print ' ---->>Add dropout of %f for %d-th conv layer' % (dropouts[conv_idx], conv_idx)
		
		#[third conv layer] for vgg_modi_3x3
		if model_type == 'vgg_modi_3x3':
			n_feat_here = int(num_stacks[conv_idx]*vgg_modi_weight[conv_idx][1])
			W_regularizer = get_regulariser(setting_dict['regulariser'][conv_idx])
			print ' ---->>     one more additional 1x1 conv layer is added for vgg_modi_3x3, %d' % (n_feat_here)
			model.add(Convolution2D(n_feat_here, 1, 1, 
									border_mode='same',	W_regularizer=W_regularizer, init='he_normal'))
			if setting_dict['BN']:
				print ' ---->>    and BN + elu'
				model.add(BatchNormalization(axis=1))
			model.add(get_activation(activations[0]))

		# add pooling
		if model_type in ['vgg_original', 'vgg_modi_1x1', 'vgg_modi_3x3', 'vgg_simple']:
			print ' ---->>MP is added', pool_sizes[conv_idx]
			model.add(MaxPooling2D(pool_size=pool_sizes[conv_idx]))
		# elif model_type.startswith('vgg_simple'):
		# 	print ' ---->>MP is added', pool_sizes[conv_idx]
		# 	model.add(MaxPooling2D(pool_size=pool_sizes[conv_idx]))
		
		# add dropout
		if not dropouts[conv_idx] == 0.0:
			model.add(Dropout(dropouts[conv_idx]))
			print ' ---->>Add dropout of %f for %d-th conv layer' % (dropouts[conv_idx], conv_idx)
	
	#[Fully Connected Layers]
	model.add(Flatten())
	for fc_idx in xrange(num_fc_layers):
		# setup regulariser
		W_regularizer = get_regulariser(	setting_dict['regulariser_fc_layers'][fc_idx])
		act_regularizer = get_regulariser(setting_dict['act_regulariser_fc_layers'][fc_idx])
		
		if setting_dict['maxout']:
			# maxout...	
			model.add(MaxoutDense(nums_units_fc_layers[fc_idx], nb_feature=nb_maxout_feature ))
			print ' --->>MaxoutDense added with %d output units, %d features, no regularizer' % (nums_units_fc_layers[fc_idx], nb_maxout_feature)
		else:
			
			# ..or, dense layer
			print ' ---->>Dense layer, %d, is added' % nums_units_fc_layers[fc_idx]
			print '       with regulariser if it was ready.'
			model.add(Dense(nums_units_fc_layers[fc_idx], W_regularizer=W_regularizer,
														activity_regularizer=act_regularizer,
														init='he_normal'))
			# Activations
			model.add(get_activation(activations_fc_layers[0]))
		
		# Dropout
		if not dropouts_fc_layers[fc_idx] == 0.0:
			model.add(Dropout(dropouts_fc_layers[fc_idx]))
			print ' ---->>Dropout for fc layer, %f' % dropouts_fc_layers[fc_idx]
		# BN
		if setting_dict['BN_fc_layers']:
			print ' ---->>BN for dense is added'
			model.add(BatchNormalization()) ## BN vs Dropout - who's first?
		
	#[Output layer]
	if setting_dict["output_activation"]:
		print ' ---->>Output dense and activation is: %s with %d units' % (setting_dict["output_activation"], num_labels)
		model.add(Dense(num_labels, activation=setting_dict["output_activation"],
									init='he_normal')) 
	else:
		print ' ---->>Output dense and activation: linear with %d units' % num_labels
		model.add(Dense(num_labels, activation='linear')) 

	return model	


def design_2d_convnet_graph(setting_dict):

	is_test = setting_dict["is_test"]
	height = setting_dict["height_image"]
	width = setting_dict["width_image"]
	dropouts = setting_dict["dropouts"]
	num_labels = setting_dict["dim_labels"]
	num_layers = setting_dict["num_layers"]
	activations = setting_dict["activations"] #
	model_type = setting_dict["model_type"] # not used now.
	num_stacks = setting_dict["num_feat_maps"]

	num_fc_layers = setting_dict["num_fc_layers"]
	dropouts_fc_layers = setting_dict["dropouts_fc_layers"]
	nums_units_fc_layers = setting_dict["nums_units_fc_layers"]
	activations_fc_layers = setting_dict["activations_fc_layers"]

	mfcc_height = setting_dict["mfcc_height_image"]
	mfcc_width = setting_dict["mfcc_width_image"]
	# mp_strides = [(2,2)]*setting_dict['num_layers']

	cond_multi_input = (model_type == 'multi_input')
	mfcc_image_patch_size = [[mfcc_height/3,1], [1,1], [1,1], [1,1]]
	mfcc_pool_sizes = [(1,4), (1,4), (1,4), (1,4)]
	mfcc_num_stacks = [128, 256, 512, 1024]
	#------------------------------------------------------------------#
	num_channels=1
	image_patch_sizes = [[3,3]]*num_layers
	vgg_modi_weight, pool_sizes = get_NIN_weights(num_layers=num_layers)
	print vgg_modi_weight
	print pool_sizes
	#------------------------------------------------------------------#

	model = Graph()
	print 'Add zero padding '
	model.add_input(name='input', input_shape=(num_channels, height, width), dtype='float')
	model.add_node(keras.layers.convolutional.ZeroPadding2D(padding=(0,3),  # melgram.
					dim_ordering='th'),
					input='input',
					name = 'zeropad')
	last_node_name = 'zeropad'

	for conv_idx in xrange(num_layers):
		print 'Add conv layer %d' % conv_idx
		n_feat_here = int(num_stacks[conv_idx]*vgg_modi_weight[conv_idx][0])
		# conv 0
		this_node_name = 'conv_%d_0' % conv_idx
		model.add_node(Convolution2D(n_feat_here, image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
						border_mode='same',  # no input shape after adding zero-padding
						init='he_normal'),
						input=last_node_name,
						name=this_node_name)
		last_node_name = this_node_name

		this_node_name = 'bn_%d_0' % conv_idx
		model.add_node(BatchNormalization(axis=1),
										input=last_node_name,
										name=this_node_name)
		last_node_name = this_node_name

		this_node_name = 'elu_%d_0' % conv_idx
		model.add_node(keras.layers.advanced_activations.ELU(alpha=1.0),
										input=last_node_name,
										name=this_node_name)
		last_node_name = this_node_name
		# # conv 1
		# this_node_name = 'conv_%d_1' % conv_idx
		# model.add_node(Convolution2D(n_feat_here, 1,1, 
		# 				border_mode='same',  # no input shape after adding zero-padding
		# 				init='he_normal'),
		# 				input=last_node_name,
		# 				name=this_node_name)
		# last_node_name = this_node_name		

		# this_node_name = 'bn_conv_%d_1' % conv_idx
		# model.add_node(BatchNormalization(axis=1),
		# 								input=last_node_name,
		# 								name=this_node_name)
		# last_node_name = this_node_name

		# this_node_name = 'elu_conv_%d_1' % conv_idx
		# model.add_node(keras.layers.advanced_activations.ELU(alpha=1.0),
		# 								input=last_node_name,
		# 								name=this_node_name)
		# last_node_name = this_node_name

		this_node_name = 'mp_%d' % conv_idx
		model.add_node(MaxPooling2D(pool_size=pool_sizes[conv_idx]),
									input=last_node_name,
									name=this_node_name)
		last_node_name = this_node_name

		this_node_name = 'dropout_conv_%d' % conv_idx
		model.add_node(Dropout(dropouts[conv_idx]),
									input=last_node_name,
									name=this_node_name)
		last_node_name = this_node_name		

	if cond_multi_input:
		print '=== Multi input! ==='
		model.add_input(name='mfcc_input', input_shape=(1, mfcc_height, mfcc_width), dtype='float')
		model.add_node(keras.layers.convolutional.ZeroPadding2D(padding=(0,3),  # melgram.
						dim_ordering='th'),
						input='mfcc_input',
						name = 'mfcc_zeropad')
		mfcc_last_node_name = 'mfcc_zeropad'
		# conv layers
		for conv_idx in xrange(num_layers):
			mfcc_this_node_name = 'mfcc_conv_%d_0' % conv_idx
			if conv_idx ==0:
				model.add_node(Convolution2D(mfcc_num_stacks[conv_idx], mfcc_image_patch_size[conv_idx][0], mfcc_image_patch_size[conv_idx][1],
											border_mode='valid',
											subsample=(mfcc_height/3, 1),
											init='he_normal'),
								input=mfcc_last_node_name,
								name=mfcc_this_node_name)
			else:
				model.add_node(Convolution2D(mfcc_num_stacks[conv_idx], mfcc_image_patch_size[conv_idx][0], mfcc_image_patch_size[conv_idx][1],
											border_mode='same',
											init='he_normal'),
								input=mfcc_last_node_name,
								name=mfcc_this_node_name)
			mfcc_last_node_name = mfcc_this_node_name

			mfcc_this_node_name = 'mfcc_bn_%d' % conv_idx
			model.add_node(BatchNormalization(),
							input=mfcc_last_node_name,
							name=mfcc_this_node_name)
			mfcc_last_node_name = mfcc_this_node_name

			mfcc_this_node_name = 'mfcc_elu_%d' % conv_idx
			model.add_node(get_activation(activations[0]),
							input=mfcc_last_node_name,
							name=mfcc_this_node_name)
			mfcc_last_node_name = mfcc_this_node_name

			mfcc_this_node_name = 'mfcc_mp_%d' % conv_idx
			model.add_node(MaxPooling2D(pool_size=mfcc_pool_sizes[conv_idx]),
							input=mfcc_last_node_name,
							name=mfcc_this_node_name)
			mfcc_last_node_name = mfcc_this_node_name

		mfcc_this_node_name='mfcc_flatten'
		model.add_node(Flatten(), input=mfcc_last_node_name,
									name=mfcc_this_node_name)
		mfcc_last_node_name = mfcc_this_node_name


	# end of conv
	print 'Add flatten layer'
	this_node_name = 'flatten'
	model.add_node(Flatten(), input=last_node_name,
								name=this_node_name)
	last_node_name = this_node_name
	
	# merge if needed



	for fc_idx in xrange(num_fc_layers):
		print 'Add fc layer %d' % fc_idx
		this_node_name = 'maxout_%d' % fc_idx
		nb_feature = 4
		if cond_multi_input:
			model.add_node(MaxoutDense(nums_units_fc_layers[fc_idx], 
									nb_feature=nb_feature),
							inputs=['flatten', 'mfcc_flatten'],
							name=this_node_name,
							merge_mode='concat')
		else:
			model.add_node(MaxoutDense(nums_units_fc_layers[fc_idx], 
									nb_feature=nb_feature),
							input=last_node_name,
							name=this_node_name)
		last_node_name = this_node_name

		this_node_name = 'bn_fc_%d' % fc_idx
		model.add_node(BatchNormalization(axis=1),
										input=last_node_name,
										name=this_node_name)
		last_node_name = this_node_name

	# 50 dense layers
	# num_sparse_units = int(nums_units_fc_layers[num_fc_layers-1]/setting_dict['dim_labels'])
	num_sparse_units = setting_dict['num_sparse_units']
	nb_maxout_feature = setting_dict['nb_maxout_feature']
	print 'num sparse units: %d' % num_sparse_units
	print 'Add dense layers, %d x %d' % (setting_dict['dim_labels'], num_sparse_units)
	if setting_dict['maxout_sparse_layer']:
		print 'use Maxout in sparse layer'
	else:
		print 'use dense in sparse layer'

	for dense_idx in xrange(setting_dict['dim_labels']):
		# 1	
		for sparse_idx in xrange(setting_dict['num_sparse_layer']):
			sparse_node_name = 'dense_sparse_%d_%d' % (sparse_idx, dense_idx) # (0,0) to (1,50)
			if not setting_dict['maxout_sparse_layer']:

				if sparse_idx == 0:
					if cond_multi_input and num_fc_layers == 0: # multi-input and fully sparse.
						model.add_node(Dense(num_sparse_units), 
									inputs=['flatten', 'mfcc_flatten'],
									name=sparse_node_name,
									merge_mode='concat')
					else:
						model.add_node(Dense(num_sparse_units), 
										input=last_node_name,
										name=sparse_node_name)
				else:
					model.add_node(Dense(num_sparse_units), 
									input=bn_node_name,
									name=sparse_node_name)


				elu_node_name = 'elu_sparse_%d_%d' % (sparse_idx, dense_idx)
				model.add_node(get_activation('elu'),
								input=sparse_node_name,
								name=elu_node_name)
				node_before_dropout = elu_node_name

			else:
				if sparse_idx == 0:
					if cond_multi_input and num_fc_layers ==0:
						model.add_node(MaxoutDense(num_sparse_units, nb_feature=nb_maxout_feature ),
									inputs=['flatten', 'mfcc_flatten'],
									name=sparse_node_name,
									merge_mode='concat')
					else:
						model.add_node(MaxoutDense(num_sparse_units, nb_feature=nb_maxout_feature ),
										input=last_node_name,
										name=sparse_node_name)
				else:
					model.add_node(MaxoutDense(num_sparse_units, nb_feature=nb_maxout_feature ),
									input=bn_node_name,
									name=sparse_node_name)
				node_before_dropout = sparse_node_name

			dropout_node_name = 'dropout_sparse_%d_%d' % (sparse_idx, dense_idx)
			model.add_node(Dropout(0.6),
							input=node_before_dropout,
							name=dropout_node_name)

			bn_node_name = 'batch_nor_sparse_%d_%d' % (sparse_idx, dense_idx)
			model.add_node(BatchNormalization(),
							input=dropout_node_name,
							name=bn_node_name)
		# output
		output_gate_node_name = 'output_gate_%d' % dense_idx
		model.add_node(Dense(1, activation='sigmoid'),
						input=bn_node_name,
						name=output_gate_node_name)

		output_node_name = 'output_%d' % dense_idx
		model.add_output(input=output_gate_node_name,
						name=output_node_name)

	print 'add sparse node: Done '
	return model
'''

def design_simple_graph(setting_dict):

	is_test = setting_dict["is_test"]
	height = setting_dict["height_image"]
	width = setting_dict["width_image"]
	dropouts = setting_dict["dropouts"]
	num_labels = setting_dict["dim_labels"]
	num_layers = setting_dict["num_layers"]
	activations = setting_dict["activations"] #
	model_type = setting_dict["model_type"] # not used now.
	num_stacks = setting_dict["num_feat_maps"]

	num_fc_layers = setting_dict["num_fc_layers"]
	dropouts_fc_layers = setting_dict["dropouts_fc_layers"]
	nums_units_fc_layers = setting_dict["nums_units_fc_layers"]
	activations_fc_layers = setting_dict["activations_fc_layers"]
	# mp_strides = [(2,2)]*setting_dict['num_layers']
	#------------------------------------------------------------------#
	num_channels=1
	image_patch_sizes = [[3,3]]*num_layers
	vgg_modi_weight, pool_sizes = get_NIN_weights(num_layers=num_layers)
	print vgg_modi_weight
	print pool_sizes
	#------------------------------------------------------------------#
	model = Graph()
	print 'Add zero padding '
	model.add_input(name='input', input_shape=(num_channels, height, width), dtype='float')
	model.add_node(keras.layers.convolutional.ZeroPadding2D(padding=(0,2), 
					dim_ordering='th'),
					input='input',
					name = 'zeropad')
	last_node_name = 'zeropad'

	conv_idx = 0
	print 'Add conv layer %d' % conv_idx
	n_feat_here = num_stacks[conv_idx]
	# conv 0
	this_node_name = 'conv_%d_0' % conv_idx
	model.add_node(Convolution2D(n_feat_here, image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
						border_mode='same',  # no input shape after adding zero-padding
						init='he_normal'),
						input=last_node_name,
						name=this_node_name)
	last_node_name = this_node_name

	this_node_name = 'bn_%d_0' % conv_idx
	model.add_node(BatchNormalization(axis=1),
									input=last_node_name,
									name=this_node_name)
	last_node_name = this_node_name

	this_node_name = 'elu_%d_0' % conv_idx
	model.add_node(keras.layers.advanced_activations.ELU(alpha=1.0),
										input=last_node_name,
										name=this_node_name)
	# last_node_name = this_node_name
	# 	# conv 1
	# this_node_name = 'conv_%d_1' % conv_idx
	# model.add_node(Convolution2D(n_feat_here, 1,1, 
	# 					border_mode='same',  # no input shape after adding zero-padding
	# 					init='he_normal'),
	# 					input=last_node_name,
	# 					name=this_node_name)
	# last_node_name = this_node_name		

	# this_node_name = 'bn_conv_%d_1' % conv_idx
	# model.add_node(BatchNormalization(axis=1),
	# 									input=last_node_name,
	# 									name=this_node_name)
	# last_node_name = this_node_name

	# this_node_name = 'elu_conv_%d_1' % conv_idx
	# model.add_node(keras.layers.advanced_activations.ELU(alpha=1.0),
	# 									input=last_node_name,
	# 									name=this_node_name)
	# last_node_name = this_node_name
	# end of conv
	print 'Add flatten layer'
	this_node_name = 'flatten'
	model.add_node(Flatten(), input=last_node_name,
								name=this_node_name)
	last_node_name = this_node_name
	
	fc_idx = 0
	print 'Add fc layer %d' % fc_idx
	this_node_name = 'maxout_%d' % fc_idx
	nb_feature = 4
	model.add_node(MaxoutDense(nums_units_fc_layers[fc_idx], 
								nb_feature=nb_feature),
								input=last_node_name,
								name=this_node_name)
	last_node_name = this_node_name

	this_node_name = 'bn_fc_%d' % conv_idx
	model.add_node(BatchNormalization(axis=1),
									input=last_node_name,
									name=this_node_name)
	last_node_name = this_node_name

	# 50 dense layers
	num_sparse_units = int(nums_units_fc_layers[num_fc_layers-1]/setting_dict['dim_labels'])
	print 'Add dense layers, %d x %d' % (setting_dict['dim_labels'], num_sparse_units)
	for dense_idx in xrange(setting_dict['dim_labels']):
		
		sparse_node_name = 'sparse_dense_0_%d' % dense_idx
		
		model.add_node(Dense(num_sparse_units, activation='relu'), # use relu for simplicity.
						input=last_node_name,
						name=sparse_node_name)

		output_gate_node_name = 'output_gate_%d' % dense_idx
		model.add_mode(Dense(1, activation='sigmoid'),
						input=sparse_node_name,
						name=output_gate_node_name)

		output_node_name = 'output_%d' % dense_idx
		model.add_output(name=output_node_name,
						input=output_gate_node_name)
	print 'add sparse node: Done '
	return model


'''

def design_residual_model(setting_dict):
	'''residual net using graph'''
	pass



def design_gnu_convnet_model(setting_dict):
	'''It's a hybrid type model - perhaps something like Sander proposed?
	Mainly convnet is done as 1d time-axis, then 
	'''
	is_test = setting_dict["is_test"]
	height = setting_dict["height_image"]
	width = setting_dict["width_image"]
	dropouts = setting_dict["dropouts"]
	num_labels = setting_dict["dim_labels"]
	num_layers = setting_dict["num_layers"]
	activations = setting_dict["activations"] #
	model_type = setting_dict["model_type"] # not used now.
	num_stacks = setting_dict["num_feat_maps"]

	num_fc_layers = setting_dict["num_fc_layers"]
	dropouts_fc_layers = setting_dict["dropouts_fc_layers"]
	nums_units_fc_layers = setting_dict["nums_units_fc_layers"]
	activations_fc_layers = setting_dict["activations_fc_layers"]
	#------------------------------------------------------------------#
	num_channels=1

	image_patch_sizes = [[1,3], [1,4], [1,4],[1,4]]
	pool_sizes = [(1,3), (1,4), (1,4),(2,4)]
	num_stacks = [48,48,64,64]

	model = Sequential()

	for conv_idx in range(len(num_stacks)):
		if conv_idx == 0:
			model.add(Convolution2D(num_stacks[conv_idx], image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
										border_mode='same', 
										input_shape=(1, height, width), 
										init='he_normal'))
		else:
			model.add(Convolution2D(num_stacks[conv_idx], image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
										border_mode='same', 
										init='he_normal'))

		model.add(BatchNormalization())
		model.add(keras.layers.advanced_activations.LeakyReLU(alpha=leakage))
		model.add(MaxPooling2D(pool_size=pool_sizes[conv_idx]))

	model.add(Flatten())

	model.add(Dense(2048, init='he_normal'))
	model.add(Dropout(0.5))
	model.add(keras.layers.advanced_activations.LeakyReLU(alpha=leakage))
	model.add(BatchNormalization())

	model.add(Dense(2048, init='he_normal'))
	model.add(Dropout(0.5))
	model.add(keras.layers.advanced_activations.LeakyReLU(alpha=leakage))
	model.add(BatchNormalization())

	model.add(Dense(num_labels, activation='sigmoid',
								init='he_normal')) 
	return model
		

def design_mfcc_convnet_model(setting_dict):
	height = setting_dict["height_image"]
	width = setting_dict["width_image"]
	num_labels = setting_dict["dim_labels"]
	#------------------------------------------------------------------#
	num_channels=1
	image_patch_sizes = [[height/3,1], [1,1], [1,1], [1,1]]
	pool_sizes = [(1,4), (1,4), (1,4), (1,4)]
	num_stacks = [128, 256, 512, 1024]
	# num_stacks = [48, 48, 64, 96]
	dropouts = setting_dict["dropouts"]
	nb_maxout_feature = setting_dict['nb_maxout_feature']
	activations = setting_dict["activations"] #
	num_fc_layers = setting_dict["num_fc_layers"]
	dropouts_fc_layers = setting_dict["dropouts_fc_layers"]
	nums_units_fc_layers = setting_dict["nums_units_fc_layers"]
	activations_fc_layers = setting_dict["activations_fc_layers"]
	model = Sequential()

	model.add(keras.layers.convolutional.ZeroPadding2D(padding=(0,3), dim_ordering='th', input_shape=(1, height, width)))
	for conv_idx in range(len(num_stacks)):
		if conv_idx == 0:
			print '--> Conv layer for the first layer'
			model.add(Convolution2D(num_stacks[conv_idx], image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
									border_mode='valid', 
									subsample=(height/3, 1),
									init='he_normal'))
		else:
			print '--> Conv layer for the following layer'
			model.add(Convolution2D(num_stacks[conv_idx], image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
									border_mode='same', 
									init='he_normal'))
		if conv_idx == 0: # for first layer
			print '  --> BN for the first layer'
			model.add(BatchNormalization())
		print '  --> activation'
		model.add(get_activation(activations[0]))
		
		if not conv_idx == 0:
			if not dropouts[conv_idx] == 0.0:
				model.add(Dropout(dropouts[conv_idx]))
				print '  --> Add dropout of %f for %d-th conv layer' % (dropouts[conv_idx], conv_idx)
			print '  --> BN'
			model.add(BatchNormalization())
		print '  --> MP'
		model.add(MaxPooling2D(pool_size=pool_sizes[conv_idx]))
	
	model.add(Flatten())
	if setting_dict['maxout']:

		for fc_idx in range(num_fc_layers):
			print '--> Maxout dense'
			model.add(MaxoutDense(nums_units_fc_layers[fc_idx], 
								nb_feature=nb_maxout_feature))

			# Dropout
			if not dropouts_fc_layers[fc_idx] == 0.0:
				model.add(Dropout(dropouts_fc_layers[fc_idx]))
				print ' ---->>Dropout for fc layer, %f' % dropouts_fc_layers[fc_idx]
			print '  --> BN'
			model.add(BatchNormalization())
	else:
		for fc_idx in range(num_fc_layers):
			print '--> Dense'
			model.add(Dense(nums_units_fc_layers[fc_idx], init='he_normal'))
			print '  --> Dropout'
			model.add(Dropout(dropouts_fc_layers[fc_idx]))
			print '  --> Activation'
			model.add(get_activation(activations_fc_layers[0]))
			print '  --> BN'
			model.add(BatchNormalization())			

	model.add(Dense(num_labels, activation='sigmoid',
								init='he_normal')) 
	return model
	
'''
#--------------------------------------------#

def design_1d_time_convnet_model(setting_dict):
	is_test = setting_dict["is_test"]
	height = setting_dict["height_image"]
	width = setting_dict["width_image"]
	dropouts = setting_dict["dropouts"]
	num_labels = setting_dict["dim_labels"]
	num_layers = setting_dict["num_layers"]
	activations = setting_dict["activations"] #
	model_type = setting_dict["model_type"] # not used now.
	num_stacks = setting_dict["num_feat_maps"]

	num_fc_layers = setting_dict["num_fc_layers"]
	dropouts_fc_layers = setting_dict["dropouts_fc_layers"]
	nums_units_fc_layers = setting_dict["nums_units_fc_layers"]
	activations_fc_layers = setting_dict["activations_fc_layers"]
	#------------------------------------------------------------------#
	num_channels=1

	if setting_dict['tf_type'] in ['cqt', 'stft', 'melgram']:
		image_patch_sizes = [1,5]*2 + [1,3]*(num_layers-1)
		pool_sizes = [(2,2)]*num_layers
	elif setting_dict['tf_type'] == 'mfcc':
		image_patch_sizes = [[height,1]]*num_layers
		pool_sizes = [(1,2)]*num_layers	

	#-------------------------------#
	# prepre modules
	model = Sequential()
	#[Convolutional Layers]
	for conv_idx in xrange(num_layers):
		if setting_dict['regulariser'][conv_idx] in [None, 0.0]:
			W_regularizer = None
		else:
			if setting_dict['regulariser'][conv_idx][0] == 'l2':
				W_regularizer=keras.regularizers.l2(setting_dict['regulariser'][conv_idx][1])
				print ' ---->>prepare l2 regulariser of %f for %d-th conv layer' % (setting_dict['regulariser'][conv_idx][1], conv_idx)
			elif setting_dict['regulariser'][conv_idx][0] == 'l1':
				W_regularizer=keras.regularizers.l1(setting_dict['regulariser'][conv_idx][1])
				print ' ---->>prepare l1 regulariser of %f for %d-th conv layer' % (setting_dict['regulariser'][conv_idx][1], conv_idx)

		# add conv layer
		if conv_idx == 0:
			print ' ---->>First conv layer is being added!'
			model.add(Convolution2D(num_stacks[conv_idx], image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
									border_mode='same', 
									input_shape=(num_channels, height, width), 
									W_regularizer=W_regularizer,
									init='he_normal'))
		else:
			print ' ---->>%d-th conv layer is being added ' % conv_idx
			model.add(Convolution2D(num_stacks[conv_idx], image_patch_sizes[conv_idx][0], image_patch_sizes[conv_idx][1], 
									border_mode='same',
									W_regularizer=W_regularizer,
									init='he_normal'))
		# add BN
		if setting_dict['BN']:
			print ' ---->>BN is added for conv layer'
			model.add(BatchNormalization())

		# add activation
		print ' ---->>%s activation is added.' % activations[conv_idx]
		if activations[conv_idx] == 'relu':
			model.add(Activation('relu'))
		elif activations[conv_idx] == 'lrelu':
			model.add(keras.layers.advanced_activations.LeakyReLU(alpha=leakage))
		elif activations[conv_idx] == 'prelu':
			model.add(keras.layers.advanced_activations.PReLU())
		elif activations[conv_idx] == 'elu':
			model.add(keras.layers.advanced_activations.ELU(alpha=1.0))
		else:
			print ' ---->>No activation here? No!'

		# add pooling	
		print ' ---->>MP with (2,2) strides is added', pool_sizes[conv_idx]
		model.add(MaxPooling2D(pool_size=pool_sizes[conv_idx], strides=(2, 2)))
		# add dropout
		if not dropouts[conv_idx] == 0.0:
			model.add(Dropout(dropouts[conv_idx]))
			print ' ---->>Add dropout of %f for %d-th conv layer' % (dropouts[conv_idx], conv_idx)
	#[Fully Connected Layers]
	model.add(Flatten())
	for fc_idx in xrange(num_fc_layers):
		if setting_dict['regulariser_fc_layers'][fc_idx] is None:
			W_regularizer = None
		else:
			if setting_dict['regulariser_fc_layers'][fc_idx][0] == 'l2':
				W_regularizer=keras.regularizers.l2(setting_dict['regulariser_fc_layers'][fc_idx][1])
			elif setting_dict['regulariser_fc_layers'][fc_idx][0] == 'l1':
				W_regularizer=keras.regularizers.l1(setting_dict['regulariser_fc_layers'][fc_idx][1])
		# dense layer
		if not dropouts_fc_layers[fc_idx] == 0.0:
			print ' ---->>Dense layer is added with dropout of %f.' % dropouts_fc_layers[fc_idx]
			model.add(Dense(nums_units_fc_layers[fc_idx],init='he_normal'))
		
		else:
			print ' ---->>Dense layer is added with regularizer.'
			model.add(Dense(nums_units_fc_layers[fc_idx], W_regularizer=W_regularizer,
													init='he_normal'))
		
		# Activations
		print ' ---->>%s activation is added' % activations_fc_layers[fc_idx]
		if activations_fc_layers[fc_idx] == 'relu':
			model.add(Activation('relu'))
		elif activations_fc_layers[fc_idx] == 'lrelu':
			model.add(keras.layers.advanced_activations.LeakyReLU(alpha=leakage))
		elif activations_fc_layers[fc_idx] == 'prelu':
			model.add(keras.layers.advanced_activations.PReLU())
		elif activations_fc_layers[fc_idx] == 'elu':
			model.add(keras.layers.advanced_activations.ELU(alpha=1.0))
		else:
			print ' ---->>No activation here? No!'
		# Dropout
		if not dropouts_fc_layers[fc_idx] == 0.0:
			model.add(Dropout(dropouts_fc_layers[fc_idx]))
		# BN
		if setting_dict['BN_fc_layers']:
			print ' ---->>BN for dense is added'
			model.add(BatchNormalization())

	#[Output layer]
	if setting_dict["output_activation"]:
		print ' ---->>Output dense and activation is: %s with %d units' % (setting_dict["output_activation"], num_labels)
		model.add(Dense(num_labels, activation=setting_dict["output_activation"],
									init='he_normal')) 
	else:
		print ' ---->>Output dense and activation: linear with %d units' % num_labels
		model.add(Dense(num_labels, activation='linear')) 

	return model
'''
