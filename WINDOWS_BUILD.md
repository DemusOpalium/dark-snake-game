# DARK Snake · Windows-Build und Downloadprüfung

## Befund am bisherigen Build

Geprüft wurde das von GitHub Actions archivierte Windows-Paket für `main` bei `ff382f69c4c9f25b029980c78a2b784460758eaa`. Der SHA-256 des äußeren Actions-Archivs stimmt mit dem GitHub-Digest überein. Beide Archive bestanden die ZIP-Integritätsprüfung. Das innere ZIP enthielt die EXE, Startanleitung, die unveränderte MIT-Lizenz und Hinweise für Python und PyInstaller. Ein pygame-Lizenztext fehlte in diesem Paket. Die EXE war unsigniert und hatte keine Angaben zu Produktname, Version, Hersteller oder Copyright. [GitHub-Build des Ausgangsstands](https://github.com/DemusOpalium/dark-snake-game/actions/runs/42690975777)

| Geprüfte Datei | SHA-256 |
| --- | --- |
| Äußeres GitHub-Actions-Archiv | `666cd21e79c9147edf72229b145590bed915b5f6a6c6f5547ce03cec16240778` |
| Enthaltenes `DARK-Snake-v1.0.0-Windows-x64.zip` | `5b48c7ae8c3d57e61f8d8526e7dd8cae9b8642fdf723fd791564aff0156d0808` |
| Darin enthaltene `DARK-Snake.exe` | `afbaac7a77d39c69847c9e4f032b22614ab1b33d5327214951af4c025aa60b97` |

Die konkret beanstandete Downloadadresse, der exakte Warntext und der SHA-256 der beanstandeten Datei liegen nicht vor. Daher ist offen, ob Firefox genau dieses Artefakt bewertet hat. Die Meldung des Entwicklers, dass Defender keine Bedrohung gefunden hat, ist ein separates Prüfergebnis. Auch ein übereinstimmender Hash belegt nur die Gleichheit mit der Referenzdatei. Firefox unterscheidet unter anderem zwischen Malware, unerwünschter Software und selten heruntergeladenen Dateien und nutzt Google Safe Browsing für die Downloadprüfung. Eine neue EXE kann eine andere Prüfsumme und eine andere Einstufung haben. Das erklärt eine mögliche Änderung der Bewertung, belegt sie für diesen Fall aber nicht. [Mozilla zur Downloadprüfung](https://support.mozilla.org/en-US/kb/where-find-and-manage-downloaded-files-firefox#download-protection)

Der alte Workflow installierte PyInstaller ohne feste Version, aktualisierte pip und verwendete veränderliche Action-Tags. Der neue Windows-Workflow bindet die Actions an überprüfte Commit-SHAs, verwendet Lesezugriff und legt keine Checkout-Anmeldedaten im Arbeitsverzeichnis ab. `requirements-windows-build.txt` bindet die Windows-Wheels einschließlich der transitiven Abhängigkeiten an Version und SHA-256. Der Build verwendet weiterhin die PyInstaller-Onefile-Variante. Diese Verpackungsform allein erlaubt keine Aussage darüber, warum Firefox den Download gemeldet hat. [GitHub zur Absicherung von Actions](https://docs.github.com/en/actions/reference/security/secure-use)

## Das Build-Paket prüfen

1. Das ZIP und die zugehörige `.zip.sha256` aus **demselben** GitHub-Actions-Lauf oder offiziellen Release verwenden. Bei Actions liegen diese beiden Dateien im äußeren Download-Archiv `dark-snake-windows-zip`. Die Prüfsumme bezieht sich auf das darin enthaltene Spiel-ZIP.
2. In PowerShell den SHA-256 der Spiel-ZIP berechnen und mit den ersten 64 Zeichen der Prüfsummendatei vergleichen.

   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath .\DARK-Snake-v1.0.0-Windows-x64.zip
   Get-Content -LiteralPath .\DARK-Snake-v1.0.0-Windows-x64.zip.sha256
   ```

3. Im Spiel-ZIP nennt `BUILD.json` Quellcommit, Python-Version, die Versionen von pygame und PyInstaller sowie die Prüfsumme der enthaltenen EXE. Die Eigenschaften der EXE zeigen `DARK Snake`, Produktversion `1.0.0`, Hersteller `DemusOpalium` und den Copyright-Hinweis aus der MIT-Lizenz. Das Herstellerfeld ist eine Metadatenangabe. Eine verifizierte Herausgeberidentität setzt eine gültige Authenticode-Signatur voraus.

## Build nachvollziehen

Der [Windows-Workflow](.github/workflows/python-app.yml) enthält die vollständigen Schritte. Ein sauberer Windows-x64-Checkout mit CPython 3.12 und dem Commit aus `BUILD.json` ist der Ausgangspunkt. Für einen Vergleich dieselbe Python-Patchversion und Runner-Umgebung verwenden. Der Workflow setzt den PE-Zeitstempel aus dem Quellcommit und hält ZIP-Reihenfolge und ZIP-Metadaten fest. Bei identischer EXE und denselben Build-Eingaben erzeugt der ZIP-Test identische Archive. Das GitHub-Runner-Image und die Python-Patchversion können sich weiter ändern. Byteidentische EXEs auf unterschiedlichen Runnern sind damit noch nicht nachgewiesen.

Für eine spätere Veröffentlichung das endgültige Spiel-ZIP samt zugehöriger SHA-256-Datei gemeinsam als Assets bereitstellen. Ein Actions-Artefakt ist zeitlich begrenzt. Der Archiv-Digest von GitHub bezieht sich auf die äußere Datei. Er ersetzt den SHA-256 des Spiel-ZIP nicht.

## Mögliche Falschmeldung untersuchen

1. Die Warnung stehen lassen. Firefox-Version, Windows-Version, Zeitpunkt, exakten Meldungstext und ursprüngliche Downloadadresse notieren. Falls die Datei bereits lokal vorliegt, ihren SHA-256 berechnen. Bei abweichender Prüfsumme die Datei nicht ausführen und den Downloadpfad prüfen.
2. Für eine gemeldete URL den offiziellen Safe-Browsing-Kanal verwenden. Bei einer selbst verwalteten Website kann der Betreiber eine Überprüfung über Search Console beantragen. Bei einem GitHub-Artefakt die stabile öffentliche Build- oder Release-URL angeben. Temporäre signierte Downloadlinks, Zugangsdaten und persönliche Pfade gehören nicht in eine öffentliche Meldung. [Safe-Browsing-Korrekturformular](https://safebrowsing.google.com/safebrowsing/report_error/) · [Google zur Überprüfung schädlicher Downloads](https://support.google.com/webmasters/answer/9044101)
3. Wenn sich die Warnung in Firefox mit dem offiziellen Paket reproduzieren lässt und unklar bleibt, ob URL oder Datei betroffen ist, den Fall mit Warntext, stabiler URL und SHA-256 an Mozilla melden. In Bugzilla gibt es dafür den Bereich **Toolkit → Safe Browsing**. [Mozilla zur Fehlermeldung](https://bugzilla.mozilla.org/page.cgi?id=bug-writing.html) · [Beispiel für den zuständigen Bereich](https://bugzilla.mozilla.org/show_bug.cgi?id=1623959)

## Codesignierung

Für eine öffentliche Windows-EXE kommen ein öffentlich vertrauenswürdiges Codesignaturzertifikat mit SignTool oder Microsofts verwaltetes Artifact Signing mit geprüfter Herausgeberidentität infrage. Vor der Auswahl sind Identitätsprüfung und Verfügbarkeit für den Herausgeber zu klären. Eine Signatur belegt Herausgeber und Integrität, sie garantiert keine bestimmte Browserbewertung. Ein selbstsigniertes Zertifikat liefert im öffentlichen Download keinen allgemein vertrauenswürdigen Herausgeber.

Die Reihenfolge für einen späteren Signierschritt ist **EXE bauen → EXE signieren und mit RFC-3161/SHA-256 zeitstempeln → Signatur prüfen → ZIP packen → SHA-256 des endgültigen ZIP erzeugen**. Signierzugriff gehört nur in einen geschützten Veröffentlichungsjob. Der PR-Build ist unsigniert. [Microsoft SignTool](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool) · [Microsoft zur Authenticode-Zeitstempelung](https://learn.microsoft.com/en-us/windows/win32/seccrypto/time-stamping-authenticode-signatures) · [Microsoft Artifact Signing](https://learn.microsoft.com/en-us/azure/artifact-signing/faq)
