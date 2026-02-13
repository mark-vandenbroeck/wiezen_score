# Wiezen Score Tracker

Een moderne, web-gebaseerde score tracker voor het kaartspel **Wiezen**, gebouwd met Flask en SQLite. De applicatie biedt een premium dark-mode interface met real-time score updates en uitgebreide ondersteuning voor alle Wiezen contracten.

![Wiezen Score Tracker](/Users/mark/.gemini/antigravity/brain/563004b1-29f2-4d1e-b384-a7c9b642d7bf/open_wiezen_app_1770926639755.webp)

## 🎯 Features

### Spelbeheer
- **4 of 5 spelers**: Volledige ondersteuning voor zowel 4- als 5-speler varianten
- **Automatische dealer rotatie**: De dealer roteert automatisch na elke ronde
- **Zit-stil functie**: Bij 5 spelers zit de dealer automatisch stil

### Contracten
De applicatie ondersteunt alle standaard Wiezen contracten:
- **Vraag** (2 punten + extra slagen)
- **Troel** (2 punten + extra slagen, partner verplicht)
- **Abondance** (5 punten + extra slagen)
- **Solo** (13 punten)
- **Miserie** (10 punten)
- **Grote Miserie** (20 punten)
- **Multi-player Miserie**: Meerdere spelers kunnen tegelijk Miserie spelen

### Troefkeuze
- Verplichte troefkeuze voor Vraag, Troel, Abondance en Solo
- Visuele weergave met kaartkleur symbolen (♥ ♦ ♣ ♠)
- Troef wordt getoond in de ronde geschiedenis

### Score Berekening
- **Automatische puntentelling**: Alle scores worden automatisch berekend
- **Partner ondersteuning**: Correcte verdeling bij 2-tegen-2 scenario's
- **Extra slagen**: Ondersteuning voor overslagen met limieten
- **Verloren rondes**: Speciale berekening voor verloren contracten (undertricks)

### Gebruikersinterface
- **Premium dark mode**: Moderne, oogvriendelijke interface
- **Real-time updates**: Scores worden direct bijgewerkt
- **Responsive design**: Werkt op desktop en tablet
- **Nederlandse interface**: Volledig in het Nederlands
- **Validatie**: Uitgebreide invoervalidatie met Nederlandse foutmeldingen
- **Custom modals**: Betrouwbare dialoogvensters voor bewerken en verwijderen
- **Edit functionaliteit**: Rondes kunnen achteraf worden bewerkt met automatische score herberekening
- **Delete functionaliteit**: Rondes kunnen worden verwijderd met bevestiging


## 🚀 Installatie

### Vereisten
- Python 3.7 of hoger
- pip (Python package manager)

### Stappen

1. **Clone of download het project**
   ```bash
   cd /Users/mark/Documents/Python/Wiezen_score
   ```

2. **Installeer dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start de applicatie**
   ```bash
   python3 app.py
   ```

4. **Open in browser**
   ```
   http://localhost:5000
   ```

## 📖 Gebruik

### Een nieuw spel starten

1. Ga naar de homepage
2. Voer 4 of 5 spelersnamen in (of gebruik de standaard namen: Jan, Piet, Joris, Korneel)
3. Klik op "Start Spel"

### Een ronde toevoegen

1. Klik op "+ Nieuwe Ronde"
2. Selecteer het **Contract** (Vraag, Troel, Abondance, etc.)
3. Kies de **Troefkleur** (indien van toepassing)
4. Selecteer de **Speler** die het contract speelt
5. Kies eventueel een **Partner** (bij Vraag of Troel)
6. Selecteer het **Resultaat** (Gewonnen/Verloren)
7. Voer eventueel **Extra Slagen** in
8. Klik op "Opslaan"

### Een ronde bewerken

1. Klik op het **potlood icoon** (✏️) bij de ronde die je wilt bewerken
2. De edit modal opent met alle huidige gegevens vooraf ingevuld
3. Wijzig de gewenste velden (contract, troef, speler, resultaat, etc.)
4. Klik op "Opslaan"
5. De scores worden automatisch herberekend vanaf deze ronde

### Een ronde verwijderen

1. Klik op het **prullenbak icoon** (🗑️) bij de ronde die je wilt verwijderen
2. Bevestig de verwijdering in het dialoogvenster
3. De ronde wordt verwijderd en alle scores worden opnieuw berekend


### Speciale gevallen

#### Multi-player Miserie
Bij Miserie of Grote Miserie:
1. Selecteer het contract
2. Vink aan welke spelers meedoen
3. Selecteer voor elke speler of ze gewonnen of verloren hebben
4. De scores worden automatisch berekend voor alle combinaties

#### 5 Spelers
- De dealer zit automatisch stil en krijgt geen punten die ronde
- De dealer roteert na elke ronde

## 🎮 Spelregels & Puntentelling

### Basis Contracten

| Contract | Basis Punten | Extra Slagen | Partner | Troef |
|----------|--------------|--------------|---------|-------|
| Vraag | 2 | Max 5 (gewonnen) / 8 (verloren) | Optioneel | Verplicht |
| Troel | 2 | Max 5 (gewonnen) / 8 (verloren) | Verplicht | Verplicht |
| Abondance | 5 | Max 4 (gewonnen) / 9 (verloren) | Nee | Verplicht |
| Solo | 13 | Geen | Nee | Verplicht |
| Miserie | 10 | Geen | Nee | Nee |
| Grote Miserie | 20 | Geen | Nee | Nee |

### Score Berekening

