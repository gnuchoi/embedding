import platform
import os
import sys

device_name = platform.node()

if device_name.endswith('eecs.qmul.ac.uk') or device_name in ['octave', 'big-bird']:
	isServer = True
	isMac = False
	isMsi = False

else:
	isServer = False
	if device_name == "KChoiMBPR2013.local":
		isMac = True
		isMsi = False


if isServer:
	print "THIS IS A SERVER NAMED %s" % device_name
	PATH_ILM = '/import/c4dm-01/ilm10k-dataset/'
	PATH_ILM_ACT = PATH_ILM + 'act-coordinates/'
	PATH_ILM_AUDIO = PATH_ILM + 'ilmaudio/'
	PATH_ILM_META = PATH_ILM + 'metadata/'

	PATH_HOME = "/homes/kc306/"
	PATH_WORK = PATH_HOME + "embedding/"
	PATH_DATA = PATH_WORK + "data/"
	PATH_MODEL= PATH_WORK + 'keras_models/'
	PATH_SENTI= PATH_WORK + "sentiment/" 

	PATH_IMAGES=PATH_WORK + 'images/'

	PATH_FIGURE = PATH_WORK + 'figures/'
	PATH_RESULTS= PATH_WORK + 'results/'

	PATH_WIKI = "/import/c4dm-datasets/Wikipedia_dump/"

	PATH_STFT = '/import/c4dm-04/keunwoo/ilm10k_audio_transformed/' + 'STFT/'
	PATH_CQT  = '/import/c4dm-04/keunwoo/ilm10k_audio_transformed/' + 'CQT/'

	for path in [PATH_DATA, PATH_MODEL, PATH_SENTI, PATH_IMAGES, PATH_FIGURE, PATH_RESULTS]:
		if not os.path.exists(path):
			os.mkdir(path)

	sys.path.append(PATH_HOME + 'modules/' + 'librosa/')
else:
	PATH_DATA = 'data/'