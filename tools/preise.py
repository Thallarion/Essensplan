#!/usr/bin/env python3
"""Schätzt die Zutatenkosten (Euro) je Gericht für 3 Personen und schreibt P:<Euro> in index.html.

Aufruf:  python3 tools/preise.py            (schreibt index.html)
         python3 tools/preise.py --check    (zeigt nur an, prüft auf Zutaten ohne Preis)

- Preise sind grobe Durchschnittswerte deutscher Supermärkte (Euro je kg bzw. je l).
- Gramm je Einheit kommen aus TAB in naehrwerte.py. Vorräte (Öl, Gewürze …) zählen pauschal VORRAT_EUR.
- Die Stufen 💶/💶💶/💶💶💶 vergibt die App aus P (Grenzen: const BUDGET in index.html).
Neue Zutat?  ->  in PREIS ergänzen (Euro je kg/l).
"""
import re, sys
sys.path.insert(0, __import__("pathlib").Path(__file__).resolve().parent.__str__())
import naehrwerte as nw

VORRAT_EUR = 1.0
PREIS = {
 "Apfelmus":2.5,"Apfelsaft":1.2,"Aubergine":3.5,"Aufbackbrötchen":5,"Avocado":8,"Avocados (reif)":8,"Babyspinat":9,"Baguette":4.5,"Banane":1.8,"Bananen":1.8,
 "Bandnudeln":3,"Basilikum":40,"Basmatireis":3.5,"Beerenmischung":6,"Bergkäse gerieben":16,"Blattspinat":4,"Blattspinat (frisch)":6,"Rahmspinat (TK)":3.5,"Blumenkohl":3,"Blätterteig":5,"Brokkoli":4,"Brokkoli (TK)":3.5,
 "Buchweizen":4,"Buchweizenmehl":4.5,"Bulgur":3,"Burgerbrötchen":5,"Buttergemüse (TK)":4,"Bärlauch (oder Schnittlauch / fertiges grünes Pesto)":20,"Cashewkerne":18,
 "Champignons":6,"Cheddar gerieben":12,"Cornflakes (ungezuckert)":4,"Couscous":3,"Cranberrys (getrocknet)":14,"Crème fraîche":6,"Dill":40,"Dinkelmehl":2,"Edamame":8,"Edamame (TK)":8,
 "Ei":4,"Eier":4,"Emmentaler gerieben":12,"Erbsen":3,"Erdnusskerne (ungesalzen)":8,"Erdnussmus":9,"Erdnüsse (geröstet)":8,"Falafel (fertig)":9,"Feldsalat":20,"Feta":10,
 "Fischsauce":10,"Fischstäbchen":8,"Fladenbrot":5,"Flammkuchenteig":6,"Fleischbrühe":10,"Forellenfilet":25,"Frische Spätzle":5,"Frischkäse":8,"Frühlingszwiebeln":8,"Fusilli":3,
 "Garnelen":22,"Gemahlene Mandeln":12,"Gemüsebrühe":0.3,"Gemüsebrühe (glutenfrei)":0.6,"Gemüsebrühe (ohne Jodsalz)":0.6,"Gerstengraupen (oder Risottoreis)":4,"Getrocknete Tomaten":20,
 "Gewürzgurken":3,"Gnocchi":5,"Gochujang (koreanische Chilipaste)":15,"Gouda am Stück":10,"Gouda gerieben":10,"Gouda in Scheiben":10,"Griechischer Joghurt":5,"Grüne Bohnen":5,
 "Grüne Bohnen (TK)":4,"Grüne Linsen":5,"Grüne Peperoni":8,"Grüner Spargel":10,"Grünes Pesto":12,"Grünkernschrot":5,"Grünkohl":5,"Gurke":3,"Gyoza mit Gemüsefüllung":12,"Gyros (gewürzt)":10,
 "Hackfleisch gemischt":9,"Haferdrink (ohne Jodzusatz)":1.5,"Haferflocken":2.5,"Halloumi":13,"Hefeflocken":25,"Hirse":4,"Hokkaido-Kürbis":3,"Holzspieße":0,"Hähnchenbrust":11,
 "Mandeln (gehobelt)":14,"Romanesco":6,"Hähnchenbrustfilet":11,"Hähnchenschenkel":6,"Hüttenkäse":6,"Ingwer (klein)":12,"Jasminreis":3.5,"Kabeljaufilet":24,"Karotten":1.5,"Kartoffeln (festkochend)":1.8,
 "Kartoffeln (mehligkochend)":1.8,"Kartoffeln (mittelgroß)":1.8,"Kichererbsen":3.5,"Kidneybohnen":3.5,"Kirschtomaten":7,"Knoblauch":12,"Knollensellerie (klein)":3,"Kochschinken":14,
 "Kohlrabi":3,"Kokosmilch":4,"Koriander":40,"Krautsalat":4,"Kresse":40,"Kräuter-Schmelzkäse":8,"Käse-Tortellini":9,"Kürbiskerne":12,"Lachsfilet":25,"Lasagneplatten":4,"Lauch":3,
 "Leinsamen (geschrotet)":5,"Limette":8,"Limette (Bio)":8,"Linsen (Dose)":4,"Linsennudeln (glutenfrei)":9,"Magerquark":3,"Mais":3.5,"Mais-Reis-Nudeln (glutenfrei)":7,
 "Mais-Tortillas (glutenfrei)":12,"Makkaroni":3,"Mandelmus (hell)":22,"Mango":6,"Mangold (oder Blattspinat)":6,"Mehl":1.5,"Mie-Nudeln":5,"Milch":1.2,"Milchreis":3,
 "Mineralwasser (mit Kohlensäure)":0.3,"Minze":40,"Mozzarella":9,"Mungbohnensprossen":8,"Möhren":1.5,"Möhren (lila oder orange)":2.5,"Naan-Brot":8,"Naturjoghurt":2.5,
 "Naturjoghurt (3,8 %)":2.5,"Oliven":10,"Orzo (Risoni)":4,"Pak Choi":5,"Paneer (oder Halloumi)":12,"Paprika":4,"Parmesan":25,"Parmesan am Stück":25,"Passierte Tomaten":1.8,
 "Pastinaken":5,"Penne":3,"Petersilie":40,"Petersilienwurzeln":6,"Pinienkerne":60,"Pistazien":28,"Pizzateig":5,"Polenta":3,"Putenbrust":12,"Putenhackfleisch":9,"Quark":3,
 "Quark (20 % Fett)":4,"Quinoa":8,"Radieschen":6,"Reis":3,"Reisnudeln":6,"Reispapier":15,"Ricotta":8,"Rinderhack":11,"Rindersteak (Hüfte)":28,"Risottoreis":5,"Rosenkohl":6,
 "Rote Bete (gegart, vakuumverpackt)":4,"Rote Bete (klein, roh)":2.5,"Rote Chilischote":30,"Rote Currypaste":15,"Rote Linsen":3.5,"Rote Zwiebel":3,"Rotkohl":2,"Rucola":18,
 "Räucherlachs":35,"Römersalat":6,"Sahne":4.5,"Salat":5,"Salatgurke":3,"Salatgurke (groß)":3,"Sauerkirschen":4,"Saure Sahne":4,"Schalotten":8,"Schmand":4,"Schmelzkäse":8,
 "Schnittlauch":40,"Schwarze Bohnen":4,"Schwarzer Sesam":40,"Seelachsfilet":12,"Semmelbrösel":3,"Semmelknödel (Kochbeutel)":8,"Sesamöl":20,"Spaghetti":2.5,"Speckwürfel":10,
 "Spinat gehackt":3.5,"Stangensellerie":5,"Stückige Tomaten":1.8,"Suppengemüse / gemischtes Gemüse":5,"Suppennudeln":3,"Sushireis":5,"Süßkartoffel":3.5,"Tahin (Sesammus)":14,
 "Tamari (glutenfreie Sojasauce)":15,"Tellerlinsen":4,"Teriyakisauce":10,"Thunfisch (im eigenen Saft)":14,"Thunfisch im eigenen Saft":14,"Thymian":50,"Toastbrot":3,"Tofu":7,
 "Tofu mit Kräutern":9,"Tofu natur":7,"Tomaten":4,"Tortilla-Wraps":6,"Trockenhefe":40,"Tzatziki":5,"Udon-Nudeln (vorgegart)":6,"Veggie-Hack (Erbsenprotein)":14,"Veggie-Patties":14,
 "Vollkorn-Tortillas":7,"Vollkornbrot":4,"Vollkornmehl":2,"Vollkornnudeln":3.5,"Vollkornreis":3.5,"Walnusskerne":14,"Weichweizengrieß":2.5,"Weiße Bohnen":3.5,"Weißkohl":1.8,
 "Wiener Würstchen":11,"Wirsing (klein)":3,"Wurst (z. B. Mettwurst oder Fleischwurst)":10,"Zanderfilet (mit Haut)":28,"Ziegenfrischkäse (oder Feta)":14,"Zitrone":5,"Zitrone (Bio)":5,
 "Zucchini":3,"Zwiebel":1.5,"Äpfel":3,
}

