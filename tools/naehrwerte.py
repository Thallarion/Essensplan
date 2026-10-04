#!/usr/bin/env python3
"""Schätzt Nährwerte pro Erwachsenen-Portion für alle Gerichte in index.html
und schreibt sie als Feld N:{kcal,p,f,kh,bs,gv,pm,q} in jedes Gericht.

Aufruf:  python3 tools/naehrwerte.py            (schreibt index.html)
         python3 tools/naehrwerte.py --check    (zeigt nur an, prüft auf unbekannte Zutaten)

- Mengen in den Rezepten gelten für 3 Personen (2 Erwachsene + 1 Kind)  ->  Werte pro Portion = Gesamt / 3.
- Pauschal 20 g Öl pro Gericht (Vorrat, steht nicht in der Zutatenliste).
- Zutaten mit „(optional)“ im Namen zählen nicht mit.
- BUCH: Werte aus dem Kochbuch (pro Portion) haben Vorrang; Ballaststoffe/Gemüse werden trotzdem geschätzt.
Neue Zutat?  ->  in TAB ergänzen (Werte je 100 g, Gramm je Einheit).
"""
import json, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
PORTIONS = 3
OIL_G = 20

# name: (Gramm je Einheit oder None bei g/ml/l, kcal, Eiweiß, Fett, KH, Ballaststoffe, Gemüse/Hülsenfrucht 0/1, verarbeitetes Fleisch 0/1)
TAB = {
 "Buttergemüse (TK)":(300,75,2,4,6,3,1,0), "Kräuter-Schmelzkäse":(None,260,11,21,6,0,0,0), "Speckwürfel":(None,300,15,27,0.5,0,0,1), "Pinienkerne":(None,675,14,68,4,4,0,0),
 "Apfelmus":(360,75,0.2,0.1,17,1.5,0,0), "Aubergine":(300,24,1.2,0.2,3,2.8,1,0), "Aufbackbrötchen":(60,250,8,1.5,50,3,0,0),
 "Avocados (reif)":(150,200,2,20,4,6.5,1,0), "Avocado":(150,200,2,20,4,6.5,1,0), "Babyspinat":(None,23,2.9,0.4,1.4,2.2,1,0),
 "Orzo (Risoni)":(None,355,12.5,1.5,71,3,0,0), "Baguette":(250,260,8.5,1.5,52,2.5,0,0), "Bandnudeln":(None,360,13,2.5,70,3,0,0), "Basilikum":(20,30,3,0.6,3,3,0,0),
 "Basmatireis":(None,350,8,0.6,77,1.4,0,0), "Beerenmischung":(None,40,1,0.3,7,4,0,0), "Blattspinat":(None,20,2.5,0.3,1,2,1,0), "Blattspinat (frisch)":(None,23,2.9,0.4,0.6,2.2,1,0), "Rahmspinat (TK)":(None,65,2.6,4,4,1.8,1,0),
 "Blumenkohl":(600,25,2,0.3,2.5,2.5,1,0), "Blätterteig":(275,390,5.5,25,36,1.5,0,0), "Brokkoli (TK)":(None,34,3.5,0.4,3,3,1,0),
 "Brokkoli":(400,34,3.5,0.4,3,3,1,0), "Bulgur":(None,350,12,1.5,70,9,0,0), "Burgerbrötchen":(75,270,9,4.5,48,2.5,0,0),
 "Bärlauch (oder Schnittlauch / fertiges grünes Pesto)":(50,25,2.5,0.5,2,2,0,0), "Cashewkerne":(None,580,18,44,26,3,0,0),
 "Champignons":(None,22,3,0.3,0.6,2,1,0), "Cheddar gerieben":(None,400,25,33,0.5,0,0,0), "Cornflakes (ungezuckert)":(None,370,7,1,82,3,0,0),
 "Couscous":(None,360,12,1.5,72,5,0,0), "Crème fraîche":(None,300,2.4,30,3,0,0,0), "Dill":(20,30,3,0.6,3,3,0,0),
 "Dinkelmehl":(None,340,12,2,68,4,0,0), "Edamame":(None,120,11,5,9,5,1,0), "Eier":(60,140,12.5,10,0.7,0,0,0),
 "Emmentaler gerieben":(None,380,28,30,0,0,0,0), "Erbsen":(None,80,5.5,0.4,11,5,1,0), "Erdnusskerne (ungesalzen)":(None,600,25,49,12,8,0,0),
 "Erdnussmus":(50,620,25,50,12,7,0,0), "Erdnüsse (geröstet)":(None,600,25,49,12,8,0,0), "Falafel (fertig)":(None,330,13,18,30,8,0,0),
 "Feldsalat":(None,20,1.8,0.4,0.7,1.5,1,0), "Feta":(None,260,17,21,0.5,0,0,0), "Fischsauce":(25,35,5,0,4,0,0,0),
 "Fischstäbchen":(30,200,13,9,17,1,0,0), "Fladenbrot":(400,260,8.5,1.5,52,2.5,0,0), "Flammkuchenteig":(260,300,7,8,48,2,0,0),
 "Fleischbrühe":(None,5,0.5,0.2,0.4,0,0,0), "Frische Spätzle":(None,260,9,3,48,2,0,0), "Frischkäse":(None,250,6,22,4,0,0,0),
 "Frühlingszwiebeln":(150,30,1.8,0.2,5,2.5,1,0), "Fusilli":(None,355,12.5,1.5,71,3,0,0), "Garnelen":(None,90,19,1.5,0.5,0,0,0),
 "Mandeln (gehobelt)":(None,600,24,53,5,10,0,0),
 "Grünkern":(None,330,11.5,2.7,63,9,0,0), "Burrata":(125,300,15,25,1,0,0,0), "Pekannusskerne":(None,690,9,72,4,9.5,0,0), "Rosmarin":(3,130,3,6,20,14,0,0),
 "Gemahlene Mandeln":(None,600,24,53,5,10,0,0), "Gemüsebrühe":(None,3,0.2,0.2,0.4,0,0,0), "Gerstengraupen (oder Risottoreis)":(None,350,10,1.5,72,5,0,0),
 "Getrocknete Tomaten":(None,250,5,15,20,6,0,0), "Gnocchi":(None,155,3.5,0.3,34,2,0,0), "Gochujang (koreanische Chilipaste)":(40,200,4,1.5,43,2,0,0),
 "Gouda am Stück":(None,360,25,28,0,0,0,0), "Gouda gerieben":(None,360,25,28,0,0,0,0), "Gouda in Scheiben":(None,360,25,28,0,0,0,0),
 "Grüne Bohnen (TK)":(None,30,2,0.2,5,2.5,1,0), "Grüne Bohnen":(None,30,2,0.2,5,2.5,1,0), "Grüne Linsen":(None,330,25,1.5,50,11,1,0),
 "Grüner Spargel":(None,20,2.5,0.2,2,1.5,1,0), "Grünes Pesto":(150,450,5,45,6,2,0,0), "Gurke":(400,12,0.6,0.1,2,0.5,1,0),
 "Gyoza mit Gemüsefüllung":(None,200,7,6,30,2,0,0), "Gyros (gewürzt)":(None,200,19,13,1,0,0,0), "Hackfleisch gemischt":(None,250,18,20,0,0,0,0),
 "Haferflocken":(None,370,13.5,7,59,10,0,0), "Hefeflocken":(15,350,50,4,20,20,0,0), "Hokkaido-Kürbis":(900,40,1.7,0.5,8,2.5,1,0),
 "Holzspieße":(0,0,0,0,0,0,0,0), "Hähnchenbrustfilet":(None,110,23,1.5,0,0,0,0), "Hähnchenbrust":(None,110,23,1.5,0,0,0,0),
 "Hähnchenschenkel":(170,180,18,11,0,0,0,0), "Ingwer (klein)":(20,80,1.8,0.8,16,2,0,0), "Jasminreis":(None,350,7,0.6,78,1.3,0,0),
 "Karotten":(80,36,0.9,0.2,7,3,1,0), "Kartoffeln (festkochend)":(None,75,2,0.1,15,2,0,0), "Kartoffeln (mehligkochend)":(None,75,2,0.1,15,2,0,0),
 "Kartoffeln (mittelgroß)":(120,75,2,0.1,15,2,0,0), "Kichererbsen":(240,120,7,2.5,16,6,1,0), "Kidneybohnen":(250,100,7.5,0.5,13,7,1,0),
 "Kirschtomaten":(None,20,1,0.2,3,1.2,1,0), "Knoblauch":(4,140,6,0.5,28,2,0,0), "Kohlrabi":(300,25,2,0.1,4,1.5,1,0),
 "Kokosmilch":(400,170,1.8,17,3,0,0,0), "Koriander":(25,30,3,0.6,3,3,0,0), "Krautsalat":(None,60,1,3,7,2,1,0),
 "Kresse":(15,30,4,0.7,2,3,0,0), "Käse-Tortellini":(None,280,11,8,40,3,0,0), "Lachsfilet":(None,200,20,13,0,0,0,0),
 "Lasagneplatten":(None,355,12.5,1.5,71,3,0,0), "Lauch":(200,30,2,0.3,3.3,2.3,1,0), "Limette (Bio)":(40,30,0.5,0.2,7,0.5,0,0),
 "Limette":(40,30,0.5,0.2,7,0.5,0,0), "Mais":(285,90,3,1.2,16,3,1,0), "Makkaroni":(None,355,12.5,1.5,71,3,0,0),
 "Mangold (oder Blattspinat)":(None,20,2,0.3,2,1.5,1,0), "Mango":(300,60,0.8,0.4,13,1.6,0,0), "Mehl":(None,340,10,1,71,3,0,0),
 "Mie-Nudeln":(None,360,12,2,70,3,0,0), "Milchreis":(None,350,7,0.6,78,1.3,0,0), "Milch":(None,64,3.3,3.5,4.8,0,0,0),
 "Mineralwasser (mit Kohlensäure)":(None,0,0,0,0,0,0,0), "Mozzarella":(125,250,18,19,1,0,0,0), "Mungbohnensprossen":(None,20,2.5,0.2,2,1.5,1,0),
 "Möhren (lila oder orange)":(80,36,0.9,0.2,7,3,1,0), "Möhren":(None,36,0.9,0.2,7,3,1,0), "Naan-Brot":(90,290,8,7,48,2,0,0),
 "Naturjoghurt (3,8 %)":(None,64,3.4,3.8,4.1,0,0,0), "Naturjoghurt":(None,64,3.4,3.8,4.1,0,0,0), "Oliven":(80,150,1,15,1,3,0,0),
 "Pak Choi":(150,13,1.5,0.2,1.2,1,1,0), "Paneer (oder Halloumi)":(None,300,18,24,3,0,0,0), "Paprika":(160,30,1,0.3,5,2,1,0),
 "Parmesan am Stück":(None,390,35,28,0,0,0,0), "Parmesan":(None,390,35,28,0,0,0,0), "Passierte Tomaten":(None,25,1.3,0.2,4,1.2,1,0),
 "Pastinaken":(150,60,1.3,0.4,12,4,1,0), "Penne":(None,355,12.5,1.5,71,3,0,0), "Petersilienwurzeln":(100,40,3,0.5,6,4,1,0),
 "Petersilie":(25,30,3,0.6,3,3,0,0), "Pizzateig":(400,260,7,5,45,2,0,0), "Polenta":(None,350,8,1.5,75,4,0,0),
 "Putenbrust":(None,110,24,1,0,0,0,0), "Quark (20 % Fett)":(None,110,12,5,3,0,0,0), "Quark":(None,70,12,0.3,4,0,0,0),
 "Reisnudeln":(None,360,6,0.6,82,1.5,0,0), "Reispapier":(120,340,5,0.5,80,1,0,0), "Reis":(None,350,7,0.6,78,1.3,0,0),
 "Ricotta":(None,150,9,11,3,0,0,0), "Rinderhack":(None,230,20,16,0,0,0,0), "Risottoreis":(None,350,7,0.6,78,1.3,0,0),
 "Rosenkohl":(None,40,4.5,0.3,3.5,4.5,1,0), "Rote Bete (gegart, vakuumverpackt)":(400,40,1.5,0.1,8,2.5,1,0),
 "Rote Bete (klein, roh)":(150,40,1.5,0.1,8,2.5,1,0), "Rote Chilischote":(15,40,2,0.4,7,1.5,0,0), "Rote Currypaste":(40,120,2.5,8,10,4,0,0),
 "Rote Linsen":(None,340,24,1.5,50,11,1,0), "Romanesco":(500,25,2.5,0.3,3,2.5,1,0),
 "Rucola":(None,25,2.6,0.7,2,1.6,1,0), "Römersalat":(400,15,1.2,0.2,1.8,1.5,1,0),
 "Sahne":(None,300,2.4,30,3.2,0,0,0), "Salatgurke (groß)":(500,12,0.6,0.1,2,0.5,1,0), "Salatgurke":(400,12,0.6,0.1,2,0.5,1,0),
 "Salat":(300,15,1.2,0.2,1.8,1.5,1,0), "Sauerkirschen":(350,60,0.7,0.1,13,1,0,0), "Saure Sahne":(200,115,3,10,4,0,0,0),
 "Schalotten":(30,30,1.2,0.2,5,1.8,1,0), "Schmand":(None,240,2.6,24,3.5,0,0,0), "Schmelzkäse":(None,280,11,23,6,0,0,0),
 "Schnittlauch":(25,30,3,0.6,3,3,0,0), "Schwarzer Sesam":(10,580,18,50,12,12,0,0), "Seelachsfilet":(None,80,18,0.9,0,0,0,0),
 "Semmelbrösel":(None,360,10,2,72,4,0,0), "Semmelknödel (Kochbeutel)":(200,350,11,4,67,4,0,0), "Sesamöl":(30,880,0,100,0,0,0,0),
 "Spaghetti":(None,355,12.5,1.5,71,3,0,0), "Spinat gehackt":(None,25,2.5,0.4,1.3,2,1,0), "Stückige Tomaten":(None,25,1.3,0.2,4,1.2,1,0),
 "Suppengemüse / gemischtes Gemüse":(None,30,1.2,0.3,5,2.5,1,0), "Suppennudeln":(None,355,12.5,1.5,71,3,0,0), "Sushireis":(None,350,7,0.6,78,1.3,0,0),
 "Süßkartoffel":(400,86,1.6,0.1,20,3,1,0), "Teriyakisauce":(100,120,5,0,24,0,0,0), "Thunfisch (im eigenen Saft)":(150,110,25,1,0,0,0,0),
 "Toastbrot":(250,260,8,4,48,3.5,0,0), "Tofu mit Kräutern":(None,130,14,8,1.5,1.5,0,0), "Tofu":(None,130,14,8,1.5,1.5,0,0),
 "Tomaten":(100,20,1,0.2,3,1.2,1,0), "Tortilla-Wraps":(60,300,8,7,50,3,0,0), "Trockenhefe":(7,330,40,5,20,20,0,0),
 "Tzatziki":(None,110,4,9,4,0,0,0), "Udon-Nudeln (vorgegart)":(None,140,3.5,0.5,29,1.5,0,0), "Veggie-Patties":(100,220,15,12,12,4,0,0),
 "Vollkorn-Tortillas":(60,290,9,7,45,6,0,0), "Vollkornbrot":(300,220,7,1.5,40,8,0,0), "Vollkornmehl":(None,330,12,2,60,10,0,0),
 "Vollkornnudeln":(None,340,13,2.5,63,8,0,0), "Vollkornreis":(None,350,7.5,2.5,73,3.5,0,0), "Walnusskerne":(None,680,15,68,7,6,0,0),
 "Weichweizengrieß":(None,350,10,1,72,3,0,0), "Weiße Bohnen":(250,100,7,0.5,13,7,1,0), "Wiener Würstchen":(50,260,13,23,1,0,0,1),
 "Wurst (z. B. Mettwurst oder Fleischwurst)":(None,300,14,27,1,0,0,1), "Ziegenfrischkäse (oder Feta)":(None,250,12,21,1,0,0,0),
 "Zitrone (Bio)":(40,30,0.5,0.2,7,0.5,0,0), "Zitrone":(40,30,0.5,0.2,7,0.5,0,0), "Zucchini":(250,20,1.5,0.4,2,1.1,1,0),
 "Zwiebel":(100,30,1.2,0.2,5,1.8,1,0),
 "Zanderfilet (mit Haut)":(None,85,19,0.7,0,0,0,0), "Mandelmus (hell)":(None,620,24,53,6,12,0,0), "Thymian":(2,100,5,2,10,14,0,0), "Weißkohl":(None,25,1.4,0.2,4,3,1,0), "Kochschinken":(None,110,20,3,1,0,0,1), "Bergkäse gerieben":(None,400,28,32,0,0,0,0), "Veggie-Hack (Erbsenprotein)":(None,190,20,10,4,5,1,0), "Wirsing (klein)":(700,30,3,0.4,3,3,1,0), "Schwarze Bohnen":(240,110,8,0.5,14,7,1,0), "Grüne Peperoni":(40,30,1.5,0.3,4,2,1,0),
 "Gemüsebrühe (glutenfrei)":(None,3,0.2,0.2,0.4,0,0,0), "Tamari (glutenfreie Sojasauce)":(30,70,10,0,6,0,0,0),
 "Linsennudeln (glutenfrei)":(None,340,25,2,50,11,1,0), "Buchweizenmehl":(None,340,12,2.5,70,4,0,0),
 "Mais-Tortillas (glutenfrei)":(30,220,5,3,45,5,0,0), "Mais-Reis-Nudeln (glutenfrei)":(None,355,7,1.5,79,2,0,0),
 "Gemüsebrühe (ohne Jodsalz)":(None,3,0.2,0.2,0.4,0,0,0), "Quinoa":(None,360,14,6,58,7,0,0), "Tahin (Sesammus)":(60,600,24,53,10,9,0,0), "Cranberrys (getrocknet)":(None,330,0.2,1,80,5,0,0), "Linsen (Dose)":(265,100,8,0.6,14,5,1,0), "Pistazien":(None,600,20,50,17,10,0,0), "Radieschen":(150,15,1,0.1,2,1.6,1,0), "Stangensellerie":(50,15,1,0.2,2,1.6,1,0),
 "Forellenfilet":(None,110,20,3,0,0,0,0), "Buchweizen":(None,340,10,1.7,70,4,0,0), "Rindersteak (Hüfte)":(None,120,22,4,0,0,0,0),
 "Hirse":(None,355,11,4,69,4,0,0), "Grünkohl":(None,45,4.3,0.9,2.5,4.2,1,0), "Haferdrink (ohne Jodzusatz)":(None,45,0.5,1.5,7,0.8,0,0),
 "Leinsamen (geschrotet)":(None,450,24,31,2,30,0,0), "Minze":(25,45,3.5,0.7,5,7,0,0), "Kürbiskerne":(None,570,30,46,8,9,0,0),
 "Bananen":(120,90,1.1,0.2,20,2,0,0),
 "Grünkernschrot":(None,330,11.5,2.7,63,9,0,0),
 "Apfelsaft":(None,45,0.1,0.1,11,0,0,0), "Banane":(120,90,1.1,0.3,20,2,0,0), "Edamame (TK)":(None,120,11,5,9,5,1,0), "Ei":(60,140,12.5,10,0.7,0,0,0),
 "Gewürzgurken":(350,15,0.5,0.1,2.5,1,0,0), "Griechischer Joghurt":(None,130,5,10,4,0,0,0), "Halloumi":(None,320,22,25,2,0,0,0), "Hüttenkäse":(None,100,12,4.3,3,0,0,0),
 "Kabeljaufilet":(None,82,18,0.7,0,0,0,0), "Knollensellerie (klein)":(400,42,1.6,0.3,7,4.2,1,0), "Magerquark":(None,67,12,0.3,4,0,0,0), "Putenhackfleisch":(None,150,22,6,0,0,0,0),
 "Rote Zwiebel":(100,40,1.2,0.1,8,1.7,0,0), "Rotkohl":(None,28,1.4,0.2,4,2.5,1,0), "Räucherlachs":(None,180,22,10,0,0,0,0), "Tellerlinsen":(None,340,24,1.5,50,11,1,0),
 "Thunfisch im eigenen Saft":(150,110,25,1,0,0,0,0), "Tofu natur":(None,120,13,7,1,1,0,0), "Äpfel":(180,52,0.3,0.2,12,2,0,0),
 "Fenchel":(250,31,1.2,0.2,4,3.1,1,0), "Haselnüsse":(None,650,15,62,10,8,0,0), "Knäckebrot (Sesam)":(250,370,12,5,62,14,0,0), "Kokosraspeln":(None,600,6,60,7,16,0,0),
 "Nackthafer":(None,370,12,7,60,10,0,0), "Sesamsamen":(None,570,18,50,12,12,0,0), "Sonnenblumenkerne":(None,590,23,50,12,9,0,0), "Spitzkohl":(None,25,1.3,0.2,3.5,2.5,1,0),
 "Zuckerschoten":(None,40,2.8,0.2,5,2.6,1,0), "Äpfel (säuerlich)":(180,52,0.3,0.4,11,2,0,0),
}
# Einheiten, die als Gramm/ml zählen
GRAM = {"g":1, "ml":1, "l":1000, "kg":1000}

