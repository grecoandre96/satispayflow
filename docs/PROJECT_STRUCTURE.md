# 📦 Struttura Progetto SatispayFlow

```
satispayFlow/
│
├── 📄 README.md                    # Panoramica del progetto
├── 📄 .gitignore                   # File da ignorare in Git
├── 📄 Procfile                     # Config per Render deploy
├── 📄 start.sh                     # Script avvio per Render
├── 📄 runtime.txt                  # Versione Python per Render
├── 📄 docker-compose.yml           # Config Docker (opzionale)
│
├── 📁 matching-service/            # ⭐ CORE: API Python
│   ├── 📄 requirements.txt         # Dipendenze Python
│   ├── 📄 .env.example             # Template variabili ambiente
│   ├── 📄 demo.py                  # Script demo per test locale
│   │
│   ├── 📁 app/                     # Codice applicazione
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py              # ⭐ FastAPI app + endpoints
│   │   ├── 📄 models.py            # ⭐ Modelli dati (Pydantic)
│   │   ├── 📄 matching_engine.py   # ⭐ LOGICA MATCHING
│   │   ├── 📄 config.py            # Configurazione
│   │   └── 📄 utils.py             # Funzioni helper
│   │
│   └── 📁 tests/                   # Test unitari
│       ├── 📄 __init__.py
│       └── 📄 test_matching.py     # Test logica matching
│
├── 📁 data/                        # Dati di esempio
│   ├── 📄 companies.json           # Aziende di test
│   ├── 📄 deals.json               # Deal di test
│   ├── 📄 orders.json              # Ordini di test
│   └── 📄 sample_request.json      # Esempio richiesta API
│
├── 📁 n8n/                         # Workflow n8n
│   └── 📄 workflow.json            # Export workflow n8n
│
└── 📁 docs/                        # 📚 Documentazione
    ├── 📄 QUICKSTART.md            # ⭐ GUIDA PASSO-PASSO
    ├── 📄 PRESENTATION_GUIDE.md    # ⭐ CHECKLIST COLLOQUIO
    ├── 📄 architecture.md          # Architettura sistema
    └── 📄 matching-logic.md        # Dettagli algoritmo
```

---

## 🎯 File Chiave da Conoscere

### Per Sviluppo
1. **`matching-service/app/matching_engine.py`** - Logica principale
2. **`matching-service/app/models.py`** - Strutture dati
3. **`matching-service/app/main.py`** - API endpoints
4. **`matching-service/demo.py`** - Test rapido

### Per Deploy
1. **`Procfile`** - Dice a Render come avviare l'app
2. **`requirements.txt`** - Librerie Python necessarie
3. **`runtime.txt`** - Versione Python da usare

### Per Documentazione
1. **`docs/QUICKSTART.md`** - ⭐ INIZIA DA QUI
2. **`docs/PRESENTATION_GUIDE.md`** - Checklist colloquio
3. **`README.md`** - Panoramica generale

### Per Testing
1. **`data/sample_request.json`** - Esempio richiesta API
2. **`matching-service/tests/test_matching.py`** - Test automatici

---

## 🚀 Workflow Tipico

### Sviluppo Locale
```
1. Modifica codice in matching-service/app/
2. Testa con: python demo.py
3. Avvia API: uvicorn app.main:app --reload
4. Testa su: http://localhost:8000/docs
```

### Deploy su Render
```
1. Commit modifiche: git add . && git commit -m "Update"
2. Push su GitHub: git push
3. Render fa deploy automatico
4. Verifica su: https://TUO-URL.onrender.com/docs
```

### Test con n8n
```
1. Apri n8n Cloud
2. Apri workflow "SatispayFlow"
3. Clicca "Execute Workflow"
4. Verifica risultati
```

---

## 📊 Flusso dei Dati

```
1. DATI IN INGRESSO (data/*.json)
   ↓
2. ELABORAZIONE (matching_engine.py)
   ↓
3. VALIDAZIONE (models.py)
   ↓
4. API RESPONSE (main.py)
   ↓
5. RISULTATI (matched, self_service, needs_review)
```

