import numpy as np
import math

# 常数
RANDOM_SEED = 42
MILLISECONDS_IN_SECOND = 1000.0
B_IN_MB = 1000000.0
BITS_IN_BYTE = 8.0

# 网络参数
PACKET_PAYLOAD_PORTION = 0.95
LINK_RTT = 104.  # millisec
PACKET_SIZE = 1500  # bytes

# chunk长度（1s写死，未使用）
VIDEO_CHUNCK_LEN = 1000.0  # millisec

#模拟视频时长
TOTAL_VIDEO_CHUNCK = 172
#可变参数
# fps_set = [1, 5, 10, 15, 20, 25, 30, 60]
# tile_set = [(1,1), (2,3), (4,6), (8,12), (16,24)]
# tile_size_set备选：8k 4k 2k 1080P 720P ?
# tile_size_set = ['WxH', 'WxH', 'WxH', 'WxH', 'WxH']
# BITRATE_LEVELS = 6
# VIDEO_BIT_RATE = np.array([20000, 40000, 60000, 80000, 110000, 160000])  # Kbps
# BITRATE_LEVELS = 7
# VIDEO_BIT_RATE = np.array([0, 20000, 40000, 60000, 80000, 110000, 160000])  # Kbps
fps_set = [30]
tile_set = [(1,1)]
# tile_size_set备选：8k 4k 2k 1080P 720P ?
tile_size_set = ['WxH']
BITRATE_LEVELS = 1
VIDEO_BIT_RATE = [160000]  # Kbps

# 需要更换
VIDEO_SIZE_FILE = '../videos/frame_size.txt'
VIDEO_INFO_FILE = '../videos/frame_info.txt'
VIDEO_DIFF_FILE = '../videos/frame_diff.txt'

