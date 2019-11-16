import librosa
import numpy as np
import time
import pickle
import scipy
from scipy import signal


def read_all_music_benchmark(base_path, classifications, window_length):
    """
    Read the songs in the Benchmark dataset that fall into the given classifications.
    There are 120 (blues) + 300 (hip-pop) + 319 (jazz) + 116 (pop) + 504 (rock) = 1359 songs.
    Each song is around 10 seconds long and the sample rate is 44100 Hz.
    The samples are resampled to be 22050 Hz.
    :param base_path: path to the dataset.
    :param classifications: the classifications to load.
    :param window_length: the number of points in the output window.
    :return: the music data, the labels for each music.
    """
    print('Loading files for the Benchmark dataset.')
    benchmark_sample_rate = 44100
    expected_music_length = 10
    return read_all_music(base_path, classifications, benchmark_sample_rate, expected_music_length, window_length)


def read_all_music_gtzan(base_path, classifications, window_length):
    """
    Read the songs in the GTZAN dataset that fall into the given classifications.
    There are 100 * 5 = 500 songs.
    Each song is around 30 seconds long and the sample rate is 22050 Hz.
    :param base_path: path to the GTZAN dataset.
    :param classifications: the classifications to load.
    :param window_length: the number of points in the output window.
    :return: the music data, the labels for each music.
    """
    print('Loading files for the GTZAN dataset.')
    gtzan_sample_rate = 22050
    expected_music_length = 30
    return read_all_music(base_path, classifications, gtzan_sample_rate, expected_music_length, window_length)


def read_all_music(base_path, classifications, sample_rate, expected_music_length, window_length):
    """
    Read the songs in the dataset specified by the base path and which fall into the given classifications.
    Some samples are cut to be a little shorter to ensure that the spectrograms have the same dimensions.
    :param base_path: path to the dataset.
    :param classifications:  the classifications to load.
    :param sample_rate: sample rate of the songs.
    :param expected_music_length: expected music lengths in seconds.
    :param window_length: the number of points in the output window.
    :return: the music data, the labels for each music.
    """
    dataset = []
    labels = []

    # (len(x) - window_length) // (window_length - window_length//8) + 1 = spectrogram number of columns
    window_length_to_max_sample_length = {256: 220223, 1024: 220543}
    upper_bound = window_length_to_max_sample_length[window_length]

    # todo: remove debugging code
    max_length = -1
    min_length = 100000000

    counter = 0
    for i in range(len(classifications)):
        classification = classifications[i]
        path_to_classification = base_path + classification
        print('Loading files under', path_to_classification)
        files = librosa.util.find_files(path_to_classification, ext=['mp3', 'wav'])
        files = np.asarray(files)

        for path_to_music in files:
            x, sample_rate = librosa.load(path_to_music, sr=sample_rate)
            if sample_rate != 22050:
                # resample the sample if the sample rate is not 22050 Hz.
                x = librosa.resample(x, sample_rate, 22050)
            len_x = len(x)
            if expected_music_length == 10 and len_x > upper_bound:
                # need to ensure the length is less than upper_bound to have spectrograms of the same dimension
                x = x[0:upper_bound]
            elif expected_music_length == 30 and len_x > upper_bound*3:
                # need to ensure the length is less than upper_bound * 3 to have spectrograms of the same dimension
                x = x[0:upper_bound*3]

            # todo: remove debugging code
            if len_x > max_length:
                max_length = len_x
                print('warning 1: max_length is', max_length, 'at', path_to_music)
            if len_x < min_length:
                min_length = len_x
                print('warning 2: min_length is', min_length, 'at', path_to_music)

            dataset.append(x)
            labels.append(i)
            counter += 1
    try:
        dataset = np.array(dataset)
    except:
        print('Warning: cannot convert dataset to numpy array.')
    return dataset, np.array(labels)


def spectrograms_benchmark(dataset, window_length):
    """
    Compute the spectrograms for the songs in the Benchmark dataset.
    The data are resampled from 44100 Hz to 22050 Hz.
    :param dataset: relevant data in the Benchmark dataset.
    :param window_length: the number of points in the output window.
    :return: the spectrograms.
    """
    expected_music_length = 10
    return spectrogram_of_dataset(dataset, expected_music_length, window_length)


def spectrograms_gtzan(dataset, window_length):
    """
    Compute the spectrograms for the songs in the GTZAN dataset.
    Each sample is partitioned into approximately 3 equal parts since each song was originally 30 seconds long
    and thus we analyze samples corresponding to 10-second long clips.
    :param dataset: relevant data in the GTZAN dataset.
    :param window_length: the number of points in the output window.
    :return: the spectrograms.
    """
    expected_music_length = 30
    return spectrogram_of_dataset(dataset, expected_music_length, window_length)


