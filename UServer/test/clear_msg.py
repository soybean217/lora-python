# from utils.db0 import db0
#

class Test:
    def __init__(self):
        self.aa = {1: 2}

    def __setattr__(self, key, value):
        print('lol')
        print(hasattr(self, key))
        if hasattr(self, key):
            print('wow')
            raise Exception("no way")
        self.__dict__[key] = value



# if __name__ == '__main__':
#     keys = db0.keys('MSG*')
#     print(keys)
#     for key in keys:
#         db0.delete(key)

if __name__ == '__main__':
    t = Test()

    b = t.aa
    b[3] = 4
    print(t.aa)