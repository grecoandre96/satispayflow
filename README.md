# 🚀 SatispayFlow - Deal Attribution System

## 📋 Panoramica

Sistema automatizzato per l'attribuzione corretta degli **Orders** ai **Sales Reps** attraverso il matching con i **Deals** vinti, utilizzando Python (FastAPI) e n8n per l'orchestrazione.

## 🎯 Problema da Risolvere

- **Sales Rep** possiede il **Deal** (opportunità di vendita), collegato alla **Company**
- **Order** viene importato da database esterno, collegato alla **Company** ma NON al Deal
- Una Company può avere più ordini
- Alcuni ordini sono self-service (senza intervento Sales Rep)

**Obiettivo**: Matchare automaticamente ogni Order al Deal "Won" corretto per attribuire la commissione al Sales Rep giusto.

---

## 🏗️ Architettura

```
┌─────────────────┐
│   Mock CRM      │ (Google Sheets / JSON)
│  - Companies    │
│  - Deals        │
│  - Orders       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         n8n Workflow (Orchestrator)      │
│  1. Fetch data from CRM                  │
│  2. Call Python Matching Service         │
│  3. Update CRM with attributions         │
│  4. Send notifications                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Python Matching Engine (FastAPI)      │
│  - Multi-level matching logic            │
│  - Confidence scoring                    │
│  - Audit trail                           │
└─────────────────────────────────────────┘
```

---

## 📁 Struttura del Progetto

```
satispayFlow/
├── matching-service/          # Python FastAPI service
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── models.py         # Pydantic models
│   │   ├── matching_engine.py # Core matching logic
│   │   ├── config.py         # Configuration
│   │   └── utils.py          # Helper functions
│   ├── tests/
│   │   └── test_matching.py  # Unit tests
│   └── requirements.txt
│
├── data/                      # Sample data for testing
│   ├── companies.json
│   ├── deals.json
│   ├── orders.json
│   └── attributions.json     # Output results
│
├── n8n/                       # n8n workflow exports
│   ├── workflow.json         # Main workflow
│   └── credentials.json      # Credentials template
│
├── docs/                      # Documentation
│   ├── architecture.md
│   ├── matching-logic.md
│   └── api-docs.md
│
├── docker-compose.yml         # Docker setup
└── README.md                  # This file
```

---

## 🔧 Stack Tecnologico

- **Python 3.11+** - Core logic
- **FastAPI** - REST API framework
- **pandas** - Data manipulation
- **pydantic** - Data validation
- **n8n** - Workflow automation
- **Docker** - Containerization(opzionale)

---

## 🚀 Quick Start

### 1. Setup Python Environment

```bash
cd matching-service
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Run Matching Service

```bash
cd matching-service
uvicorn app.main:app --reload
```

API disponibile su: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

### 3. Setup n8n (Docker)

```bash
docker-compose up -d
```

n8n disponibile su: `http://localhost:5678`

### 4. Import n8n Workflow

1. Apri n8n (`http://localhost:5678`)
2. Vai su "Workflows" → "Import from File"
3. Seleziona `n8n/workflow.json`

---

## 🎯 Logica di Matching

### Livello 1: Match Temporale + Valore (Priorità Alta)
- Order successivo a Deal "Won"
- Valore simile (±10% tolleranza)
- Entro 90 giorni dalla chiusura Deal

### Livello 2: Match Temporale Puro (Priorità Media)
- Deal "Won" più recente prima dell'Order
- Entro finestra temporale configurabile

### Livello 3: Self-Service Detection
- Valore sotto soglia minima
- Nessun Deal "Won" nella Company
- Order molto distante da qualsiasi Deal

### Confidence Score
```
Score = 100 punti base
- Differenza temporale: -1 punto/giorno
- Differenza valore: -10 punti per ogni 5% scostamento
- Deal unico nel periodo: +30 punti
```

Se Score < 70 → Flag per revisione manuale

---

## 📊 API Endpoints

### `POST /match-orders`
Match orders to deals

**Request:**
```json
{
  "companies": [...],
  "deals": [...],
  "orders": [...]
}
```

**Response:**
```json
{
  "matched": [...],
  "self_service": [...],
  "needs_review": [...]
}
```

### `GET /attribution/{order_id}`
Get attribution details for specific order

### `GET /health`
Health check endpoint

---

## 🧪 Testing

```bash
cd matching-service
pytest tests/ -v
```

---

## 📈 Metriche di Successo

- **Match Rate**: % di ordini matchati automaticamente
- **Confidence Score**: Media dei punteggi di confidenza
- **Manual Review Rate**: % ordini che richiedono revisione manuale
- **Processing Time**: Tempo medio di elaborazione

---

## 🔮 Sviluppi Futuri

- [ ] Machine Learning per migliorare matching
- [ ] Integrazione con CRM reali (HubSpot, Salesforce)
- [ ] Dashboard analytics
- [ ] Notifiche real-time
- [ ] A/B testing su algoritmi di matching

---

## 👤 Autore

Progetto sviluppato per colloquio tecnico - Demo di sistema di attribuzione automatica Deal-to-Order.

---

## 📝 License

MIT License - Free to use for educational purposes