def spectrogram_of_dataset(dataset, expected_music_length, window_length):
    """
    Compute the spectrograms for the samples in the given dataset.
    :param dataset: the dataset containing the samples.
    :param expected_music_length: the time length in seconds for the original music sample.
    :param window_length: the number of points in the output window.
    :return: the spectrograms
    """
    if expected_music_length not in (10, 30):
        raise Exception('Variable expected_music_length should be either 10 or 30, but received {}.'
                        .format(expected_music_length))

    spectrograms = []  # spectrograms = np.empty((len(dataset), 129, 989))

    window = scipy.signal.hanning(window_length)

    max_spec_length = -1
    min_spec_length = 1000000000
    for i in range(len(dataset)):
        x = dataset[i]
        if expected_music_length == 10:
            frequencies, times, Sxx = signal.spectrogram(x, window=window)
            spectrograms.append(Sxx)

            # todo: remove debugging code
            if len(Sxx) > max_spec_length:
                max_spec_length = len(Sxx)
                print('warning 3: max_spec_length is', max_spec_length)
            if len(Sxx) < min_spec_length:
                min_spec_length = len(Sxx)
                print('warning 4: min_spec_length is', min_spec_length)

        else:
            # expected_music_length == 30
            # partition the sample into 3 equal parts if the song was 30 seconds long originally.
            partition_size = len(x) // 3
            frequencies_1, times_1, Sxx_1 = signal.spectrogram(x[:partition_size], window=window)
            frequencies_2, times_2, Sxx_2 = signal.spectrogram(x[partition_size:partition_size * 2], window=window)
            frequencies_3, times_3, Sxx_3 = signal.spectrogram(x[partition_size * 2:], window=window)

            # todo: remove debugging code
            if len(Sxx_1[0]) > max_spec_length:
                max_spec_length = len(Sxx_1[0])
                print('warning 5: max_spec_length is', max_spec_length)
            if len(Sxx_1[0]) < min_spec_length:
                min_spec_length = len(Sxx_1[0])
                print('warning 6: min_spec_length is', min_spec_length)
            if len(Sxx_3[0]) > max_spec_length:
                max_spec_length = len(Sxx_3[0])
                print('warning 7: max_spec_length is', max_spec_length)
            if len(Sxx_3[0]) < min_spec_length:
                min_spec_length = len(Sxx_3[0])
                print('warning 8: min_spec_length is', min_spec_length)

            spectrograms.append(Sxx_1)
            spectrograms.append(Sxx_2)
            spectrograms.append(Sxx_3)
    try:
        spectrograms = np.array(spectrograms)
    except:
        # cannot convert list of spectrograms to numpy array if the spectrograms have different dimensions.
        print('Warning: cannot convert spectrograms to numpy array.')
    return spectrograms


def data_preprocessing():
    """
    Preprocess data, includes loading the Benchmark dataset and the GTZAN dataset,
    then compute the spectrograms for each data.
    """
    print('Preprocessing data...')
    classifications = np.array(['blues', 'hiphop', 'jazz', 'pop', 'rock'], dtype=object)
    # classifications = np.array(['pop'], dtype=object)
    # todo: remove debugging code above

    # paths to datasets
    benchmark_base_path = 'dataset/benchmarkdataset/'
    gtzan_base_path = 'dataset/gtzan/'

    window_length = 256
    # read music files
    t_1 = time.time()
    benchmark_dataset, benchmark_labels = read_all_music_benchmark(benchmark_base_path, classifications, window_length)
    t_2 = time.time()
    gtzan_dataset, gtzan_labels = read_all_music_gtzan(gtzan_base_path, classifications, window_length)
    # replicate the labels 3 times for samples in the GTZAN dataset
    gtzan_labels = np.array([x for x in gtzan_labels for _ in (0, 1, 2)])
    t_3 = time.time()
    print('The time used for loading the Benchmark dataset was', t_2 - t_1)
    print('The time used for loading the GTZAN dataset was', t_3 - t_2)

    # compute spectrograms
    t_4 = time.time()
    benchmark_spectrograms = spectrograms_benchmark(benchmark_dataset, window_length)
    t_5 = time.time()
    print('The time used for calculating spectrograms for the Benchmark dataset was', t_5 - t_4)
    gtzan_spectrograms = spectrograms_gtzan(gtzan_dataset, window_length)
    t_6 = time.time()
    print('The time used for calculating spectrograms for the GTZAN dataset was', t_6 - t_5)

    # pickling data
    benchmark_spectrograms_base_path = 'dataset/benchmark_spectrograms'
    gtzan_spectrograms_base_path = 'dataset/gtzan_spectrograms'
    benchmark_labels_base_path = 'dataset/benchmark_labels'
    gtzan_labels_base_path = 'dataset/gtzan_labels_labels'
    # modify name_suffix to choose dataset
    name_suffix = '_256'
    pickle_ext = '.p'

    pickle.dump(benchmark_spectrograms, open(benchmark_spectrograms_base_path + name_suffix + pickle_ext, 'wb'))
    pickle.dump(gtzan_spectrograms, open(gtzan_spectrograms_base_path + name_suffix + pickle_ext, 'wb'))
    pickle.dump(benchmark_labels, open(benchmark_labels_base_path + pickle_ext, 'wb'))
    pickle.dump(gtzan_labels, open(gtzan_labels_base_path + pickle_ext, 'wb'))
