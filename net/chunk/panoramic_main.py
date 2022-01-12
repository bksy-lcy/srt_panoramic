# buffer-based approach
import itertools
import os
import sys
import numpy as np
import load_trace
import panoramic_env as env
import datetime

M_IN_K = 1000.0
RANDOM_SEED = 42
LOG_FILE = '../5G_test_results/log_panoramic_v0'
# TEST_TRACES = '../test/'
TEST_TRACES = '../one_trace/'

S_INFO = 6  # bit_rate, buffer_size, next_chunk_size, bandwidth_measurement(throughput and time), chunk_til_video_end
S_LEN = 8  # take how many chunks in the past
A_DIM = 6

BITRATE_LEVELS = env.BITRATE_LEVELS
VIDEO_BIT_RATE = env.VIDEO_BIT_RATE
fps_set =env.fps_set
tile_set = env.tile_set
tile_size_set = env.tile_size_set



#state: 用于决策的状态
#state: 待定
def get_video_init_setings():
    setings = {'tile': (1,1), 'tile_size':[0], 'tile_bitrate': [0], 'fps': 30}
    state = []
    return setings, state


# net_info:start_time, end_time, delay, chunk_size, video_chunk_remain, latency
# video_info:待定
def get_video_setings(state, net_info, video_info):
    # 改变state
    # state => setings
    setings = {'tile': (1,1), 'tile_size':[0], 'tile_bitrate': [0], 'fps': 30}
    return setings


def calc_reward(net_info, video_info):
    return 0


def record_log(log_file,net_info, video_info, reward):
    log_file.write('{0:10.3f}\t'.format(net_info[0])+
                    '{0:10.3f}\t'.format(net_info[1])+
                    '{0:10.3f}\t'.format(net_info[2]/1000.0)+
                    '{0:10.3f}\t'.format(net_info[3]/1000.0)+
                    '{0:10.3f}\t'.format(net_info[4])+
                    '{0:10.3f}\n'.format(net_info[5]))

    
def main():

    np.random.seed(RANDOM_SEED)

    all_cooked_time, all_cooked_bw, all_file_names = load_trace.load_trace(TEST_TRACES)
    net_env = env.panoramic_env(all_cooked_time=all_cooked_time, all_cooked_bw=all_cooked_bw)
    video_count = 0
    log_path = LOG_FILE + '_' + all_file_names[net_env.trace_idx]
    log_file = open(log_path, 'w')

    video_setings, state = get_video_init_setings()

    while True:
        
        tile = video_setings['tile']
        tile_size = video_setings['tile_size']
        tile_bitrate = video_setings['tile_bitrate']
        fps = video_setings['fps']

        net_info, video_info, end_of_video = net_env.get_video_chunk(video_setings)

        reward = calc_reward(net_info, video_info)
        record_log(log_file, net_info, video_info, reward)

        if not end_of_video:
            video_setings = get_video_setings(state, net_info, video_info)
        else:
            video_count += 1
            if video_count >= len(all_file_names):
                break
            video_setings, state = get_video_init_setings()
            log_path = LOG_FILE + '_' + all_file_names[net_env.trace_idx]
            log_file = open(log_path, 'w')


if __name__ == '__main__':
    curr_time = datetime.datetime.now()
    main()
    curr_time2 = datetime.datetime.now()
    print(curr_time2 - curr_time)
