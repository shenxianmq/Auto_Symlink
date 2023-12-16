#!/bin/bash

python /app/run.py &
python /app/restart_sync.py &
python /app/web.py &

# 等待所有后台任务完成
wait