**Gewonnen contract (zonder partner):**
- Speler: +(basis + extra slagen) × 3
- Anderen: -(basis + extra slagen)

**Gewonnen contract (met partner):**
- Speler & Partner: +(basis + extra slagen)
- Anderen: -(basis + extra slagen)

**Verloren contract:**
- Speler: -(basis + extra slagen) × 3 (zonder partner)
- Speler: -(basis + extra slagen) (met partner)
- Anderen: +(basis + extra slagen)

**Miserie:**
- Gewonnen: +10 × (aantal tegenstanders)
- Verloren: -10 × (aantal tegenstanders)
- Tegenstanders krijgen het omgekeerde

## 🛠️ Technische Details

### Architectuur

```
Wiezen_score/
├── app.py                 # Flask applicatie & routes
├── models.py              # Database modellen (SQLAlchemy)
├── test_app.py           # Unit tests
├── requirements.txt       # Python dependencies
├── wiezen.db             # SQLite database (auto-generated)
├── static/
│   └── css/
│       └── style.css     # Styling
└── templates/
    ├── base.html         # Base template
    ├── setup.html        # Game setup pagina
    └── index.html        # Main game interface
```

### Database Schema

**Game**
- `id`: Primary key
- `date`: Aanmaakdatum
- `is_active`: Boolean voor actief spel

**Player**
- `id`: Primary key
- `game_id`: Foreign key naar Game
- `name`: Spelersnaam

**Round**
- `id`: Primary key
- `game_id`: Foreign key naar Game
- `round_number`: Rondenummer
- `contract_type`: Type contract
- `result`: Gewonnen/Verloren
- `trump_suit`: Troefkleur (optioneel)
- `tricks`: Extra slagen
- `dealer_id`: Foreign key naar Player
- `sitter_id`: Foreign key naar Player (optioneel)
- `main_player_id`: Foreign key naar Player
- `partner_id`: Foreign key naar Player (optioneel)

**Score**
- `id`: Primary key
- `round_id`: Foreign key naar Round
- `player_id`: Foreign key naar Player
- `points_change`: Puntenverandering deze ronde
- `current_total`: Totale score na deze ronde

### Database Resilience

De applicatie bevat automatische database recovery:
- Bij opstarten wordt gecontroleerd of `wiezen.db` bestaat
- Als het bestand ontbreekt, wordt het automatisch aangemaakt
- Bij elke request wordt gecontroleerd of de database nog bestaat
- Dit voorkomt "no such table" fouten

## 🧪 Testing

### Unit Tests Uitvoeren

```bash
python3 -m unittest test_app.py
```

### Test Coverage

De test suite bevat:
- ✅ Game flow tests (start game, add rounds, score calculation)
- ✅ Partner scoring tests (2v2 scenarios)
- ✅ Multi-player Miserie tests
- ✅ Validation tests (self-partner prevention, trick limits)
- ✅ Mandatory trump selection tests
- ✅ Database recovery tests

## 🎨 Styling & Design

### Design Principes
- **Dark Mode First**: Oogvriendelijke donkere interface
- **Neon Accents**: Levendige neon groene accenten (#00e676)
- **Modern Typography**: Inter font family
- **Responsive**: Werkt op verschillende schermformaten
- **Glassmorphism**: Subtiele transparantie effecten

### Kleurenschema

```css
--bg-color: #121212        /* Achtergrond */
--card-bg: #1e1e1e        /* Kaart achtergrond */
--text-primary: #ffffff    /* Primaire tekst */
--text-secondary: #b3b3b3  /* Secundaire tekst */
--accent-color: #00e676    /* Neon groen accent */
--danger-color: #ff5252    /* Rood voor danger */
```

## 🔧 Configuratie

### Standaard Spelersnamen

De applicatie gebruikt standaard de namen: **Jan, Piet, Joris, Korneel**

Deze kunnen worden aangepast in `app.py`:
```python
if not player_names:
    player_names = ['Jan', 'Piet', 'Joris', 'Korneel']
```

### Database Locatie

De database wordt standaard opgeslagen als `wiezen.db` in de project directory.

Wijzig in `app.py` om een andere locatie te gebruiken:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pad/naar/wiezen.db'
```

## 📝 Ontwikkeling

### Nieuwe Features Toevoegen

1. **Database wijzigingen**: Update `models.py`
2. **Backend logic**: Voeg routes toe in `app.py`
3. **Frontend**: Pas `index.html` aan
4. **Styling**: Update `style.css`
5. **Tests**: Voeg tests toe in `test_app.py`

### Debug Mode

De applicatie draait standaard in debug mode. Voor productie:

```python
if __name__ == '__main__':
    app.run(debug=False)
```

## 🐛 Troubleshooting

### Database Errors

**"no such table: game"**
- De database wordt automatisch opnieuw aangemaakt
- Ververs de pagina in je browser

### Port Already in Use

```bash
# Vind en stop het proces op poort 5000
lsof -ti:5000 | xargs kill -9

# Start de applicatie opnieuw
python3 app.py
```

### Styling Updates Niet Zichtbaar

- Hard refresh in browser: `Cmd + Shift + R` (Mac) of `Ctrl + Shift + R` (Windows)
- Clear browser cache

## 📄 Licentie

Dit project is ontwikkeld voor persoonlijk gebruik.

## 🤝 Bijdragen

Dit is een persoonlijk project. Voor vragen of suggesties, neem contact op met de ontwikkelaar.

## 📞 Contact

Voor vragen of ondersteuning, raadpleeg de documentatie of bekijk de code comments in de bronbestanden.

---

**Veel plezier met Wiezen! 🎴**
