import subprocess
from multiprocessing import Manager, Process, Pool, cpu_count
from queue import Queue, Full, Empty
import time
from datetime import datetime
import os

from threads.jack_of_all_trades import Jack, Jill


def main():
    inputPath = r'C:\Users\geek_\Desktop\Muszack'
    outputPath = r'C:\Users\geek_\Desktop\Muszack Sorted'
    with Manager() as mpManager:    
        pool_length = cpu_count()
        queueSize = pool_length*10
        mainQueue = mpManager.Queue()
        messageQueue = mpManager.Queue()
        messageQueue.put(f'{datetime.now()} > Starting Jill')
        jill = Process(target=Jill,args=(messageQueue,))
        jill.start()
        
        with Pool(pool_length) as pool:
            jacks = [pool.apply_async(func=Jack,args=(mainQueue,index,outputPath,messageQueue)) for index in range(0,pool_length)]
            time.sleep(1)
            for root,_,files in os.walk(inputPath):
                for file in files:
                    path = os.path.join(root,file)
                    emptyDict = {'path':path}
                    while True:
                        if mainQueue.qsize() < (queueSize-(pool_length*2)):    
                            try:
                                mainQueue.put(emptyDict,True,1)
                                break
                            except Full:
                                time.sleep(1)
                        else:
                            time.sleep(1)
            for jack in jacks:
                jack.wait()
            jill.join()
        
if __name__ == '__main__':
    start = datetime.now()
    main()
    print(f'That took {datetime.now() - start}')
    