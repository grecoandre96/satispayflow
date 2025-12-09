# 🚀 GUIDA COMPLETA - Dal Codice al Funzionamento

**Questa guida ti porta da ZERO a un sistema funzionante in ~30 minuti.**

---

## 📚 Indice

1. [Cosa Abbiamo Costruito](#cosa-abbiamo-costruito)
2. [Prerequisiti](#prerequisiti)
3. [PARTE 1: Test in Locale](#parte-1-test-in-locale)
4. [PARTE 2: Deploy su Render (Cloud)](#parte-2-deploy-su-render-cloud)
5. [PARTE 3: Collegare n8n](#parte-3-collegare-n8n)
6. [PARTE 4: Test Completo](#parte-4-test-completo)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Cosa Abbiamo Costruito

Un sistema che:
1. **Riceve** dati di Companies, Deals e Orders
2. **Matcha** automaticamente gli Orders ai Deals giusti
3. **Restituisce** risultati con Sales Rep attribuiti

```
Dati → Python API (FastAPI) → Risultati con attribuzioni
         ↑
    n8n chiama questa API
```

---

## ✅ Prerequisiti

### Cosa ti serve:

- [ ] **Python 3.11** installato ([Download](https://www.python.org/downloads/))
- [ ] **Account GitHub** gratuito ([Crea qui](https://github.com/signup))
- [ ] **Account Render** gratuito ([Crea qui](https://render.com/))
- [ ] **Account n8n Cloud** trial ([Crea qui](https://n8n.io/cloud/))
- [ ] **Git** installato ([Download](https://git-scm.com/downloads))

### Verifica Python:
```bash
python --version
# Deve mostrare: Python 3.11.x o superiore
```

---

## 📍 PARTE 1: Test in Locale

**Obiettivo**: Verificare che il codice funzioni sul tuo computer.

### Step 1.1: Apri il Terminale

1. Premi `Win + R`
2. Digita `cmd` e premi Invio
3. Vai nella cartella del progetto:
   ```bash
   cd C:\Users\utente\.gemini\antigravity\scratch\satispayFlow
   ```

### Step 1.2: Crea Ambiente Virtuale Python

```bash
cd matching-service
python -m venv venv
```

**Cosa fa**: Crea un ambiente isolato per le librerie Python.

### Step 1.3: Attiva l'Ambiente Virtuale

```bash
venv\Scripts\activate
```

**Vedrai**: `(venv)` prima del prompt del terminale.

### Step 1.4: Installa le Dipendenze

```bash
pip install -r requirements.txt
```

**Cosa fa**: Installa FastAPI, pandas, e tutte le librerie necessarie.

**Tempo**: ~2 minuti

### Step 1.5: Testa con lo Script Demo

```bash
python demo.py
```

**Cosa aspettarsi**: Vedrai un output simile a questo:

```
🚀 SatispayFlow - Deal Attribution Demo
========================================

📂 Loading sample data...
✅ Loaded 5 companies, 7 deals, 10 orders

🔄 Running matching engine...

========================================
📊 RESULTS SUMMARY
========================================
Total Orders:        10
✅ Matched:          6 (60.0%)
🤖 Self-Service:     3
⚠️  Needs Review:     1
```

**✅ Se vedi questo, il codice funziona!**

### Step 1.6: Avvia il Server API

```bash
uvicorn app.main:app --reload
```

**Cosa aspettarsi**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 1.7: Testa l'API

1. Apri il browser
2. Vai su: `http://localhost:8000/docs`
3. Vedrai la documentazione interattiva (Swagger)

**Prova l'API**:
1. Clicca su `POST /match-orders`
2. Clicca su "Try it out"
3. Clicca su "Execute"
4. Vedrai la risposta JSON

**✅ Se funziona, sei pronto per il deploy!**

**Ferma il server**: Premi `Ctrl + C` nel terminale

---

## 🌐 PARTE 2: Deploy su Render (Cloud)

**Obiettivo**: Mettere l'API online così n8n può chiamarla.

### Step 2.1: Prepara il Progetto per Git

Nel terminale (dalla cartella `satispayFlow`):

```bash
cd ..
git init
git add .
git commit -m "Initial commit - SatispayFlow"
```

**Cosa fa**: Prepara il codice per essere caricato su GitHub.

### Step 2.2: Crea Repository su GitHub

1. Vai su [github.com](https://github.com)
2. Clicca sul `+` in alto a destra → "New repository"
3. Nome repository: `satispayflow`
4. Lascia tutto il resto come default
5. Clicca "Create repository"

### Step 2.3: Carica il Codice su GitHub

**Copia i comandi** che GitHub ti mostra (simili a questi):

```bash
git remote add origin https://github.com/TUO-USERNAME/satispayflow.git
git branch -M main
git push -u origin main
```

**Incolla nel terminale** e premi Invio.

**Cosa fa**: Carica il tuo codice su GitHub.

**✅ Verifica**: Ricarica la pagina GitHub, dovresti vedere i tuoi file.

### Step 2.4: Crea Account Render

1. Vai su [render.com](https://render.com/)
2. Clicca "Get Started for Free"
3. Scegli "Sign up with GitHub"
4. Autorizza Render ad accedere a GitHub

### Step 2.5: Crea Web Service su Render

1. Nella dashboard Render, clicca "New +"
2. Seleziona "Web Service"
3. Clicca "Connect" accanto al repository `satispayflow`
4. Compila il form:

   **Name**: `satispayflow` (o quello che vuoi)
   
   **Region**: `Frankfurt (EU Central)` (più vicino all'Italia)
   
   **Branch**: `main`
   
   **Root Directory**: lascia vuoto
   
   **Runtime**: `Python 3`
   
   **Build Command**: 
   ```
   cd matching-service && pip install -r requirements.txt
   ```
   
   **Start Command**:
   ```
   cd matching-service && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   
   **Instance Type**: `Free`

5. Clicca "Create Web Service"

### Step 2.6: Aspetta il Deploy

**Cosa succede**:
- Render scarica il tuo codice
- Installa le dipendenze
- Avvia l'API

**Tempo**: 3-5 minuti

**Vedrai i log** in tempo reale. Aspetta fino a vedere:
```
==> Your service is live 🎉
```

### Step 2.7: Ottieni l'URL Pubblico

1. In alto nella pagina Render vedrai l'URL, tipo:
   ```
   https://satispayflow.onrender.com
   ```

2. **Copia questo URL** - lo userai con n8n!

### Step 2.8: Testa l'API Online

Apri il browser e vai su:
```
https://TUO-URL.onrender.com/docs
```

**Dovresti vedere** la stessa documentazione Swagger di prima!

**Prova l'API**:
1. Clicca su `GET /health`
2. Clicca "Try it out" → "Execute"
3. Dovresti vedere: `{"status": "healthy"}`

**✅ L'API è online e funzionante!**

---

## 🔗 PARTE 3: Collegare n8n

**Obiettivo**: Creare un workflow n8n che chiama la tua API.

### Step 3.1: Accedi a n8n Cloud

1. Vai su [n8n.io/cloud](https://n8n.io/cloud/)
2. Accedi al tuo account trial
3. Clicca "New Workflow"

### Step 3.2: Crea il Workflow Base

**Aggiungi nodi in questo ordine**:

#### Nodo 1: Manual Trigger
1. Clicca sul `+` per aggiungere nodo
2. Cerca "Manual Trigger"
3. Selezionalo

#### Nodo 2: HTTP Request (Prepara Dati)
1. Clicca sul `+` dopo Manual Trigger
2. Cerca "HTTP Request"
3. Configura:
   - **Method**: `GET`
   - **URL**: `https://raw.githubusercontent.com/TUO-USERNAME/satispayflow/main/data/companies.json`

**Nota**: Questo è solo per la demo. In produzione leggeresti dal CRM.

#### Nodo 3: Code (Prepara Payload)
1. Aggiungi nodo "Code"
2. Incolla questo codice:

```javascript
// Prepara i dati per l'API di matching
const companies = [
  {
    "id": "comp_001",
    "name": "TechCorp Solutions",
    "created_at": "2024-01-15T10:00:00Z"
  }
];

const deals = [
  {
    "id": "deal_001",
    "company_id": "comp_001",
    "sales_rep_id": "rep_alice",
    "sales_rep_name": "Alice Johnson",
    "amount": 15000.0,
    "status": "Won",
    "close_date": "2024-06-15T16:30:00Z",
    "created_at": "2024-05-01T10:00:00Z"
  }
];

const orders = [
  {
    "id": "order_001",
    "company_id": "comp_001",
    "amount": 15200.0,
    "order_date": "2024-06-25T10:00:00Z",
    "products": ["Product A", "Product B"]
  }
];

return {
  json: {
    companies: companies,
    deals: deals,
    orders: orders
  }
};
```

#### Nodo 4: HTTP Request (Chiama API)
1. Aggiungi nodo "HTTP Request"
2. Configura:
   - **Method**: `POST`
   - **URL**: `https://TUO-URL.onrender.com/match-orders`
   - **Send Body**: ✅ Attiva
   - **Body Content Type**: `JSON`
   - **Specify Body**: `Using JSON`
   - **JSON**: `={{ $json }}`

### Step 3.3: Salva il Workflow

1. Clicca "Save" in alto a destra
2. Nome: "SatispayFlow - Order Attribution"

### Step 3.4: Testa il Workflow

1. Clicca "Execute Workflow" (o "Test Workflow")
2. Aspetta qualche secondo
3. Dovresti vedere i risultati!

**Output atteso**:
```json
{
  "matched": [
    {
      "order_id": "order_001",
      "deal_id": "deal_001",
      "sales_rep_name": "Alice Johnson",
      "confidence_score": 96.5
    }
  ],
  "self_service": [],
  "needs_review": [],
  "summary": {
    "total_orders": 1,
    "matched_count": 1,
    "match_rate_percent": 100.0
  }
}
```

**✅ Funziona! n8n sta chiamando la tua API su Render!**

---

## 🧪 PARTE 4: Test Completo

### Test 1: Ordine con Match Perfetto

Nel nodo Code di n8n, prova questo:

```javascript
const orders = [
  {
    "id": "order_001",
    "company_id": "comp_001",
    "amount": 15200.0,  // Vicino a 15000
    "order_date": "2024-06-25T10:00:00Z"  // 10 giorni dopo deal
  }
];
```

**Risultato atteso**: Match con alta confidenza (>90%)

### Test 2: Ordine Self-Service

```javascript
const orders = [
  {
    "id": "order_002",
    "company_id": "comp_001",
    "amount": 300.0,  // Sotto soglia €500
    "order_date": "2024-06-25T10:00:00Z"
  }
];
```

**Risultato atteso**: Classificato come `self_service`

### Test 3: Ordine che Richiede Revisione

```javascript
const orders = [
  {
    "id": "order_003",
    "company_id": "comp_001",
    "amount": 50000.0,  // Molto diverso da 15000
    "order_date": "2024-06-25T10:00:00Z"
  }
];
```

**Risultato atteso**: In `needs_review` con bassa confidenza

---

## 🐛 Troubleshooting

### Problema: "Module not found" in locale

**Soluzione**:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Problema: Render deploy fallisce

**Controlla**:
1. Build Command è corretto?
2. Start Command è corretto?
3. Guarda i log su Render per errori specifici

**Soluzione comune**:
- Vai su Render → Settings → Build & Deploy
- Verifica i comandi

### Problema: n8n non riesce a chiamare l'API

**Controlla**:
1. L'URL Render è corretto? (copia-incolla)
2. L'API è "live" su Render? (controlla dashboard)
3. Hai aspettato che Render finisse il deploy?

**Test manuale**:
Apri browser e vai su: `https://TUO-URL.onrender.com/health`

Dovresti vedere: `{"status":"healthy"}`

### Problema: API lenta (30 secondi per rispondere)

**Causa**: Render free tier va in "sleep" dopo 15 min di inattività.

**Soluzione**: 
- Prima richiesta sarà lenta (~30 sec)
- Richieste successive saranno veloci
- Normale per tier gratuito!

### Problema: Git push fallisce

**Soluzione**:
```bash
git config --global user.email "tua@email.com"
git config --global user.name "Tuo Nome"
git push -u origin main
```

---

## 🎉 Congratulazioni!

Hai:
- ✅ Testato il codice in locale
- ✅ Deployato l'API su Render (cloud)
- ✅ Creato un workflow n8n
- ✅ Collegato n8n all'API
- ✅ Testato il sistema end-to-end

**Il tuo sistema è FUNZIONANTE!** 🚀

---

## 📝 Per il Colloquio

### Cosa Mostrare:

1. **Swagger Docs**: `https://TUO-URL.onrender.com/docs`
2. **n8n Workflow**: Mostra il workflow visuale
3. **Risultati**: Esegui il workflow e mostra i risultati
4. **Codice**: Mostra `matching_engine.py`

### URL da Condividere:

- **API Live**: `https://TUO-URL.onrender.com`
- **GitHub Repo**: `https://github.com/TUO-USERNAME/satispayflow`
- **API Docs**: `https://TUO-URL.onrender.com/docs`

---

## 🆘 Serve Aiuto?

Se qualcosa non funziona:

1. **Controlla i log** su Render
2. **Testa l'API** manualmente con `/docs`
3. **Verifica** che tutti i file siano su GitHub
4. **Rileggi** la sezione Troubleshooting


