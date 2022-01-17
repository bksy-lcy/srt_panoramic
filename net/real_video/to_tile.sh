# NYC8K_VR360.mp4 7680x3840
let i_w=7680
let i_h=3840

# # mkdir
# mkdir ~/srt_tmp/videos/NYC8K
# mkdir ~/srt_tmp/videos/NYC8K/tile_1_1
# for k in 1 2 4 8
# do 
#     let x=k*2
#     let y=k*3
#     mkdir ~/srt_tmp/videos/NYC8K/tile_${x}_${y}
# done

# #ffmpeg -i ~/srt_tmp/videos/NYC8K_VR360.mp4 -ss 00:00:00 -to 00:01:00 -vf crop=3840:1920:0:0 tile0.mp4

# # 1x1
# ffmpeg -i ~/srt_tmp/videos/NYC8K_VR360.mp4 -y ~/srt_tmp/videos/NYC8K/tile_1_1/tile0.mp4
# 2x3, 4x6, 8x12, 16x24
# for k in 1 2 4 8
for k in 2 4 8
do 
    let x=k*2
    let y=k*3
    let o_w=i_w/y
    let o_h=i_h/x
    # echo ${o_w},${o_h}
    mkdir ~/srt_tmp/videos/NYC8K/tile_${x}_${y}
    for((i=0;i<${x};i++))
    do
        for((j=0;j<${y};j++))
        do
            let s_x=j*o_w
            let s_y=i*o_h
            let id=i*y+j
            # echo ${o_w},${o_h},${s_x},${s_y},${id}
            ffmpeg -i ~/srt_tmp/videos/NYC8K_VR360.mp4 -vf crop=${o_w}:${o_h}:${s_x}:${s_y} -y ~/srt_tmp/videos/NYC8K/tile_${x}_${y}/tile${id}.mp4
        done
    done
done