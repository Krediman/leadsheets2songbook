#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 22:27:10 2020

@author: paul
"""

from typing import Collection, Set
from song_converter import SongConverter
import sys
import os
import typing

# typing: Pfadspezifikation:
pfad = typing.Union[str, os.DirEntry]

insuffixes = ['.txt',]
outsuffix = '.tex'
template_file = "Template.jinja"


def get_dir_content(directory:pfad) -> Set[os.DirEntry]:
    with os.scandir(directory) as listing:
        return set(listing)


def get_files(dir_content:Set[pfad])-> Set[pfad]:
    return set(elem for elem in dir_content if elem.is_file)


def get_accessable(dir_content:Set[pfad], access=os.R_OK) -> Set[pfad]:
    return set(elem for elem in dir_content if os.access(elem, access))


def get_inaccessable(dir_content:Set[pfad], access=os.R_OK) -> Set[pfad]:
    return set.difference(dir_content, get_accessable(dir_content, access))


def get_outfilename(infilename:str, outending:str, inendings:Collection[str]) -> str:
    """bestimmt einen Dateinamen für die Ausgabe
    outending ist die gewünschte endung der ausgabe, Endungen in inending werden entfernt"""
    for end in inendings: # Dateiendung kürzen
        if infilename.endswith(end):
            infilename = infilename[:len(infilename)-len(end)]
            break
    return infilename + outending #Dateiname für die Ausgabe


def readfile(filename:pfad, mode='r') -> str:
    # Liest den gesamten inhalt der Datei(auch von langsamen streams)
    chunksize = 10000 #anzahl der zeichen, die auf einemal gelesen werden.
    data = ''
    with open(filename, mode) as file:
        while 1:
            newdata = file.read(chunksize)
            data += newdata
            if len(newdata) < chunksize: # wurde das Ende der Datei erreicht? 
                break
    return data


def writefile(filename:pfad, data:str, mode='w')->int:
    with open(filename, mode) as file:
        chars_written = file.write(data)
        if chars_written != len(data):
            return 1
    return 0


def build_path(directory:pfad, filename:str)-> pfad:
    return os.path.join(directory, filename)


def convertFile(infile:pfad, outfile: pfad)-> None:
        # Datei laden
        print(infile.name.rjust(30), ' lesen… ', end='')
        indata = readfile(infile)
        # Datei Konvertieren
        print(' umwandeln… ', end='')
        outdata = converter.convert(indata)  # multithreading nötig?
        # Datei speichern
        print(' speichern… ', end='')
        writefile(outfile, outdata)
        print("fertig")


def getInfiles(directory:pfad) -> Set[pfad]:
    return get_accessable(get_files(get_dir_content(directory)), os.R_OK)


def fileIsWriteable(datei:pfad, allow_overwrite=False)->bool:
    # datei kann geschrieben werden und (es darf überschrieben werden oder die datei existiert nicht.)
    if os.path.exists(datei):
        # der pfad existiert.
        if os.path.isfile(datei) and allow_overwrite:  # ist es eine datei und ist überschreiben erlaubt
            # funktioniert auch für verknüpfungen, deren ziel schreibbar ist
            return os.access(datei, os.W_OK) 
        else:
            return False  # es handelt sich um ein verzeichnis oder wir dürfen nicht überschreiben(das heißt nicht, dass es nicht möglich wäre) 
    # datei existier nicht. Überprüfe schreibrechte im Ordner
    pdir = os.path.dirname(datei)
    if not pdir:
        pdir = '.'
    # Die datei kann erzeugt werden, falls in das verzeichnis geschrieben werde kann.
    return os.access(pdir, os.W_OK)


if __name__== "__main__":
    # Aufrufparameter lesen
    if len(sys.argv) >= 3:
        indir, outdir = sys.argv[-2:]
        if len(sys.argv) > 3 and '-o' in sys.argv[1:-2]:
            overwrite = True
        else:
            overwrite = False
    else:
        print("Benutzung: converter.py [-o] Eingabeverzeichnis Ausgabeverzeichnis", file=sys.stderr)
        sys.exit(1)
    if not (os.path.isdir(indir) and os.path.isdir(outdir)):
        raise Exception("dirctory not found")

    # Dateien, die gelesen werden können
    infiles = getInfiles(indir)

    # Converter laden:
    converter = SongConverter(template_path=template_file)
    
    for infile in infiles:
        outfilename = get_outfilename(infile.name, outsuffix, insuffixes) # Dateiname für die Ausgabe
        outpath = build_path(outdir, outfilename)                         # Ausgabepfad 

        # Prüfen, ob ausgabedatei geschrieben werden kann / darf.
        if not fileIsWriteable(outpath, overwrite):
            print(outfilename, ' darf nicht überschrieben werden. ', infile.name, " wird übersprungen.", file=sys.stderr)
            continue # Datei überspringen
        
        try:
            convertFile(infile, outpath)
        except Exception as e:
            print('FEHLER bei Datei', infile, e, file=sys.stderr)
     
