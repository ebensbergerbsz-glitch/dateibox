# DateiBox 📦

Eine private Datei-Sharing Plattform für kleine Gruppen.

## Standard-Zugangsdaten (UNBEDINGT ÄNDERN!)

| Benutzer   | Passwort   |
|------------|------------|
| benutzer1  | passwort1  |
| benutzer2  | passwort2  |
| benutzer3  | passwort3  |
| benutzer4  | passwort4  |
| benutzer5  | passwort5  |

## Passwörter ändern

Öffne `app.py` und suche nach diesen Zeilen (ca. Zeile 40):

```python
users = [
    ('benutzer1', 'passwort1'),
    ('benutzer2', 'passwort2'),
    ...
]
```

Ändere die Benutzernamen und Passwörter nach Wunsch.

## Deployment auf Render.com

1. Diesen Code auf GitHub hochladen
2. Auf render.com → New Web Service → GitHub verbinden
3. Repository auswählen
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Environment Variable setzen: `SECRET_KEY` = (langer zufälliger Text)
7. Deploy!
