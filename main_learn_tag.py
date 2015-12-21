""" To predict tags! using ilm10k data, stft or cqt representation, 
"""
#import matplotlib
#matplotlib.use('Agg')
from constants import *
from environments import *
import numpy as np

import keras
import os
import pdb
import my_keras_models
import my_keras_utils
import cPickle as cP
import time
import sys
import my_plots

class File_Manager():
	def __init__(self):
		self.track_ids = cP.load(open(PATH_DATA + FILE_DICT["track_ids"], 'r')) #list, 9320
		self.id_path = cP.load(open(PATH_DATA + FILE_DICT["id_path"], 'r')) #dict, 9320
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
			rand_inds = np.load(rand_filename)
		else:
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
		tf_representation = file_manager.load_stft(0)
		len_freq, num_fr_temp, num_ch = tf_representation.shape # 513, 6721, 2 for example.

	elif tf_type=='cqt':
		tf_representation = file_manager.load_cqt(0)
		len_freq, num_fr_temp, num_ch = tf_representation.shape # 513, 6721, 2 for example.
	if len_freq > max_len_freq:
		len_freq = max_len_freq
	else:
		print 'You set max_len_freq as %d, but it doesnt have that many frequency bins, so it will use all it has, which is %d.' % (max_len_freq, len_freq)

	num_labels = truths.shape[1]
	width = width_image
	print '   -- check number of all data --'
	num_data = 0
	if clips_per_song==0:
		for i in indices:
			if tf_type=='stft':
				tf_representation = file_manager.load_stft(i)
			elif tf_type=='cqt':
				tf_representation = file_manager.load_cqt(i)
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
			tf_representation = np.abs(file_manager.load_stft(i))
		elif tf_type=='cqt':
			tf_representation = file_manager.load_cqt(i)

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

def load_all_sets(label_matrix, clips_per_song, num_train_songs=100, tf_type=None):
	if not tf_type:
		print '--- tf_type not specified, so stft is assumed. ---'
		tf_type = 'stft'
	if tf_type not in ['stft', 'cqt']:
		print '--- wrong tf_type:%s, it should be either stft or cqt---' % tf_type
		return

	file_manager = File_Manager()

	train_inds, valid_inds, test_inds = file_manager.split_inds(num_folds=5)
	num_songs_train = min(num_train_songs, len(train_inds))
	
	train_inds = train_inds[0:num_songs_train]
	valid_inds = valid_inds[:30]
	test_inds  = test_inds [:30]
	print "--- Lets go! ---"
	start = time.time()
	train_x, train_y = get_input_output_set(file_manager, train_inds, truths=label_matrix, tf_type=tf_type, max_len_freq=256, width_image=256, clips_per_song=clips_per_song)
	until = time.time()
	print "--- train data prepared; %d clips from %d songs, took %d seconds to load---" % (len(train_x), len(train_inds), (until-start) )
	start = time.time()
	valid_x, valid_y = get_input_output_set(file_manager, valid_inds, truths=label_matrix, tf_type=tf_type, max_len_freq=256, width_image=256, clips_per_song=clips_per_song)
	until = time.time()
	print "--- valid data prepared; %d clips from %d songs, took %d seconds to load---" % (len(valid_x), len(valid_inds), (until-start) )
	start = time.time()
	test_x,  test_y  = get_input_output_set(file_manager, test_inds, truths=label_matrix, tf_type=tf_type, max_len_freq=256, width_image=256, clips_per_song=clips_per_song)
	until = time.time()
	print "--- test data prepared; %d clips from %d songs, took %d seconds to load---" % (len(test_x), len(test_inds), (until-start) )
	
	if tf_type == 'cqt':
		global_mean = -61.25 # computed from the whole data for cqt
		global_std  = 14.36
	elif tf_type == 'stft':
		global_mean = -61.25 # should be mended with STFT values
		global_std  = 14.36

	train_x = (train_x - global_mean)/global_std	
	valid_x = (valid_x - global_mean)/global_std
	test_x  = (test_x - global_mean) /global_std

	return train_x, train_y, valid_x, valid_y, test_x, test_y



def print_usage_and_die():
	print 'python filename num_of_epoch(int) num_of_train_song(int) tf_type model_type num_of_layers'
	print 'ex) $ python main_learn_tag.py 200 5000 cqt vgg 4 5 6'
	sys.exit()

