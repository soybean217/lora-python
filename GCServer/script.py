import pysftp
# with pysftp.Connection('183.230.40.231', username='ftp-vistor', password='ftp&132D') as sftp:
#     with sftp.cd('lora-ftp'):
#         print(sftp.get('/lora-ftp/log.conf'))
#         sftp.get('/lora-ftp/log.conf.md5')
# with pysftp.Connection('183.230.40.231', username='ftp-vistor', password='ftp&132D') as sftp:
#     print('connect...')
#     print(sftp.listdir())
#     # sftp.get(self.file_path,'/home/chenxing/sftp_file/config_file')
#     print(sftp.cwd('lora-ftp'))
#     print(sftp.listdir())
#     for file_name in sftp.listdir():
#         print(file_name)
#         print(sftp.get(file_name))


def if_sftp_file_exist(file_name):
    with pysftp.Connection('183.230.40.231', username='ftp-vistor', password='ftp&132D') as sftp:
        sftp.cwd('lora-ftp')
        if file_name in sftp.listdir():
            return True
        else:
            return False

if __name__ == '__main__':
    import time
    start_time = time.time()
    print(if_sftp_file_exist('asdfadfas'))
    end_time = time.time()
    print(start_time)
    print(end_time)