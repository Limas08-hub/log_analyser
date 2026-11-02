import gzip #c est un module pour lire les fichiers gzip
import os
"""
   read data logs from data directory as rows

"""

def is_gzip(file_path):
    # gzip files always start with the bytes 1f 8b
    with open(file_path, 'rb') as f:
        return f.read(2) == b'\x1f\x8b'


def toRows(path):
    files=sorted(os.listdir(path))# we give it as variable directory to form where we liste the data
    rows=[]
    for file in files :
        file_path=path+'/'+file # correspond généralement à la création d'un chemin d'accès (path) absolu ou relatif en concaténant un dossier
        if not os.path.isfile(file_path):
            continue
        # data/auth.log is a compressed archive of the other files but has no .gz name: skip it,
        # otherwise it is read as garbage text (and its content is already in the other files)
        if not file.endswith('.gz') and is_gzip(file_path):
            print(f'skipping {file}: compressed archive without .gz extension')
            continue
        openner=gzip.open(filename=file_path,mode='rt',encoding='utf-8',errors='replace') if file.endswith('.gz') else open(file_path,encoding='utf-8',errors='replace')
        with openner as f :   # inside the for loop -> every file is read, not only the last one
            rows+=f.read().splitlines()
    return rows

if __name__ =='__main__':
  print(toRows('./data')[:10])# slicing so he only shows the 10 first
