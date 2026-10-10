# Play Store – Ablauf

1. **Entwicklerkonto** anlegen (play.google.com/console, einmalig 25 $, Identitätsprüfung).
2. **Paket erzeugen:** auf pwabuilder.com `https://wasessenwir.at` eingeben → „Package for stores“ → Android. Paketname z. B. `at.wasessenwir.app`. Die ZIP enthält die `.aab`, den Signaturschlüssel (sicher aufbewahren!) und die Datei `assetlinks.json`.
3. **assetlinks.json:** Inhalt der von PWABuilder/Play Console gelieferten Datei in `.well-known/assetlinks.json` einfügen (aktuell leer: `[]`). Den SHA-256-Fingerabdruck zeigt die Play Console unter „App-Signatur“ (Play App Signing).
4. **Store-Eintrag:** Texte aus `listing.md`, Bilder aus diesem Ordner (`store-icon-512.png`, `feature-graphic-1024x500.png`, `screenshot-*.png`), Datenschutz-URL `https://wasessenwir.at/datenschutz.html`.
5. **Formulare:** Datensicherheit (Firebase speichert den geteilten Plan unter einer zufälligen Kennung, keine Konten), Inhaltseinstufung, Zielgruppe (Erwachsene/Familien), Werbung: nein.
6. **Test:** Geschlossener Test mit mindestens 12 Testern über 14 Tage am Stück (bei neuen privaten Konten; Zahl in der Play Console prüfen), dann Produktivfreigabe beantragen.
