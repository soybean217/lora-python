import logging

# 创建一个logger
timing = logging.getLogger('timing')
timing.setLevel(logging.DEBUG)

# 创建一个handler，用于写入日志文件
fh = logging.FileHandler('timing.log')
fh.setLevel(logging.DEBUG)

# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)

timing.addHandler(fh)