---

## 🔍 Dove Trovare Cosa

### "Voglio capire l'algoritmo di matching"
→ `docs/matching-logic.md`
→ `matching-service/app/matching_engine.py`

### "Voglio testare in locale"
→ `docs/QUICKSTART.md` (Parte 1)
→ `matching-service/demo.py`

### "Voglio deployare su Render"
→ `docs/QUICKSTART.md` (Parte 2)

### "Voglio collegare n8n"
→ `docs/QUICKSTART.md` (Parte 3)

### "Voglio prepararmi per il colloquio"
→ `docs/PRESENTATION_GUIDE.md`

### "Voglio capire l'architettura"
→ `docs/architecture.md`

### "Voglio modificare i parametri di matching"
→ `matching-service/app/config.py`
→ `matching-service/.env.example`

### "Voglio aggiungere test"
→ `matching-service/tests/test_matching.py`

---

## 💡 File Generati Automaticamente

Questi file vengono creati quando esegui i comandi:

- **`venv/`** - Ambiente virtuale Python (dopo `python -m venv venv`)
- **`__pycache__/`** - Cache Python (ignorato da Git)
- **`data/attributions.json`** - Risultati del demo script

**Non committare questi file su Git!** (già in `.gitignore`)

---

## 🎨 Personalizzazione

### Cambiare Parametri di Matching
Modifica `matching-service/app/config.py`:
```python
time_window_days: int = 90        # Finestra temporale
value_tolerance_percent: float = 10.0  # Tolleranza valore
self_service_threshold: float = 500.0  # Soglia self-service
```

### Aggiungere Nuovi Dati di Test
Modifica i file in `data/`:
- `companies.json` - Aggiungi aziende
- `deals.json` - Aggiungi deal
- `orders.json` - Aggiungi ordini

### Modificare Logica di Matching
Modifica `matching-service/app/matching_engine.py`:
- `_find_temporal_value_match()` - Match livello 1
- `_find_temporal_match()` - Match livello 2
- `_calculate_confidence_score()` - Scoring

---

## 🔧 Comandi Utili

### Sviluppo
```bash
# Attiva ambiente virtuale
venv\Scripts\activate

# Installa dipendenze
pip install -r requirements.txt

# Avvia server
uvicorn app.main:app --reload

# Esegui test
pytest tests/ -v

# Esegui demo
python demo.py
```

### Git
```bash
# Stato modifiche
git status

# Commit modifiche
git add .
git commit -m "Descrizione modifiche"

# Push su GitHub
git push

# Vedi log
git log --oneline
```

### Render
```bash
# Trigger manuale deploy (dopo push)
# Vai su dashboard Render → Manual Deploy

# Vedi log
# Dashboard Render → Logs tab
```

---

## 📚 Risorse Esterne

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **n8n Docs**: https://docs.n8n.io/
- **Render Docs**: https://render.com/docs
- **Python Docs**: https://docs.python.org/3/

---

## ✅ Checklist File Essenziali

Prima di fare commit, assicurati di avere:

- [x] `README.md` - Panoramica
- [x] `requirements.txt` - Dipendenze
- [x] `Procfile` - Config Render
- [x] `runtime.txt` - Versione Python
- [x] `.gitignore` - File da ignorare
- [x] `matching-service/app/main.py` - API
- [x] `matching-service/app/matching_engine.py` - Logica
- [x] `matching-service/app/models.py` - Modelli
- [x] `docs/QUICKSTART.md` - Guida
- [x] `data/*.json` - Dati di test

---

## 🎯 Prossimi Passi

1. ✅ Leggi `docs/QUICKSTART.md`
2. ✅ Testa in locale (Parte 1)
3. ✅ Deploy su Render (Parte 2)
4. ✅ Collega n8n (Parte 3)
5. ✅ Prepara colloquio con `docs/PRESENTATION_GUIDE.md`

**Buon lavoro!** 🚀
