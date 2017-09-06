from time import ctime,time


def timeStumpFunc(args):
    def get_function(function):
        def wrappedFunc(*nkw):
            time_start = time()*1000
            result = function(*nkw)
            time_casted = time()*1000 - time_start
            print('Function',args,'cast %f ms' % time_casted)
            return result
        return wrappedFunc
    return get_function


def debuger(args):
    def get_function(function):
        def wrapped_function(*nkw):
            print(args,'begin!')
            # print('input type:',type(*nkw),'len:',len(*nkw))
            result = function(*nkw)
            print(args,'done!')
            return result
        return wrapped_function
    return get_function


def average_time_stump(times,name=''):
    def get_function(function):
        def wrappedFunc(*nkw):
            time_avg = 0
            for i in range(0,times):
                time_start = time()*1000
                result = function(*nkw)
                time_casted = time()*1000 - time_start
                time_avg += time_casted/times
                print(i,'time stump:',time_casted)
            print('Function:',name,'cast %f ms'%time_avg,'average in %d times tested'%times)
            return result
        return wrappedFunc
    return get_function