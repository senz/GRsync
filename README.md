# GRsync
GRsync is a handy Python script, which allows you to sync photos from Ricoh GR II via Wifi. It has been tested on Mac OS X and Ubuntu, and should be able to run on any platform that has a Python environment.

It automatically checks if photos already exists in your local drive. Duplicated photos will be skipped and only sync needed photos for you.

## Installaion
1. Get the source from Github
 
```bash
$ wget https://raw.githubusercontent.com/clyang/GRsync/master/GRsync.py
$ chmod +x GRsync.py
```

2. Assign the downloaded photo directory. Edit `GRsync.py`
 
```python
# Change the value of PHOTO_DEST_DIR
# Don't forget the tailing "/"
PHOTO_DEST_DIR = "/path/to/downloaded/photos/"
```

## Usage
1. Simple usage - Download ALL photos from Ricoh GR II via Wifi

```bash
./GRsync -a
```

2. Advanced usage - Download photos after specific directory and file

```bash
./GRsync -d 100RICOH -f R0000005.JPG
```