# Kochbuch-Angaben pro Portion: kcal, Eiweiß, Fett, KH
BUCH = {
 "k01":(470,11,31,39), "k02":(465,40,27,12), "k03":(425,29,18,33),
 "k04":(335,17,13,29), "k05":(685,32,43,41), "k06":(500,52,22,24),
 "k10":(515,31,22,44),
 "k28":(310,18,12,30), "k29":(510,7,20,70), "k30":(690,18,31,84), "k31":(550,17,36,35), "k32":(1096,60,67,67),
 "k71":(382,8,17,44), "k73":(285,7,13,32),
 "k74":(420,15,18,49), "k75":(210,18,13,3), "k76":(330,13,16,33),
 "k77":(805,32,56,37), "k80":(230,4,16,16), "k83":(640,19,36,60), "k88":(790,24,47,68),
 "k11":(470,36,27,20), "k12":(350,1,37,2),
}

def load_dishes(src):
    a = src.index("const DISHES = ["); b = src.index("\n];", a)
    js = "const D=" + src[a+15:b+3] + "\nprocess.stdout.write(JSON.stringify(D));"
    out = subprocess.run(["node","-"], input=js, capture_output=True, text=True, check=True).stdout
    return json.loads(out), a, b

def estimate(d):
    tot = [0.0]*5; gv = 0.0; pm = 0; unknown = []
    for q, u, n, _c in d["i"]:
        if "(optional)" in n: continue
        t = TAB.get(n)
        if t is None: unknown.append(n); continue
        per_unit, kcal, p, f, kh, bs, veg, proc = t
        grams = q * GRAM[u] if u in GRAM else q * (per_unit or 0)
        k = grams / 100
        for idx, v in enumerate((kcal, p, f, kh, bs)): tot[idx] += v * k
        if veg: gv += grams
        if proc and grams: pm = 1
    tot[0] += OIL_G * 9; tot[2] += OIL_G
    per = [x / PORTIONS for x in tot]
    N = {"kcal": round(per[0] / 10) * 10, "p": round(per[1]), "f": round(per[2]), "kh": round(per[3]), "bs": round(per[4]),
         "gv": round(gv / PORTIONS / 10) * 10, "pm": pm, "q": "s"}
    if d["id"] in BUCH:
        kc, p, f, kh = BUCH[d["id"]]
        N.update({"kcal": kc, "p": p, "f": f, "kh": kh, "q": "b"})
    return N, unknown

def main():
    src = HTML.read_text(encoding="utf-8")
    dishes, a, b = load_dishes(src)
    missing = set(); result = {}
    for d in dishes:
        N, unk = estimate(d); missing.update(unk); result[d["id"]] = N
    if missing:
        print("Unbekannte Zutaten – bitte in TAB ergänzen:", *sorted(missing), sep="\n  "); sys.exit(1)
    if "--check" in sys.argv:
        for d in dishes: print(d["id"], d["n"][:40].ljust(40), result[d["id"]])
        return
    body = src[a:b]
    for did, N in result.items():
        pat = re.compile(r'(\{id:"' + did + r'",)(N:\{[^}]*\},)?')
        body, n = pat.subn(lambda m: m.group(1) + "N:" + json.dumps(N, separators=(",", ":")).replace('"', '') .replace("q:s", 'q:"s"').replace("q:b", 'q:"b"') + ",", body, count=1)
        assert n == 1, did
    HTML.write_text(src[:a] + body + src[b:], encoding="utf-8")
    print(f"{len(result)} Gerichte aktualisiert.")

if __name__ == "__main__":
    main()