if __name__ == "__main__":
	
	if len(sys.argv) < 7:
		print_usage_and_die()

	nb_epoch = int(sys.argv[1])
	num_train_songs = int(sys.argv[2])
	tf_type = sys.argv[3]
	model_type = sys.argv[4]
	if sys.argv[5].lower() in ['reg', 'regression']:
		isRegression = True
		isClassification = False
	elif sys.argv[5].lower() in ['cla', 'classification']:
		isRegression = False
		isClassification = True

	num_layers_list = [int(sys.argv[i]) for i in xrange(6, len(sys.argv))]
	print '--- num_layers are ---'
	print num_layers_list
	# nb_epoch = 1
	clips_per_song = 3
	# label matrix
	dim_latent_feature = 3
	# label_matrix_filename = (FILE_DICT["mood_latent_matrix"] % dim_latent_feature)
	label_matrix_filename = (FILE_DICT["mood_latent_tfidf_matrix"] % dim_latent_feature) # tfidf is better!
	
	if os.path.exists(PATH_DATA + label_matrix_filename):
		label_matrix = np.load(PATH_DATA + label_matrix_filename) #np matrix, 9320-by-100
	else:
		"print let's cook the mood-latent feature matrix"
		import main_prepare
		mood_tags_matrix = np.load(PATH_DATA + label_matrix_filename) #np matrix, 9320-by-100
		label_matrix = main_prepare.get_LDA(X=mood_tags_matrix, num_components=k, show_topics=False)
		np.save(PATH_DATA + label_matrix_filename, W)
	print 'size of mood tag matrix:'
	print label_matrix.shape

	# load dataset
	print "I'll take %d clips for each song." % clips_per_song
	train_x, train_y, valid_x, valid_y, test_x, test_y = load_all_sets(label_matrix=label_matrix, clips_per_song=clips_per_song, num_train_songs=num_train_songs, tf_type=tf_type)
	moodnames = cP.load(open(PATH_DATA + FILE_DICT["moodnames"], 'r')) #list, 100
	# learning_id =  str(np.random.randint(999999))
	if isClassification:
		train_y = my_keras_utils.continuous_to_categorical(train_y)
		valid_y = my_keras_utils.continuous_to_categorical(valid_y)
		test_y  = my_keras_utils.continuous_to_categorical(test_y)

	for num_layers in num_layers_list:
		#prepare model

		model_name = model_type + '_dim'+str(dim_latent_feature)+'_'+sys.argv[1] +'epochs_' + sys.argv[2] + 'songs' + sys.argv[3] + '_' + str(num_layers) + 'layers'
		model_name_dir = model_name + '/'
		fileout = model_name + '_results'
		print "="*60
		print model_name
		print "="*60

		if not os.path.exists(PATH_MODEL + model_name_dir):
			os.mkdir(PATH_MODEL + model_name_dir)
		if not os.path.exists(PATH_IMAGES + model_name_dir):
			os.mkdir(PATH_IMAGES + model_name_dir)
		start = time.time()
		print "--- going to build a keras model with height:%d, width:%d, num_labels:%d" % (train_x.shape[2], train_x.shape[3], train_y.shape[1])
	 	'''
	 	if tf_type == 'stft':
	 		model = my_keras_models.build_convnet_model(height=train_x.shape[2], width=train_x.shape[3], num_labels=train_y.shape[1], num_layers=num_layers)
	 	else:
	 		model = my_keras_models.build_strict_convnet_model(height=train_x.shape[2], width=train_x.shape[3], num_labels=train_y.shape[1], num_layers=num_layers, model_type=model_type)
	 		# model = my_keras_models.build_overfitting_convnet_model(height=train_x.shape[2], width=train_x.shape[3], num_labels=train_y.shape[1], num_layers=num_layers)
	 	'''
	 	if isRegression:
	 		print '--- ps. this is a regression task. ---'
	 		model = my_keras_models.build_regression_convnet_model(height=train_x.shape[2], width=train_x.shape[3], num_labels=train_y.shape[1], num_layers=num_layers, model_type=model_type)
		else:
			print '--- ps. this is a classification task. ---'
			 model = my_keras_models.build_classification_convnet_model(height=train_x.shape[2], width=train_x.shape[3], num_labels=train_y.shape[1], num_layers=num_layers, model_type=model_type)		
	 	until = time.time()
	 	print "--- keras model was built, took %d seconds ---" % (until-start)

		#prepare callbacks
		checkpointer = keras.callbacks.ModelCheckpoint(filepath=PATH_MODEL + model_name_dir +"weights.{epoch:02d}-{val_loss:.2f}.hdf5", verbose=1, save_best_only=False)
		weight_image_saver = my_keras_utils.Weight_Image_Saver(model_name_dir)
		history = my_keras_utils.History_Regression_Val()
		early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, verbose=0)
		#train!
		my_plots.save_model_as_image(model, save_path=PATH_IMAGES+model_name_dir, filename_prefix='INIT_', normalize='local', mono=False)
		predicted = model.predict(train_x, batch_size=40)
		np.save(PATH_RESULTS + fileout + '_predicted_and_truths_init.npy', [predicted, train_y])

		model.fit(train_x, train_y, validation_data=(valid_x, valid_y), batch_size=32, nb_epoch=nb_epoch, show_accuracy=False, verbose=1, callbacks=[history, early_stopping, weight_image_saver, checkpointer])
		# model.fit(train_x, train_y, validation_data=(valid_x, valid_y), batch_size=40, nb_epoch=nb_epoch, show_accuracy=False, verbose=1, callbacks=[history, early_stopping, weight_image_saver])
		#test
		loss_testset = model.evaluate(test_x, test_y, show_accuracy=False)
		predicted = model.predict(test_x, batch_size=40)
		#save results
		model.save_weights(PATH_MODEL + model_name_dir + ('final_after_%d.keras' % nb_epoch), overwrite=True) 
		
		np.save(PATH_RESULTS + fileout + '_history.npy', history.val_losses)
		np.save(PATH_RESULTS + fileout + '_loss_testset.npy', loss_testset)
		np.save(PATH_RESULTS + fileout + '_predicted_and_truths_final.npy', [predicted, test_y])
		
		my_plots.export_history(history.losses, history.val_losses, acc=None, val_acc=None, out_filename=PATH_RESULTS + fileout + '.png')
		my_plots.save_model_as_image(model, save_path=PATH_IMAGES+model_name_dir, filename_prefix='', normalize='local', mono=False)
		
	# figure_filepath = PATH_FIGURE + model_name + '_history.png'
