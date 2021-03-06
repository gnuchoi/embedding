
from constants import *
from environments import *
from training_settings import *

import os
import cPickle as cP
import time
import sys
import numpy as np
import adjspecies
import pprint	
import h5py
from collections import defaultdict
from keras.utils import np_utils

import pdb
import hdf5matrix

		


class File_Manager():
	def __init__(self):
		self.track_ids = cP.load(open(PATH_DATA + FILE_DICT["track_ids"], 'r')) # # all 9320 ids [440, 444, 447, 646,...]
		self.id_path = cP.load(open(PATH_DATA + FILE_DICT["id_path"], 'r')) # dict, {440 : 310829-10.01.wav, ...}
		self.filenum = len(self.track_ids)
		print "file manager init with %d track ids and %d element dictionary " % (self.filenum, len(self.id_path))
	'''
	def load_src(self, ind):
		import librosa
		if ind > len(self.track_ids):
			print 'wrong ind -- too large: %d' % ind
		path = self.id_path[self.track_ids[ind]]
		return librosa.load(path, sr=SR, mono=False)
	'''
	def load(self, ind, data_type):
		if data_type == 'cqt':
			return self.load_cqt(ind)
		elif data_type == 'stft':
			return self.load_stft(ind)
		elif data_type =='mfcc':
			return self.load_mfcc(ind)
		elif data_type == 'chroma':
			return self.load_chroma(ind)
		elif data_type == 'melgram':
			return self.load_melgram(ind)
		else:
			print 'wrong data type input in file_manager.load()'
			raise ValueError
		# make more for mfcc, chroma, ... 

	def load_melgram(self, ind):
		return np.load(PATH_MELGRAM + str(self.track_ids[ind]) + '.npy')

	def load_mfcc(self, ind):
		return np.load(PATH_MFCC + str(self.track_ids[ind]) + '.npy')

	def load_chroma(self, ind):
		return np.load(PATH_CHROMA + str(self.track_ids[ind]) + '.npy')

	def load_stft(self, ind):
		return np.load( PATH_STFT + str(self.track_ids[ind]) + '.npy')

	def load_cqt(self, ind):
		return np.load( PATH_CQT + str(self.track_ids[ind]) + '.npy')

	def split_inds(self, num_folds):
		"""returns index of train/valid/test songs"""
		if num_folds < 3:
			return "wrong num_folds, should be >= 3"
		num_test = self.filenum / num_folds
		num_valid = self.filenum / num_folds
		num_train = self.filenum - (num_test + num_valid)

		rand_filename = PATH_DATA +("random_permutation_%d_%d.npy" % (num_folds, self.filenum))
		if os.path.exists(rand_filename):
			print 'File manager will use a previously made random permutation file'
			rand_inds = np.load(rand_filename)
		else:
			print 'File manager will use a new random permutation file'
			rand_inds = np.random.permutation(self.filenum)
			np.save(rand_filename, rand_inds)

		return rand_inds[0:num_train], rand_inds[num_train:num_train+num_valid], rand_inds[num_train+num_valid:]





