from subprocess import run, PIPE
from queue import Queue, Full, Empty
import hashlib
import time
import re
import os
import shutil
import datetime
from unidecode import unidecode
import traceback


import audio_metadata # pip install audio-metadata
from pathvalidate import sanitize_filename # pip install pathvalidate



def Jack(queue:Queue,index:int,outPath:str,logQueue: Queue):
    logQueue.put(f'{datetime.datetime.now()} > Starting Jack {index}')
    looping = True
    while looping:
        try:
            fileDict = queue.get(True,5)
            if 'md5' not in fileDict:
                logQueue.put(f'{datetime.datetime.now()} > Jack {index} is processing a md5 -- "{os.path.split(fileDict["path"])[1]}"')
                command = f'ffmpeg -i "{fileDict["path"]}" -c:a pcm_s32le -vn -f md5 -'
                process = run(command,stdout=PIPE,stderr=PIPE)
                md5x = process.stdout.decode().strip().replace('MD5=','')
                if process.returncode == 0:
                    logQueue.put(f'{datetime.datetime.now()} > Jack {index} generated a md5 -- "{os.path.split(fileDict["path"])[1]}" -- {md5x}')
                    fileDict.update({'md5':md5x})
                    while True:
                        try:
                            queue.put(fileDict,True,1)
                            break
                        except Full:
                            time.sleep(1)
                continue
            # check if sha256 is empty
            if 'data' not in fileDict:
                logQueue.put(f'{datetime.datetime.now()} > Jack {index} is loading some data -- "{os.path.split(fileDict["path"])[1]}"')
                with open(fileDict['path'],'rb') as file:
                    fileDict.update({'data':file.read()})
                    while True:
                        try:
                            logQueue.put(f'{datetime.datetime.now()} > Jack {index} loaded data -- "{os.path.split(fileDict["path"])[1]}"')
                            queue.put(fileDict,True,1)
                            break
                        except Full:
                            time.sleep(1)
                continue
            if 'sha256' not in fileDict:
                logQueue.put(f'{datetime.datetime.now()} > Jack {index} is processing a sha256 -- "{os.path.split(fileDict["path"])[1]}"')
                hashx = hashlib.sha256(fileDict['data']).hexdigest()
                fileDict.update({'sha256':hashx})
                fileDict.update({'data':''})
                while True:
                    try:
                        logQueue.put(f'{datetime.datetime.now()} > Jack {index} generated a sha256 -- "{os.path.split(fileDict["path"])[1]}" -- {hashx}')
                        queue.put(fileDict,True,1)
                        break
                    except Full:
                        time.sleep(1)
                continue
            if 'metadata' not in fileDict:
                logQueue.put(f'{datetime.datetime.now()} > Jack {index} is reading the metadata -- "{os.path.split(fileDict["path"])[1]}"')
                metadata = audio_metadata.load(fileDict['path'])
                fileDict.update({'metadata':metadata.tags})
                while True:
                    try:
                        queue.put(fileDict,True,1)
                        break
                    except Full:
                        time.sleep(1)
                continue
            
            source = fileDict['path']
            extension = os.path.splitext(source)[1]
            
            try:
                artists = fileDict['metadata']['artist']
                albums = fileDict['metadata']['album']
                titles = fileDict['metadata']['title']
                sha256 = fileDict['sha256']
                
                if len(artists) == 0: artists = ['Unknown']
                if len(albums) == 0: albums = ['Unknown']
                if len(titles) == 0: titles = ['Unknown']
            
                for a in artists:
                    for b in albums:
                        for c in titles:
                            
                            #filename = f'{sanitize_filename(unidecode(c).encode("ascii").decode())}.{sha256[:6]}{extension}'
                            filename = f'{sanitize_filename(unidecode(c))}.{sha256[:6]}{extension}'
                            paths = []
                            
                            paths.append(os.path.join(outPath,"Artists",sanitize_filename(a),sanitize_filename(b),filename))
                            paths.append(os.path.join(outPath,'All Songs',filename))
                            
                            for x in paths:
                                try:
                                    os.makedirs(os.path.split(x)[0],exist_ok=True)
                                    #shutil.copyfile(source,x)
                                    os.symlink(source, x)
                                    logQueue.put(f'{datetime.datetime.now()} > Jack {index} copied "{source}" to "{x}"')
                                except:
                                    logQueue.put(f'{datetime.datetime.now()} > Jack {index} tried to copy "{source}" to "{x}" but there was an error')
            except FileExistsError:
                continue
            except Exception as e:
                print(e)
                looping = False
            
            
        except Empty:
            looping = False
        except Exception:
            logQueue.put(traceback.print_exc())
            
def Jill(messageQueue:Queue):
    printing = True
    with open('log.log', 'w') as log:
        while True:
            try:
                message = messageQueue.get(True,15)
                try:
                    log.write(message + '\n')
                    print(message)
                except UnicodeEncodeError:
                    message = unidecode(message)
                    log.write(message + ' - decoded\n')
                    print(message,' - decoded')
            except Empty:
                break
                