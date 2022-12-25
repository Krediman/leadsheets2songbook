# leadsheets2songbook

Dieses Projekt wird bei Codeberg (www.codeberg.org) unter dem Name "txt2latex" weitergeführt. Siehe (https://codeberg.org/krediman/txt2latex)

 #leavegithub

Konvertiert Lieder aus textdateien in Latex. 
Die Ausgabe ist kompatibel mit dem Latex-Packet leadsheets.

## Installation:
Diese Software verwendet Python3. python3 kann auf [www.python.org](www.python.org/downloads/) heruntergeladen werden.
Außerdem wird die Bibliothek jinja2 benötigt.

`$ pip install jinja2`

## Verwendung:
Der Konveriterung wird gestartet mit
```$ python3 converter.py [-o] <Eingabeverzeichnis> <Ausgabeverzeichnis>```

Das Programm liest alle Dateien im Eingabeverzeichnis und erstellt für jede Datei `Name.txt` eine Datei `Name.tex` im Ausgabeverzeichnis, die den dazugehörenden Latex code enthält.
Die Option `-o` erlaubt das Überschreiben von Dateien im Ausgabeverzeichnis, falls nötig.