class panoramic_env:
    def __init__(self, all_cooked_time, random_seed=RANDOM_SEED):

        np.random.seed(random_seed)

        self.all_cooked_time = all_cooked_time

        self.video_chunk_counter = 0
        self.buffer_size = 0

        self.trace_idx = 0
        self.cooked_time = self.all_cooked_time[self.trace_idx]

        self.mahimahi_start_ptr = 0
        self.mahimahi_ptr = 0
        self.last_mahimahi_time = 0
        self.mahimahi_base = 0

        # 视频frame大小
        # chunk_id:[0,TOTAL_VIDEO_CHUNCK)/fps:(?)/tile:(1*1,2*3,4*6,8*12,16*24)/tile_id:[0,tile_cnt)/tile_size:(?)/tile_bitrate:[0,BITRATE_LEVELS)/cur_f:[0,fps)
        self.video_size = []
        video_size_file = open(VIDEO_SIZE_FILE, 'r')
        for i in range(TOTAL_VIDEO_CHUNCK):
            tmp = {}
            for fps in fps_set:
                tmp[fps] = {}
                for tile in tile_set:
                    tmp[fps][tile] = {}
                    tile_cnt = tile[0]*tile[1]
                    for tile_id in range(tile_cnt):
                        tmp[fps][tile][tile_id] = {}
                        for tile_size in range(len(tile_size_set)):
                            tmp[fps][tile][tile_id][tile_size] = {}
                            for tile_bitrate in range(BITRATE_LEVELS):
                                tmp[fps][tile][tile_id][tile_size][tile_bitrate] = []
                                for cur_f in range(fps):
                                    tmp[fps][tile][tile_id][tile_size][tile_bitrate].append(self.read_int(video_size_file))
            self.video_size.append(tmp)
        video_size_file.close()
        
        # chunk目标检测后回传信息
        # chunk_id:[0,TOTAL_VIDEO_CHUNCK)/fps:(?)/tile:(1*1,2*3,4*6,8*12,16*24)/tile_setings:[0, (len(tile_size_set) * BITRATE_LEVELS) ^ tile_cnt)
        # tile_seting : ((tile_0_size，tile_0_bitrate), (tile_1_size，tile_1_bitrate), ...,  (tile_n_size，tile_n_bitrate)) => int
        self.video_info_s = []
        video_info_file = open(VIDEO_INFO_FILE, 'r')
        for i in range(TOTAL_VIDEO_CHUNCK):
            tmp = {}
            for fps in fps_set:
                tmp[fps] = {}
                for tile in tile_set:
                    tmp[fps][tile] = {}
                    tile_cnt = tile[0]*tile[1]
                    for tile_seting in range((len(tile_size_set)*BITRATE_LEVELS)**tile_cnt):
                        tmp[fps][tile][tile_seting] = self.read_video_info(video_info_file)
            self.video_info_s.append(tmp)
        video_info_file.close()

        # chunk在某参数下与最佳参数下目标检测算法表现的差距
        self.video_diff_s = []
        video_diff_file = open(VIDEO_DIFF_FILE, 'r')
        for i in range(TOTAL_VIDEO_CHUNCK):
            tmp = {}
            for fps in fps_set:
                tmp[fps] = {}
                for tile in tile_set:
                    tmp[fps][tile] = {}
                    tile_cnt = tile[0]*tile[1]
                    for tile_seting in range((len(tile_size_set)*BITRATE_LEVELS)**tile_cnt):
                        # tmp[fps][tile][tile_seting] = self.read_int(video_diff_file)
                        tmp[fps][tile][tile_seting] = self.read_video_info(video_diff_file)
            self.video_diff_s.append(tmp)
        video_diff_file.close()


    def read_int(self, _file):
        return int(_file.readline()[0:-1])

    
    def read_video_info(self, _file):
        # info结构待定
        return None


    def tile_seting_to_int(self, tile_seting):
        seting_id = 0
        base = len(tile_size_set) * BITRATE_LEVELS
        for one_seting in tile_seting:
            seting_id *= base
            seting_id += one_seting[0]*BITRATE_LEVELS + one_seting[1]
        return seting_id
    
    def int_to_tile_seting(self, x, tile_cnt):
        tile_seting = [(0,0) for tile_id in range(tile_cnt)]
        base = len(tile_size_set) * BITRATE_LEVELS
        for tile_id in range(tile_cnt-1, -1, -1):
            y = x % base
            x = x // base
            tile_seting[tile_id] = (y//BITRATE_LEVELS, y%BITRATE_LEVELS)
        return tile_seting


    def get_video_diff(self, video_setings):
        tile_size = video_setings['tile_size']
        tile_bitrate = video_setings['tile_bitrate']
        tile_seting = self.tile_seting_to_int(zip(tile_size, tile_bitrate))
        return self.video_diff_s[self.video_chunk_counter][video_setings['fps']][video_setings['tile']][tile_seting]


    def get_video_info(self,video_setings):
        tile_size = video_setings['tile_size']
        tile_bitrate = video_setings['tile_bitrate']
        tile_seting = self.tile_seting_to_int(zip(tile_size, tile_bitrate))
        # print(self.video_chunk_counter, video_setings['fps'], video_setings['tile'], tile_seting)
        return self.video_info_s[self.video_chunk_counter][video_setings['fps']][video_setings['tile']][tile_seting], self.get_video_diff(video_setings)
    

    def get_video_chunk(self, video_setings):

        fps = video_setings['fps']
        video_chunk_size_s = self.video_size[self.video_chunk_counter][video_setings['fps']][video_setings['tile']]
        tile_cnt = video_setings['tile'][0]*video_setings['tile'][1]
        tile_size = video_setings['tile_size']
        tile_bitrate = video_setings['tile_bitrate']

        # frame level
        # 按frame传输
        packet_head = 66 #byte
        MTU = 65549-66

        produce_time = self.video_chunk_counter * MILLISECONDS_IN_SECOND
        time_per_frame = MILLISECONDS_IN_SECOND / fps 
        chunk_size = 0.0
        delay = 0.0
        self.last_mahimahi_time = self.mahimahi_base + self.cooked_time[self.mahimahi_ptr]
        start_time = max(self.last_mahimahi_time, math.floor(produce_time+time_per_frame))
        
        for cur_f in range(fps):
            produce_time += time_per_frame
            _produce_time = math.floor(produce_time)
            while self.mahimahi_base + self.cooked_time[self.mahimahi_ptr] < produce_time :
                self.mahimahi_ptr += 1
                if self.mahimahi_ptr >= len(self.cooked_time):
                    self.mahimahi_base += self.cooked_time[-1]
                    self.mahimahi_ptr = 0
            for tile_id in range(tile_cnt):
                video_frame_size = video_chunk_size_s[tile_id][tile_size[tile_id]][tile_bitrate[tile_id]][cur_f]
                packet_cnt = video_frame_size // MTU
                if packet_cnt*MTU < video_frame_size:
                    packet_cnt += 1
                chunk_size += packet_cnt*packet_head + video_frame_size
                for _packet in range(packet_cnt):
                    self.mahimahi_ptr += 1
                    if self.mahimahi_ptr >= len(self.cooked_time):
                        self.mahimahi_base += self.cooked_time[-1]
                        self.mahimahi_ptr = 0
            self.last_mahimahi_time = self.mahimahi_base + self.cooked_time[self.mahimahi_ptr-1]
            delay += self.last_mahimahi_time - _produce_time # + LINK_RTT
        # video_chunk_remain:有多少chunk停留在发送队列
        video_chunk_remain = self.last_mahimahi_time / MILLISECONDS_IN_SECOND - self.video_chunk_counter - 1
        latency = video_chunk_remain
        video_chunk_remain = math.floor(video_chunk_remain)
        self.video_chunk_counter += 1

        net_info = (start_time / MILLISECONDS_IN_SECOND, self.last_mahimahi_time / MILLISECONDS_IN_SECOND, delay, chunk_size, video_chunk_remain, latency)
        video_info = self.get_video_info(video_setings)
        end_of_video = False
        if self.video_chunk_counter >= TOTAL_VIDEO_CHUNCK-1:
            end_of_video = True
            self.video_chunk_counter = 0
            self.trace_idx += 1
            if self.trace_idx >= len(self.all_cooked_time):
                self.trace_idx = 0
            self.cooked_time = self.all_cooked_time[self.trace_idx]
            self.mahimahi_ptr = self.mahimahi_start_ptr
            self.last_mahimahi_time = 0
            self.mahimahi_base = 0

        return net_info, video_info, end_of_video