def get_input_output_set(file_manager, indices, truths, tf_type, max_len_freq=256, width_image=256, clips_per_song=0):
	"""indices: list consists of integers between [0, 9320], 
	usually it is one of train_inds, valid_inds, test_inds.
	it returns data_x and data_y.
	file_manager: an instance of File_Manager class.
	type = 'stft' or 'cqt', determines which function file_manager should use
	clips_per_song= integer, 0,1,2,...N: decide how many clips it will take from a song

	"""
	# first, set the numbers
	if tf_type=='stft':
		tf_representation = file_manager.load_stft(0)[:,:,0:1]
		len_freq, num_fr_temp, num_ch = tf_representation.shape # 513, 6721, 2 for example.

	elif tf_type=='cqt':
		tf_representation = file_manager.load_cqt(0)[:,:,0:1]
		len_freq, num_fr_temp, num_ch = tf_representation.shape # 513, 6721, 2 for example.
	if len_freq > max_len_freq:
		len_freq = max_len_freq
	else:
		print 'You set max_len_freq as %d, but it doesnt have that many frequency bins, \
						 so it will use all it has, which is %d.' % (max_len_freq, len_freq)

	num_labels = truths.shape[1]
	width = width_image
	print '   -- check number of all data --'
	num_data = 0
	if clips_per_song==0:
		for i in indices:
			if tf_type=='stft':
				tf_representation = file_manager.load_stft(i)[:,:,0:1]
			elif tf_type=='cqt':
				tf_representation = file_manager.load_cqt(i)[:,:,0:1]
			num_data += tf_representation.shape[1] / width
	else:
		num_data = len(indices) * clips_per_song
	print '   -- check:done, num_data is %d --' % num_data

	ret_x = np.zeros((num_data, num_ch, len_freq, width)) # x : 4-dim matrix, num_data - num_channel - height - width
	ret_y = np.zeros((num_data, num_labels)) # y : 2-dum matrix, num_data - labels (or whatever)

	if tf_type not in ['stft', 'cqt']:
		print "wront type in get_input_output_set, so failed to prepare data."

	data_ind = 0
	for i in indices: # for every song
		# print i
		if tf_type == 'stft':
			tf_representation = 10*np.log10(np.abs(file_manager.load_stft(i)[:,:,0:1]))
		elif tf_type=='cqt':
			tf_representation = file_manager.load_cqt(i)[:,:,0:1]

		tf_representation = np.expand_dims(tf_representation[:len_freq, :, :], axis=3) # len_freq, num_fr, num_ch, nothing(#data). -->
		# print 'expending done'
		num_fr = tf_representation.shape[1]
		tf_representation = tf_representation.transpose((3, 2, 0, 1)) # nothing, num_ch, len_freq, num_fr
		#print 'transpose done'
		if clips_per_song == 0:
			for j_ind in xrange(num_fr/len_freq):
				ret_x[data_ind, :, :, :] = tf_representation[:, :, :, j_ind*width: (j_ind+1)*width]
				ret_y[data_ind, :] = np.expand_dims(truths[i,:], axis=1).transpose()
				data_ind += 1
		else:
			for j_in in xrange(clips_per_song):
				frame_from = 43*10 + j_in*((num_fr-width_image-43*10*2)/clips_per_song) # remove 1-sec from both ends
				frame_to = frame_from + width_image

				ret_x[data_ind, :, :, :] = tf_representation[:, :, :, frame_from:frame_to]
				ret_y[data_ind, :] = np.expand_dims(truths[i,:], axis=1).transpose()
				data_ind += 1
	return ret_x, ret_y

def load_all_inputs(num_fold=10, clips_per_song=3, tf_type=None, usage_ratio=1.0):
	''''''
	def load_x(inds, clips_per_song, tf_type):
		file_manager = File_Manager()
		num_songs = len(inds)
		data_example = np.load(PATH_HDF + 'temp_' + tf_type + '/' + str(file_manager.track_ids[0]) +'.npy')
		height=data_example.shape[0]
		width=data_example.shape[1]
		if height > 256:
			cut_high_freq = True
			height = 256
		else:
			cut_high_freq = False
		ret = np.zeros((num_songs*clips_per_song, 1, height, width))
		for data_idx, song_idx in enumerate(inds):
			data_here = np.load(PATH_HDF + 'temp_' + tf_type + '/' + str(file_manager.track_ids[song_idx]) +'.npy')
			if cut_high_freq:
				data_here = data_here[:height, :, :]
			for clip_idx in xrange(clips_per_song):
				ret[data_idx + clip_idx*num_songs, 0,:,:] = data_here[:, :, clip_idx]
		return ret

	def trim_list(lst, ratio):
		return lst[:int(len(lst)*ratio)]

	file_manager = File_Manager()
	train_inds, valid_inds, test_inds = file_manager.split_inds(num_folds=10)
	train_inds = trim_list(train_inds, usage_ratio)
	valid_inds = trim_list(valid_inds, usage_ratio)
	test_inds = trim_list(test_inds, usage_ratio)

	return load_x(train_inds, clips_per_song, tf_type), \
			load_x(valid_inds, clips_per_song, tf_type), \
			load_x(test_inds, clips_per_song, tf_type)


