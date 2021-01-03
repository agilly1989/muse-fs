```
pip install audio-metadata
pip install pathvalidate
pip install unidecode
```

you also need ffmpeg in the same folder as this script OR in your env paths

add your input path and output path to lines 12 and 13 of process.py and run it (make them different folders)

this will make symlinks in your output folder that links to your music in

THERE IS BARELY ANY ERROR HANDLING IN THIS, RUN AT YOUR OWN RISK

NOTE: It is currently set up to make symlinks
