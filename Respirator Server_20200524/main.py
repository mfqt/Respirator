# coding=utf-8

"""

"""

from multiprocessing import Manager
from RespiratorServer.respirator_server import Server
from RespiratorServer.command_processor import Processor


if __name__ == '__main__':
    queue = Manager().Queue()
    processor = Processor(queue)
    processor.run_processor()
    server = Server(queue, 5)
    server.run_server()
    processor.join()
    server.join()
