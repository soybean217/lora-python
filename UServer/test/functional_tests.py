# # from selenium import webdriver
# #
# # browser = webdriver.Chrome("C:\Program Files (x86)\chromedriver_win32\chromedriver.exe")
# # browser.get('http://183.230.40.231:8100')
# #
# # print(browser.title)
# from enum import Enum
# class CA:
#     def __init__(self, a):
#         self.a = a
#
#
# def fun_a(c):
#     c.a = c.a + 1
#
#
# class Model:
#     class RaspBerryPi(Enum):
#         RaspBerryPi2 = "rpi_2"
#         RaspBerryPiB = "rpi_b"
#
#         def __str__(self):
#             return {'RaspBerryPi2':'rpi 2', 'RaspBerryPiB':'rpi B/B+'}[self._name_]
#
#
# if __name__ == '__main__':
#     # ca = CA(1)
#     # fun_a(ca)
#     # print(ca.a)
#     # try:
#     #     2 / 'fefa'
#     #     # assert 1 == 2, 'No way'
#     # except (AssertionError, TypeError) as error:
#     #     print(error)
#     a = Model.RaspBerryPi.RaspBerryPi2
#     # str(a)
#     print(str(a))

def validate_arguments(arg1, arg2):
    def decorator(func):
        def wrapped():
            print(arg1, arg2)
            return func()
        return wrapped
    return decorator

# def f1():
#   return True

def f1(arg1, arg2):
    def decorator(func):
        def wrapped():
            print('f1',arg1, arg2)
            validate_arguments(arg1, arg2)(func)
            return func()
        return wrapped
    return decorator

@f1(1,2)
def helloWorld():
    print('!!!!!!!!!!!!!!!!!!!')


helloWorld()
# f1 = validate_arguments(1, 2)(f1)
# print(f1())