def load_all_labels(n_dim=None, num_fold=10, clips_per_song=3, usage_ratio=1.0):
	'''return numpy lasbel of all labels'''
	def load_y(inds, n_dim, clips_per_song):
		num_songs = len(inds)
		labels = np.load(PATH_DATA + (FILE_DICT["mood_latent_tfidf_matrix"] % n_dim))
		ret = np.zeros((num_songs*clips_per_song, n_dim))
		for data_idx, song_idx in enumerate(inds):
			for clip_idx in xrange(clips_per_song):
				ret[data_idx + clip_idx*num_songs, :] = labels[song_idx, :]
		return ret

	def trim_list(lst, ratio):
		return lst[:int(len(lst)*ratio)]

	file_manager = File_Manager()
	train_inds, valid_inds, test_inds = file_manager.split_inds(num_folds=10)

	train_inds = trim_list(train_inds, usage_ratio)
	valid_inds = trim_list(valid_inds, usage_ratio)
	test_inds = trim_list(test_inds, usage_ratio)

	return load_y(train_inds, n_dim, clips_per_song), \
			load_y(valid_inds, n_dim, clips_per_song), \
			load_y(test_inds, n_dim, clips_per_song)

def load_all_sets_from_hdf(tf_type=None, n_dim=None, task_cla=False):
	'''using hdf. perhaps you should set PATH_HDF_LOCAL for the machine you're using.
	tf_type: cqt, stft, mfcc, chroma. ''
	task = 'reg', 'cla'
	for any tf_type, any post-processing is not required except standardization.
	'''
	def normalizer_cqt(input_data):
		global_mean = -28.3472 # computed from the whole data for cqt
		global_std  = 6.59574
		return (input_data - global_mean) / global_std

	def normalizer_stft(input_data):	
		global_mean = -2.01616 # should be mended with STFT values
		global_std  = 9.23697
		return (input_data - global_mean) / global_std

	def normalizer_mfcc(input_data):
		global_mean = 2.1356969
		global_std = 16.260582
		return (input_data - global_mean) / global_std		

	if tf_type is None:
		tf_type = 'stft'
	if n_dim is None:
		n_dim == 4
	label_num = 'label'+str(n_dim)
	if task_cla == True:
		suffix = '_cla'
	else:
		suffix = ''

	if tf_type == 'stft':
		normalizer = normalizer_stft
	elif tf_type == 'cqt':
		normalizer = normalizer_cqt
	elif tf_type == 'mfcc':
		normalizer = normalizer_mfcc
	else:
		normalizer = None
	'''
	file_train = h5py.File(PATH_HDF_LOCAL + 'data_train.h5', 'r')
	file_valid = h5py.File(PATH_HDF_LOCAL + 'data_valid.h5', 'r')
	file_test  = h5py.File(PATH_HDF_LOCAL + 'data_test.h5', 'r')

	return file_train[tf_type], file_train[label_num], \
			file_valid[tf_type], file_valid[label_num], \
			file_test[tf_type],  file_test[label_num]
	'''
	
	n_train_examples = 22368
	n_valid_examples = 2796
	n_test_examples	 = 2796

	# ??? using hdf5matrix. [1]
	# train_x = hdf5matrix.HDF5Matrix(PATH_HDF_LOCAL + 'data_train.h5', tf_type,					 0, n_train_examples, normalizer=normalizer)
	# train_y = hdf5matrix.HDF5Matrix(PATH_HDF_LOCAL + 'data_train.h5', 'label'+str(n_dim)+suffix, 0, n_train_examples, normalizer=normalizer)
	
	# valid_x = hdf5matrix.HDF5Matrix(PATH_HDF_LOCAL + 'data_valid.h5', tf_type,					 0, n_valid_examples, normalizer=normalizer)
	# valid_y = hdf5matrix.HDF5Matrix(PATH_HDF_LOCAL + 'data_valid.h5', 'label'+str(n_dim)+suffix, 0, n_valid_examples, normalizer=normalizer)
	
	# test_x  = hdf5matrix.HDF5Matrix(PATH_HDF_LOCAL + 'data_test.h5',  tf_type, 				 0, n_test_examples, normalizer=normalizer)
	# test_y  = hdf5matrix.HDF5Matrix(PATH_HDF_LOCAL + 'data_test.h5',  'label'+str(n_dim)+suffix, 0, n_test_examples, normalizer=normalizer)
	
	# return train_x, valid_x, test_x
	# or, [2]
	file_train = h5py.File(PATH_HDF_LOCAL + 'data_train.h5', 'r')
	file_valid = h5py.File(PATH_HDF_LOCAL + 'data_valid.h5', 'r')
	file_test  = h5py.File(PATH_HDF_LOCAL + 'data_test.h5', 'r')
	return file_train[tf_type], file_valid[tf_type], file_test[tf_type]