def cost(d):
    tot, unknown = VORRAT_EUR, []
    for q, u, n, _c in d["i"]:
        if "(optional)" in n: continue
        p, t = PREIS.get(n), nw.TAB.get(n)
        if p is None or t is None: unknown.append(n); continue
        grams = q * nw.GRAM[u] if u in nw.GRAM else q * (t[0] or 0)
        tot += grams / 1000 * p
    return round(tot * 2) / 2, unknown

def main():
    src = nw.HTML.read_text(encoding="utf-8")
    dishes, a, b = nw.load_dishes(src)
    res, missing = {}, set()
    for d in dishes:
        c, unk = cost(d); missing.update(unk); res[d["id"]] = c
    if missing:
        print("Zutaten ohne Preis – bitte in PREIS ergänzen:", *sorted(missing), sep="\n  "); sys.exit(1)
    if "--check" in sys.argv:
        for d in dishes: print(d["id"], d["n"][:44].ljust(44), res[d["id"]])
        return
    body = src[a:b]
    for did, c in res.items():
        pat = re.compile(r'(\{id:"' + did + r'",(?:N:\{[^}]*\},)?)(P:[\d.]+,)?')
        body, n = pat.subn(lambda m: m.group(1) + "P:%s," % ("%g" % c), body, count=1)
        assert n == 1, did
    nw.HTML.write_text(src[:a] + body + src[b:], encoding="utf-8")
    print(f"{len(res)} Gerichte aktualisiert.")

if __name__ == "__main__":
    main()
