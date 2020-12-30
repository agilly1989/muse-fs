from subprocess import run, PIPE
from queue import Queue, Full, Empty
import hashlib
import time
import re
import os
import shutil

import audio_metadata # pip install audio-metadata
from pathvalidate import sanitize_filename # pip install pathvalidate


def Jack(queue:Queue,index:int,outPath:str):
    print(f'Starting Jack {index}')
    looping = True
    while looping:
        try:
            fileDict = queue.get(True,5)

            # check if sha256 is empty
            if 'data' not in fileDict:
                #print(f'> Jack {index} is loading some data')
                with open(fileDict['path'],'rb') as file:
                    fileDict.update({'data':file.read()})
                    while True:
                        try:
                            queue.put(fileDict,True,1)
                            break
                        except Full:
                            time.sleep(1)
                continue
            if 'sha256' not in fileDict:
                #print(f'> Jack {index} is processing a sha256')
                fileDict.update({'sha256':hashlib.sha256(fileDict['data']).hexdigest()})
                fileDict.update({'data':''})
                while True:
                    try:
                        queue.put(fileDict,True,1)
                        break
                    except Full:
                        time.sleep(1)
                continue
            if 'md5' not in fileDict:
                #print(f'> Jack {index} is processing a md5')
                command = f'ffmpeg -i "{fileDict["path"]}" -c:a pcm_s32le -vn -f md5 -'
                process = run(command,stdout=PIPE,stderr=PIPE)
                if process.returncode == 0:
                    fileDict.update({'md5':process.stdout.decode().strip().replace('MD5=','')})
                    while True:
                        try:
                            queue.put(fileDict,True,1)
                            break
                        except Full:
                            time.sleep(1)
                continue
            if 'metadata' not in fileDict:
                #print(f'> Jack {index} is reading the metadata')
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
            
            def sanitize(x):
                x = "".join([c for c in x if re.match(r'\w', c)])
                return x
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
                            filename = f'{sanitize_filename(c)}.{sha256[:6]}{extension}'
                            paths = []
                            
                            paths.append(os.path.join(outPath,sanitize_filename(a),sanitize_filename(b),filename))
                            paths.append(os.path.join(outPath,sanitize_filename(a),'All Songs',filename))
                            
                            for x in paths:
                                os.makedirs(os.path.split(x)[0],exist_ok=True)
                                #shutil.copyfile(source,x)
                                os.symlink(source, x)
            except FileExistsError:
                continue
            except Exception as e:
                print(e)
                looping = False
            
            
        except Empty:
            looping = False