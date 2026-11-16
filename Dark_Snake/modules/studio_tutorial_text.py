"""Sidebar instructions for the bilingual FrostAge practice course."""

TUTORIAL_TITLE = "Mein erstes FrostAge-Level"

TUTORIAL_STEPS = (
    (
        ("Boden gestalten", "Paint the floor"),
        ("Layers → Ground. 1×1 unter FrostAge · Boden wählen. Drei markierte Felder bemalen.",
         "Layers → Ground. Pick a 1×1 tile under FrostAge · Ground. Paint three marked cells."),
        ("Halte die linke Maustaste gedrückt und ziehe quer über drei Felder im markierten Bereich.",
         "Hold the left mouse button and drag across three cells in the marked area."),
    ),
    (
        ("Hindernisse bauen", "Build obstacles"),
        ("Layers → Collision. Setze WALL auf ein markiertes Feld. Halte den Durchgang frei.",
         "Layers → Collision. Place WALL on a marked cell. Keep the passage clear."),
        ("Setze WALL auf das oberste markierte Feld. Probiere BARRIER daneben aus. Beide sperren den Weg, "
         "auch ohne Grafik.", "Put WALL on the top marked cell. Try BARRIER on another marked cell. "
         "Both block movement without needing artwork."),
    ),
    (
        ("Dach platzieren", "Place a roof"),
        ("Setze ein 4×4-Dach auf das markierte Feld. Blende es unter Layers aus und wieder ein. Öffne Learn.",
         "Place a 4×4 roof on the marked cell. Hide and show it under Layers. Return to Learn."),
        ("Wähle links unter FrostAge · Dächer ein 4×4-Dach. Schalte nach dem Setzen rechts unter Layers "
         "in der Zeile Roof die Sichtbarkeit zweimal um.",
         "Pick a 4×4 roof under FrostAge · Roofs. After placing it, open Layers on the right and toggle "
         "visibility twice in the Roof row."),
    ),
    (
        ("Ebenen verstehen", "Understand layers"),
        ("Layers → Ground. Sperre Boden, versuche ein markiertes Feld zu bemalen und entsperre Boden. Öffne Learn.",
         "Layers → Ground. Lock Ground, try painting a marked cell, then unlock it. Return to Learn."),
        ("Wähle eine andere FrostAge-Kachel und klicke mit gesperrtem Boden auf ein markiertes Feld. "
         "Der Bearbeitungsschutz lässt den Boden unverändert.",
         "Pick a different FrostAge tile and click a marked cell while Ground is locked. "
         "The lock keeps the floor unchanged."),
    ),
    (
        ("Level ausprobieren", "Try the level"),
        ("Starte den 1P-Test. Bewege die Schlange. Esc oder F2 beendet den Test.",
         "Start the 1P test. Move the snake and finish the test with Esc or F2."),
        ("Mit der Standardbelegung lenkt W Spieler 1 und ↑ Spieler 2. "
         "Nach dem 1P-Test kannst du auch den 2P-Test starten.",
         "With the default controls, W steers player 1 and ↑ steers player 2. "
         "After the 1P test, you can try 2P."),
    ),
)

TUTORIAL_EN = {source: english for step in TUTORIAL_STEPS for source, english in step}
TUTORIAL_EN.update({
    TUTORIAL_TITLE: "My First FrostAge Level",
    "Baue eine Übungskarte in fünf Schritten. Dein aktueller Entwurf bleibt erhalten.":
        "Build a practice map in five steps. Your current draft stays safe.",
    "Übung starten": "Start practice",
    "Schritt {step}/{total} · {checked} geprüft": "Step {step}/{total} · {checked} checked",
    "Glückwunsch! Dein erstes FrostAge-Level ist fertig.": "Congratulations! Your first FrostAge level is complete.",
    "Zurück zum Editor": "Return to editor",
    "Zurück": "Back",
    "Weiter": "Next",
    "Wiederholen": "Retry",
    "Beispiel": "Example",
    "Schließe diesen und die vorherigen Schritte ab.": "Complete this step and the previous ones.",
    "Öffne zuerst die vorherigen Schritte und prüfe ihre Aufgaben.":
        "Revisit the previous steps and check their tasks first.",
    "Test läuft": "Test running",
    "Esc oder F2 beendet den Test und zeigt deinen Fortschritt.": "Esc or F2 ends the test and shows your progress.",
    "Beende die Vorschau, um mit der Übung fortzufahren.": "Close the preview to continue the practice course.",
    "Test (1P)": "Test (1P)",
    "Test (2P)": "Test (2P)",
    "Starte den 1P-Test für diesen Schritt.": "Start the 1P test for this step.",
    "Probiere die Übungskarte zu zweit aus.": "Try the practice map with two players.",
})
