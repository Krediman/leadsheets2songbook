# Heuristik.py
# Dieses Skript bestimmt die Warscheinlichkeit, dass eine Zeile eine Textzeile, überschrift, etc ist.
import re

_typen = dict(Überschrift="Überschrift", Leer="Leer", Akkordzeile="Akkordzeile", Textzeile="Textzeile",
              Info="Info")

_Ueber_starts = set("wuw jahr j mel melodie weise melj meljahr txt worte text txtj wortej wortejahr textj txtjahr textjahr alb album lager bo bock vq vasquaner biest tf turmfalke gb gnorkenbüdel gnorken hvp tb burgundi tarmina hk holz holzknopp".split())

# Regex - Ausdrücke, die für die erkennung gebraucht werden.
akkord_zeilen_regex = r"( *([:|]+|(\(?([A-Ha-h](#|b)?(sus|dim|add|maj)?\d*)(\/([A-Ha-h](#|b)?(sus|dim|add|maj)?\d*))*\)?)))+ *"
akkord_regex = r"(\(?([A-Ha-h](#|b)?(sus|dim|add|maj)?\d*)(\/([A-Ha-h](#|b)?(sus|dim|add|maj)?\d*))*\)?)"


def Heuristik(zeilen):
    # Eingabe:  liste aus Strings, jeder string entspricht einer Zeile
    # Ausgabe:  Liste der wahrscheinlichen Typen dieser Zeile
    # standart: typ, der verwendet wird, wenn der gesuchte typ nicht in typen enthalten ist.

    erg = list()
    for zeilenNr in range(len(zeilen)):
        zeile = zeilen[zeilenNr]
        zeile = zeile.replace('\n', '').replace('\r', '')     # Zeilenumbrüche entfernen

        erg.append(Line_Heuristik(zeile, zeilenNr, prev=erg))
    
    return erg


def Line_Heuristik(line, lineNr, prev):
    # line:      Die zu klassifizierende Zeile
    # lineNr:    Die zeilennummer der zeile (angefangen bei 0)
    # prev:      Die typen der vorhergehenden lineNr Zeilen
    # Standart:  typ der verwendet wird, wenn nichts erkannt wird.
    
    # Ausgabe:   Liste der möglichen erkannten typen mit dazugehöriger Warscheinlichkeit
    
    if line == '':                     p_leer = 1
    elif line.replace(' ', '') == '':  p_leer = 0.65
    else:                              p_leer = 1/(2+len(line.replace(' ', '')))
    p_ueber = p_Ueberschrift(line, lineNr, prev)
    p_text  = p_Textzeile(line, lineNr, prev)
    p_akk   = p_Akkordzeile(line, lineNr, prev)
    p_info  = p_Information(line, lineNr, prev)
    p_none = max(1 - (p_leer + p_ueber + p_text + p_akk + p_info), 0) #Abschätzung der warscheinlichkeit, dass diese zeile für gar nichts zu brauchen ist.
    
    # Wahrscheinlichkeiten Normieren
    summe = p_ueber + p_text + p_akk + p_info + p_none + p_leer
    p_ueber /= summe
    p_text  /= summe
    p_akk   /= summe
    p_info  /= summe
    p_none  /= summe
    p_leer  /= summe

    erg = dict(Überschrift=p_ueber, Leer=p_leer, Akkordzeile=p_akk, Textzeile=p_text, Info=p_info, none=p_none)
    
    # gebe die wahrscheinlichste und die zweitwahrscheinlichste lösung zurück
    beste = max(erg, key=lambda key: erg[key])
    erg.pop(beste)
    zweite = max(erg, key=lambda key: erg[key])
    erg.pop(zweite)
    return(line, beste if beste != "none" else None, zweite if zweite != "none" else None)


def p_Textzeile(line, lineNr, prev):
    p_text = 1
    # Es muss zumindest irgendwas in der zeile stehen.
    # Eine Leerzeile ist keine Textzeile
    if line.replace('\r', '').replace('\n', '') == '':
        return 0
    for zeichen in line:
        if zeichen not in " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß.,-:;…–\"?!":
            p_text *= 0.85                    # Textzeilen sollten nur text enthalten.
    p_text *= 0.85 ** line.count('  ')     # Doppelte leerzeichen deuten auf Akkordzeilen hin
    # Erlaube zwei Wiederholungszeichen (:|, |: oder :|:) pro zeile, bevor der die Warscheinlichkeit sinkt
    p_text /= 0.85 ** min(line.count("|"), 2)

    # Prüfe auf ggf. vorhandene Strophennummern.
    match = re.search(r"^\d*\)", line)
    if match is not None:
        if len(prev) > 1:
            if "Leer" in prev[-1] or "Leer" in prev[-2]:
                p_text /= 0.85 ** len(match.group(0)) # kein Fehler, wenn die Strophennummer auf eine Leerzeile folgt.
                p_text += min((1 - p_text) / 3, 0.15)  # Strophennummern kommen meistens in Textzeilen vor.
    # Wenn es sich um eine Überschrift handeln könnte, reduziere die Wahrscheinlichkeit für text.
    p_text *= 1-p_Ueberschrift(line, lineNr, prev) 
    return p_text


def p_Akkordzeile(line, lineNr, prev):
    # prüfe, ob die zeile der Grammatik entspricht:
    if re.fullmatch(akkord_zeilen_regex, line.replace('\n', '')) is not None:
        return 1
    # zerlege in zusammenhängenden text und prüfe, wie groß der Anteil an akkorden ist.
    parts = line.split(' ')
    korrekte = 0   # Anzahl erkannter Akkorde
    inkorrekte = 0 # Anzahl nicht als Akkord erkannter Wörter
    for pot_Akk in parts:
        if re.fullmatch(akkord_regex, pot_Akk) is not None:
            korrekte += 1
        else: 
            inkorrekte += 1
    return korrekte/(korrekte+inkorrekte)


def p_Ueberschrift(line, lineNr, prev):
    # line:      Die zu klassifizierende Zeile
    # lineNr:    Die zeilennummer der zeile (angefangen bei 0)
    # prev:      Die typen der vorhergehenden lineNr Zeilen
    
    # Ausgabe: warscheinlichkeit, dasss line eine Überschrift ist.
    if len(prev) != 0:
        #prüfe, ob die vorherigen zeilen entweder leer, none oder überschrift sind.
        if 0 != len(set(prev[i][1] for i in range(len(prev))).difference({"Überschrift", None})):
            return 0 # Das lied hat bereits begonnen

    if line.replace(' ', '') == '': return 0     # Zeile ist leer
    p = 0.5
    if lineNr <= 1:
        # erste zeile: hier stehen titel und alt. titel
        if line.count("[") == line.count("]"):
            if line.count("[") == 1:
                return 1
            else: 
                return 0.75
        else:   #Klammerausdruck ist nicht balancliert
            print ("Vermutlich ein Tippfehler in der ersten Zeile")
    for start in _Ueber_starts:
        if line.lower().startswith(start+':'):
            return 1
    return p


def p_Information(line, lineNr, prev):
    l = line.lower().strip(' ')
    if l.startswith('@info') or l.startswith('info ') or l.startswith('info:'): # Markierte Zeile
        return 1
    if len(prev)>0 and _typen["Info"] in prev[-1][1:]: # Nicht markierte zeile
        return p_Textzeile(line.lstrip(' ')[5:], lineNr, prev)
    return 0

