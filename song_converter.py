import jinja2 as j2
import os
from typing import Tuple, Union, List, Dict
import re
import sys
from lib.Heuristik.Heuristik import Heuristik
from lib.texttype.texttype import texttype
# Erlaubt das einfache Arbeiten mit texen zugeordneten datenassert ('Überschrift' in block.types())
# typing: Pfadspezifikation:
pfad = Union[str, os.DirEntry]

class laTexttype(texttype):
    verseregex = r"^\s?\d+([).:]|( :))*\s*"
    refrainregex = r"^\s?[Rr][Ee][Ff]([Rr][Aa][Ii][Nn])?([).:]|( :))*\s*"
    inforegex = r"^\s?@?info((:\s*)|\s+)"
    """Subklasse von texttype, die zusätzlich textblöcke erzeugt, die an jinja2 übergeben werden können"""
    def __init__(self, data:List[List[str]], gew_typ=None):
        texttype.__init__(self, data, gew_typ)
        self.blocktyp = ''
        self.text = []
        self.use_autotyp = True
    
    #override
    def _generateWorkingData(self):
        self.blocktyp = ''
        self.text = []
        return super()._generateWorkingData()

    __doc__ = texttype.__doc__ + """
        Speichert die Daten, die hinterher in latex ausgegeben werden.
        typ: alle typen, die leadsheets kennt. z.B. verse, verse*, refrain, info

        text: wird 1: 1 in den latex code übernommen. """

    def set_blocktyp(self, typ):
        """typ des texttype objektes setzen"""
        self.blocktyp = typ
        self.use_autotyp = False
    
    def autotyp(self)->int:
        """findet automatisch den typ des texttype-objektes
        gibt die nummer der Zeile zurück, in der der hinweis gefunden wurde
        Es wird angenommen, dass das ganze objekt nur einen einzelnen Block enthält.
        gibt die zeilennummer zurück, in der das label, falls vorhanden, steht,
        sonst -1"""
        self._updateWD()
        for i in range(len(self.str)):
            line = self.str[i]
            if re.match(laTexttype.refrainregex, line) is not None:
                self.blocktyp = "refrain"
                return i
            elif re.match(laTexttype.verseregex, line) is not None:
                self.blocktyp = "verse"
                return i
            elif re.match(laTexttype.inforegex, line) is not None:
                self.blocktyp = "info"
                return i
            else:
                self.blocktyp = "verse*"
                #kein return, vielleicht findet man das label in der nächsten zeile
        return -1
    
    def squashChords(self):
        """setzt akkord- und Textzeilen zusammen, wenn möglich.
        sonst werden zeilen rein aus akkorden generiert
        Damit das funktioniert, muss der richtige typ gewählt sein."""
        self._updateWD()

        def ATzeile(akkzeile:Tuple[str], textzeile:Tuple[str])->Tuple[str]:
            """baut Akkord- und textzeile zu einer latex-
            kompatiblen Akkordtextzeile zusammen"""

            def atchord(akkord:str)->str:
                """gibt den latex befehl zurück, der den akkord an die passende stelle in den text setzt"""
                return r"\chord{" + akkord + "}"
            akkorde = akkzeile[0]
            #Textzeile falls nötig verlängern, bis sie wenigstens so lang ist, wie die Akkordzeile
            text = textzeile[0].ljust(len(akkorde))

            atz = '' #ergebnis: die akkordtextzeile
            textpos = 0
            # iteriere über alle Akkorde der Zeile:
            for match in re.finditer(r"\S+", akkorde):
                beg, end = match.start(), match.end()
                atz += text[textpos:beg]+atchord(akkorde[beg:end])
                textpos = beg
            
            # Den erst des textes nachd em letzten Akkord übernehmen
            atz += text[textpos:]
            return (atz, "Akkordtextzeile") #neuer typ ist klar

        def Azeile(akkzeile:Tuple[str])->Tuple[str]:
            """setzt die akkordzeile so, dass latex die zeichen als akkorde ohne text setzt"""
            akkorde = akkzeile[0]
            #wir wollen die abstände zwischen den Akkorden einigermaßen abbilden:
            #' ' -> leerzeichen
            #'  ' -> 1em
            #sonst: 1 em je 2 (3?) leerzeichen
            def achord(chord: str) -> str:
                """latex-befehl zum setzen eines Akkordes ohne text darunter"""
                return r"\writechord{" + chord + "}"
                
            lastEnd = 0 #position des vorherigen endes
            azeile = '' #Ausgabe
            for match in re.finditer(r"\S+", akkorde):
                beg, end = match.start(), match.end()
                spaces = beg - lastEnd  #anzahl der leerzeichen zwischen den beiden Akkorden
                if spaces <= 0:
                    #wenn kein leerraum, dass wird auch keiner generiert, der kleinerfall ist zur fehlervermeitung
                    pass
                elif spaces <= 1:
                    azeile += ' '
                else:
                    azeile += r"\hspace{" + str(int((spaces+1)//3)) +"}"
                azeile += achord(akkorde[beg:end])
                textpos = beg
            return (azeile, "Akkordzeile") # neuer typ ist klar
            

        newdata = []
        newtyp = []
        prevline = None #text der vorherigen zeile
        prevtyp = None  #typ der vorherigen zeile
        i = 0 # zu lesende Zeile (es wird jeweils die vorherige zeile verarbeitet)
        #füge data und gew_typ ein None-Element hinzu. Das wird hinterher nicht gelesen, das macht den Code einfacher
        self.data.append(None)
        self.gew_typ.append(None)
        while i<len(self.data):
            line = self.data[i]
            gew_typ = self.gew_typ[i]
            #unterscheide 4 Fälle:
            #1) Die vorherige zeile existiert nicht / wird nicht verwendet
            if prevline is None or prevtyp is None:
                #die zeile wird nicht verwendet.
                pass

            #2) die vorherige zeile ist eine akkordzeile
            elif prevtyp == "Akkordzeile":
                # ist die aktuelle zeile eine Textzeile?
                if gew_typ == "Textzeile":
                    #die beiden Zeilen werden zu einer Akkordtextzeile zusammengefügt.
                    newdata.append(ATzeile(prevline, line))
                    # die neue zeile ist vom typ Akkordtextzeile
                    newtyp.append("AkkordTextZeile")
                    #jetzt sind beide zeilen bentzt worden.
                    #die aktuelle zeile wird im folgenden nicht mehr (als vorherige zeile) verwendet.
                    line = None
                    gew_typ = None

                else:
                    #die vorherige Zeile wird als (einzelne) Akkordzeile formatiert
                    newdata.append(Azeile(prevline))
                    newtyp.append(prevtyp)
            
            #3) die letzte Zeile ist eine andere Zeile (infozeile, leerzeile, Überschrift) Das sollte nicht vorkommen
            else:
                #es wird nicht zusammengeführt. die vorherige zeile wird unverändert übernommen.
                newdata.append(prevline)
                newtyp.append(prevtyp)
            
            #gehe eine zeile weiter
            prevline = line
            prevtyp = gew_typ
            i += 1
        
        # Die neuen Daten verwenden
        # Die anderen arbeitsdaten (z.B. self.text) werden dadurch ungültig.
        self.invalidateWD() 
        self.data = newdata
        self.gew_typ = newtyp

    def makelatexdata(self):
        """erstellt den Text, der in das Latex-dokument eingefügt wird.
        es wird angenommen, dass das ganze objekt nur einen einzelenn block enthält"""
        # Zeilen automatich einrücken; regex vom anfang der zeile mit nummer linenr entfernen, 
        # ohne die realive position der zeichen zur zeile darüber zu ändern.
        def cutlabel(self, linenr, regex):
            if linenr > 0:
                    # vorherige Zeile muss ebenfalls gekürz werden, sonst passen die beiden nicht mehr aufeiander
                    #aktuelle zeile
                    akt = re.sub(regex, '', self.text[linenr])
                    #Anzahl der leerzeichen, die in der darüberliegenden Zeile zu viel sind.
                    l = len(self.text[linenr])-len(akt) 
                    # vorherige Zeile
                    prev = self.text[linenr - 1]
                    while l > 0:
                        l -= 1
                        if prev.startswith(' '):
                            #falls möglich, die zeile vorher kürzen
                            prev = prev[1:]
                        else:
                            #sonst die aktuelle zeile einrücken
                            akt = ' ' + akt
                    self.text[linenr - 1] = prev
                    self.text[linenr] = akt
            else:
                # Wenn es die erste zeile ist, ist nichts zu tun, da es keine vorherige zeile gibt.
                self.text[linenr] = re.sub(regex, '', self.text[linenr])
        
        self._updateWD()
        self.text = self.str + []
        if self.use_autotyp:
            lineNr = self.autotyp() #XXX: rückgabewert sollte 0 oder -1 sein, sonst Warnung werfen
            # Akkorde und text in eine zeile zusammensetzen, wenn möglich
            if self.blocktyp in {"verse*", "verse", "refrain"}:
                # Hack: updateWD löscht den blocktyp (und sollte es auch)
                #       blocktyp zwischenspeichern, um ihn hinterher wieder zu setzen
                blocktyp = self.blocktyp
                # Akkorde passend shreiben. das ändert normalerweise einige zeilen.
                self.squashChords()
                # durch das zusammensetzten der zeilen in squashchords rutschen die labels ggf in eine andere zeile.
                # Deshalb die zeilenummer des labels neu berechnen.
                lineNr = self.autotyp()
                # Deshalb müssen die Arbeitsdaten neu erstellt werden.
                self._updateWD()
                self.text = self.str + []
                self.blocktyp = blocktyp 
            
            # Labels aus dem text entfernen, falls vorhanden.
            # Labels müssen jetzt in der ersten zeile stehe
            if self.blocktyp == "verse*":  # Kein Label -> nichts zu tun
                pass
            elif self.blocktyp == "verse":
                cutlabel(self, lineNr, laTexttype.verseregex)
            elif self.blocktyp == "refrain":
                cutlabel(self, lineNr, laTexttype.refrainregex)
            elif self.blocktyp == "info":
                cutlabel(self, lineNr, laTexttype.inforegex)



class SongConverter():
    def __init__(self, template_path:pfad) -> None:
        self.template = self.get_template(template_path)

    def get_template(self, template_path:pfad) -> None:
        #  Jinja konfigurieren
        self.latex_jinja_env = j2.Environment(
            block_start_string=r'\BLOCK{',
            block_end_string=r'}',
            variable_start_string=r'\VAR{',
            variable_end_string=r'}',
            comment_start_string=r'\#{',
            comment_end_string=r'}',
            line_statement_prefix=r'%%',
            line_comment_prefix=r'%#',
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
            loader=j2.FileSystemLoader(os.path.abspath('.'))
        )
        #  Template laden
        return self.latex_jinja_env.get_template(template_path)

    def convert(self, lied:str)->str:
        """ Diese funktion erledigt die Konvertierungsarbeit für eine einzelne datei. 
            lied: [str] Inhalt der Datei """
        lied = lied.split('\n')  # in zeilen zerlegen
        # Jeder zeile die beiden wahrscheinlichsten typen zuordnen
        typen = Heuristik(lied)
        # Klasse zum einfahcen verwalten der Daten 
        texttyp = laTexttype(Heuristik(lied))

        #XXX: Hier kann man auch eine Simple Grammatik implementieren
        # Für jede Zeile den Wahrscheinlichsten typ wählen
        for linenr in range(len(texttyp)):
            zeilentypen = texttyp.choices(linenr)
            texttyp.choose(linenr, zeilentypen[0])
        bloecke = texttyp.split('Leer')

        # Jeder Block entspricht einem Liedblock, also Liedtext/Akkorde, Überschrift oder Info

        metadaten = dict()  # titel, Worte, Weise, alternativtitel, genre, tags, etc.
        inhalt = list()  # alle Blöcke, die in den latex Code übertragen werden.
        
        for i in range(len(bloecke)):
            block = bloecke[i]
            # Der erste block enthält die Überschrift und alle metadaten und wird deshalb gesondert behandelt.
            if i == 0:
                #Erster Block: Hier sollte die Überschrift stehen.
                if ('Überschrift' not in block.types()): # Wenn der erste block keine Überschrift ist, 
                    # gibt das kein sinnvolles ergebnis. dann kann man auch gleich abbrechen
                    print("Keine Überschrift gefunden", block, file=sys.stderr)
                    raise Exception()
                metadaten = SongConverter.meta_aus_titel(block)
                continue

            else:
                block.makelatexdata()
                inhalt.append(block)

        return self.fill_template(metadaten, inhalt) #TODO: Reine Zeilenumbrüche dürfen nicht vorkommen.
    
    # XXX unterstützung für Tags
    @staticmethod
    def meta_aus_titel(block: texttype)->dict:
        # Aufbau des Titelblockes: TITEL [Alternativtitel1] (Worte;Weise)
        text = str(block).replace('\n', '')  #Text, wie in der Eingabedatei, nur dieser Block, alles in einer Zeile
        #Marker:
        lb = text.find('(')     #left brace
        rb = text.find(')', lb) #right brace
        lk = text.find('[')
        rk = text.find(']', lk)
        # nicht gefunden position:
        # Wenn das zeihen nicht gefunden wird, ist sein index -1. 
        # Das führt zu dem problem, dass das Minimum dieser werte einen offset vom hinteren ende hat.
        # Dadurch fehlt das letzte zeichen des Titels, wenn nichts dahinter kommt.
        # Setze die Zeichenposition auf das len(text)-te Zeichen des Textes. Diese Position kann nicht 
        # gelesen werden, das passiert aber auc nicht. es löst das Problem
        if lb <= 0:
            lb = len(text)
        if lk <= 0:
            lk = len(text)
        #metadaten dictionary
        meta = dict()
        # Titel finden:
        meta["title"] = text[:min((lb, lk, len(text)))].strip()
        # alternativtitel finden
        if lk > 0 and rk > lk:
            meta["alt-title"] = text[lk + 1:rk].strip()
        # Worte und Weise:
        if lb > 0 and rb > lb: #lb kann nicht 0 sein, weil der Titel davor kommt.
            # TODO: Syntax (Worte: abc Weise:def) unterstützen
            ww = text[lb + 1:rb].strip()
            if ';' in ww:
                index = ww.find(';')
                meta["lyrics"] = ww[:index].strip()
                meta["music"] = ww[index + 1:].strip()
            else:
                meta["lyrics"] = ww
                meta["music"] = ww
        return meta

    convert.__doc__ = """file_content: Ein string, der ein ganzes lied enthält. 
        Siehe hiezu die Dokumentation für Lieder im Eingabeverzeichnis. 
        Die funktion convertiert das lied in latex. die ausgabe ist ein latex-dokument 
        das das lied darstellt."""
    
    def fill_template(self, metadaten: Dict[str, str], inhalt: List[laTexttype]) -> str:
        """füllt das jinja2-template mit den metadaten uund dem Inhalt
        erlaubte Schlüssel für metadaten: title, als_title, music, lyrics, genre, tags, ..."""
        metadata_str = ', '.join(str(key)+'={'+str(metadaten[key])+'}' for key in metadaten.keys())
        return self.template.render(metadata=metadata_str, content=inhalt)

    __doc__ = "Erlaubt das konvertieren von Liedern in textform in Latex_dokumente"




