# Aan de slag met CP/M

[Documentatie](README.md) · [Installatie](../README.md)

De Philips P2000C start direct in CP/M. `A>` betekent dat systeemschijf A:
geselecteerd is. Typ alleen een commando en druk daarna op **RETURN**.
Hoofdletters en kleine letters maken niet uit.

| Commando | Wat gebeurt er? |
| --- | --- |
| `DIR` | Toon bestanden op de huidige schijf. |
| `DIR F:` | Bekijk F: zonder van schijf te wisselen. |
| `B:` | Ga naar diskette 1; plaats eerst een leesbare CP/M-diskette. |
| `F:` | Ga naar de spelletjesschijf. |
| `ZORK1` | Start Zork I wanneer F: geselecteerd is. |
| `ZEESLAG` | Speel Zeeslag tegen de P2000C. |
| `TETRIS` | Start het Nederlandstalige Tetris-spel. |
| `MINES` | Speel Mijnenveger op drie niveaus. |
| `SCHAKEN` | Speel het nieuwe Nederlandstalige schaakspel. |
| `KAKURO` | Los een van 95 Japanse cijferpuzzels op. |
| `CHESS` | Start het klassieke Super-Chess 2000. |
| `D:README` | Toon de indeling van toepassingen op D:. |
| `USER 3` | Schakel naar gebruikersgebied 3 voor SuperCalc 2. |
| `USER 0` | Ga terug naar het standaardgebruikersgebied. |
| `TYPE NAAM.TXT` | Lees een tekstbestand. |

Bestandsnamen hebben maximaal acht tekens plus een extensie van drie tekens.
A: bevat CP/M en gereedschap; B:/C: zijn diskettes; D: bevat toepassingen;
E: is vrij en F: bevat spellen. Bij de CoPower-variant is G: een RAM-schijf:
bestanden daarop verdwijnen bij uitschakelen.

Met PIP kopieer je bestanden. Bijvoorbeeld `A:PIP G:=F:ZORK1.DAT[OV]` kopieert
een spelbestand naar G: en verifieert de kopie. Gebruik dit alleen met CoPower
en voldoende vrije ruimte.

Als een programma vastloopt, druk je op **RESET**. De computer keert terug naar
de CP/M-prompt; de SD-kaart hoeft niet opnieuw ingericht te worden. Niet
opgeslagen werk kan wel verloren gaan.
