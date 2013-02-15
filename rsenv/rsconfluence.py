#!/usr/bin/python



## Common ids:
## - projects spaceid: 589826


def getFilepathFromIds(spaceid, pageid=None, attachmentid=None):
    folders = list()
    folders.append('ver003')                       # Level 1
    folders.append((spaceid % 1000) % 250 )        # Level 2
    folders.append((spaceid/1000) % 250 )          # Level 3
    folders.append(spaceid)                        # Level 4
    if pageid:
        folders.append((pageid % 1000) % 250)           # Level 5
        folders.append((pageid % 1000000)/1000 % 250)  # Level 6
        folders.append(pageid)                         # Level 7
        if attachmentid:
            folders.append(attachmentid)                   # Level 8
            
        # actual file name is <file-version>.<file-extension>
    
    path = "/".join([str(folder) for folder in folders])
    return path







if __name__ == "__main__":
    path = getFilepathFromIds(589826, 2392080, 2883585)
    print path