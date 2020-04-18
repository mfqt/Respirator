class A:
    def __init__(self):
        self.__a = "3"
    def __run(self,a):
        print(a)

class B(A):
    __a = "4"
    def run(self):
        #self.__a = "5"
        self.__run(self.__a)

if __name__ == '__main__':
    a = A()
    b = B()
    b.run()