def load_all_sets(label_matrix, hyperparams):
	'''load files using numpy array i.e. batch into memory.
	It can load subset when it's debug. '''
	if hyperparams['debug']:
		num_train_songs = 30
		num_test_songs = 30
	else:
		num_train_songs = 1000
		num_test_songs = 300

	clips_per_song = 3
	tf_type = hyperparams['tf_type']
	
	file_manager = File_Manager()

	train_inds, valid_inds, test_inds = file_manager.split_inds(num_folds=5)
	num_songs_train = min(num_train_songs, len(train_inds))
	
	train_inds = train_inds[:num_songs_train]
	valid_inds = valid_inds[:num_test_songs]
	test_inds  = test_inds [:num_test_songs]
	print "--- Lets go! ---"
	start = time.time()
	train_x, train_y = get_input_output_set(file_manager, train_inds, truths=label_matrix,
											tf_type=tf_type, 
											max_len_freq=TR_CONST["height_image"], 
											width_image=TR_CONST["width_image"], 
											clips_per_song=TR_CONST["clips_per_song"])
	until = time.time()
	print "--- train data prepared; %d clips from %d songs, took %d seconds to load---" \
									% (len(train_x), len(train_inds), (until-start) )
	start = time.time()
	valid_x, valid_y = get_input_output_set(file_manager, valid_inds, truths=label_matrix, 
											tf_type=tf_type, 
											max_len_freq=TR_CONST["height_image"], 
											width_image=TR_CONST["width_image"], 
											clips_per_song=TR_CONST["clips_per_song"])
	until = time.time()
	print "--- valid data prepared; %d clips from %d songs, took %d seconds to load---" \
									% (len(valid_x), len(valid_inds), (until-start) )
	start = time.time()
	test_x,  test_y  = get_input_output_set(file_manager, test_inds, truths=label_matrix, 
											tf_type=tf_type, 
											max_len_freq=TR_CONST["height_image"], 
											width_image=TR_CONST["width_image"], 
											clips_per_song=TR_CONST["clips_per_song"])
	until = time.time()
	print "--- test data prepared; %d clips from %d songs, took %d seconds to load---" \
									% (len(test_x), len(test_inds), (until-start) )
	
	if tf_type == 'cqt':
		global_mean = -28.3472 # computed from the whole data for cqt
		global_std  = 6.59574
	# 	print 'NO'*10000000
	elif tf_type == 'stft':
		global_mean = -2.01616 # should be mended with STFT values
		global_std  = 9.23697


	train_x = (train_x - global_mean)/global_std	
	valid_x = (valid_x - global_mean)/global_std
	test_x  = (test_x - global_mean) /global_std

	return train_x, train_y, valid_x, valid_y, test_x, test_y


def log_amplitude(S):
	'''copy and paste of librosa.core.logamplitude
	with the default values.'''
	ref_power=1.0
	amin=1e-10
	top_db=80.0
	magnitude = np.abs(S)
	__ref = np.abs(ref_power)
	log_spec = 10.0 * np.log10(np.maximum(amin, magnitude))
	return np.maximum(log_spec, log_spec.max() - top_db)

def inv_log_amplitude(tf_representation):
	return 10**(0.05*tf_representation)

def continuous_to_categorical(y):
	'''input y: continuous label, (N,M) array.
	return: (N,M) array.
	'''
	maxind = np.argmax(y, axis=1)
	return np_utils.to_categorical(maxind, y.shape[1])

def append_history(total_history, local_history):
	'''local history is a dictionary,
	key:value == string:dictionary.

	key: loss, vall_loss, batch, size
	Therefore total_history has the same keys and append the values.
	'''

	for key in local_history:
		if key not in total_history:
			total_history[key] = []
		total_history[key] = total_history[key] + local_history[key]



