# 🏗️ System Architecture

## Overview

SatispayFlow is a **microservices-based** attribution system that automatically matches Orders to Deals for accurate Sales Rep commission tracking.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Companies   │  │    Deals     │  │   Orders     │          │
│  │   (CRM)      │  │   (CRM)      │  │ (External DB)│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
          ┌──────────────────────────────────────┐
          │     n8n Workflow Orchestrator        │
          │  ┌────────────────────────────────┐  │
          │  │ 1. Schedule Trigger (Cron)     │  │
          │  │ 2. Fetch Data from CRM         │  │
          │  │ 3. Health Check API            │  │
          │  │ 4. Call Matching Service       │  │
          │  │ 5. Process Results             │  │
          │  │ 6. Update CRM                  │  │
          │  │ 7. Send Notifications          │  │
          │  └────────────────────────────────┘  │
          └──────────────┬───────────────────────┘
                         │ HTTP POST
                         │ /match-orders
                         ▼
          ┌──────────────────────────────────────┐
          │   Python Matching Service (FastAPI)  │
          │  ┌────────────────────────────────┐  │
          │  │  Matching Engine               │  │
          │  │  ├─ Level 1: Temporal + Value  │  │
          │  │  ├─ Level 2: Temporal Only     │  │
          │  │  └─ Level 3: Self-Service      │  │
          │  │                                 │  │
          │  │  Confidence Scoring             │  │
          │  │  Audit Trail Logging            │  │
          │  └────────────────────────────────┘  │
          └──────────────┬───────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │         OUTPUT & STORAGE              │
          │  ┌────────────────────────────────┐  │
          │  │ Matched Attributions           │  │
          │  │ Self-Service Orders            │  │
          │  │ Manual Review Queue            │  │
          │  │ Audit Logs                     │  │
          │  └────────────────────────────────┘  │
          └──────────────────────────────────────┘
```

---

## Components

### 1. **Data Sources**

#### Companies
- **Source**: CRM (HubSpot, Salesforce, etc.)
- **Fields**: `id`, `name`, `created_at`
- **Purpose**: Link Deals and Orders

#### Deals
- **Source**: CRM
- **Fields**: `id`, `company_id`, `sales_rep_id`, `amount`, `status`, `close_date`
- **Filter**: Only "Won" deals are considered
- **Purpose**: Sales opportunities that should receive attribution

#### Orders
- **Source**: External database / E-commerce platform
- **Fields**: `id`, `company_id`, `amount`, `order_date`, `products`
- **Purpose**: Completed purchases to be attributed

---

### 2. **n8n Workflow Orchestrator**

**Role**: Automation and integration layer

**Responsibilities**:
- Schedule periodic matching runs (e.g., every 6 hours)
- Fetch data from CRM and external sources
- Call Python matching service via HTTP
- Process results and update CRM
- Send notifications to sales team
- Handle errors and retries

**Key Nodes**:
1. **Schedule Trigger**: Cron-based execution
2. **HTTP Request**: Fetch CRM data
3. **Function**: Data transformation
4. **HTTP Request**: Call matching API
5. **Switch**: Route based on confidence
6. **HTTP Request**: Update CRM
7. **Email/Slack**: Notifications

---

### 3. **Python Matching Service (FastAPI)**

**Role**: Core business logic

**Endpoints**:

#### `POST /match-orders`
- **Input**: Companies, Deals, Orders (JSON)
- **Output**: Matched, Self-Service, Needs Review (JSON)
- **Process**: Multi-level matching algorithm

#### `GET /health`
- **Purpose**: Health check for monitoring

#### `GET /config`
- **Purpose**: View current matching configuration

**Matching Algorithm**:

```python
for each order:
    # Level 1: Temporal + Value Match
    if order.amount ≈ deal.amount (±10%)
       AND order.date within 90 days of deal.close_date:
        → MATCH with high confidence
    
    # Level 2: Temporal Only Match
    elif order.date within 90 days of most recent deal:
        → MATCH with medium confidence (flag for review)
    
    # Level 3: Self-Service Detection
    elif order.amount < €500
       OR no deals exist for company:
        → SELF-SERVICE (no sales rep)
    
    else:
        → FLAG FOR MANUAL REVIEW
```

**Confidence Scoring**:
```
Score = 100 points
  - Temporal penalty: -1 point per day distance
  - Value penalty: -10 points per 5% difference
  + Unique deal bonus: +30 points if only one deal in period
```

---

### 4. **Storage & Logging**

**Development**:
- JSON files for results
- Console logging

**Production** (recommended):
- PostgreSQL for audit trail
- Redis for caching
- Elasticsearch for log aggregation
- S3 for long-term storage

---

## Data Flow

```
1. TRIGGER
   ├─ Scheduled (cron)
   ├─ Manual (webhook)
   └─ Event-driven (new order created)

2. FETCH DATA
   ├─ Query CRM for Companies
   ├─ Query CRM for Won Deals
   └─ Query external DB for unmatched Orders

3. TRANSFORM
   ├─ Normalize data formats
   ├─ Filter relevant records
   └─ Prepare API payload

4. MATCH
   ├─ Call Python API: POST /match-orders
   ├─ Receive categorized results
   └─ Log matching metadata

5. PROCESS RESULTS
   ├─ High confidence → Auto-update CRM
   ├─ Low confidence → Send to review queue
   └─ Self-service → Mark as no attribution

6. UPDATE CRM
   ├─ Link Order to Deal
   ├─ Assign Sales Rep to Order
   └─ Trigger commission calculation

7. NOTIFY
   ├─ Email summary to sales team
   ├─ Slack notification for reviews
   └─ Dashboard update
```

---

## Scalability Considerations

### Current (MVP)
- Single Python instance
- Synchronous processing
- JSON file storage
- Manual n8n trigger

### Production Ready
- **Horizontal Scaling**: Multiple Python instances behind load balancer
- **Async Processing**: Celery + Redis for queue-based matching
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis for frequently accessed data
- **Monitoring**: Prometheus + Grafana
- **Error Handling**: Dead letter queue for failed matches
- **Rate Limiting**: Protect API from abuse

---

## Security

### API Security
- API key authentication
- Rate limiting
- Input validation (Pydantic)
- CORS configuration

### Data Security
- Encrypted connections (HTTPS)
- Sensitive data masking in logs
- Access control (RBAC)
- Audit trail for all attributions

---

## Monitoring & Observability

### Metrics
- **Match Rate**: % of orders successfully matched
- **Confidence Score**: Average confidence of matches
- **Processing Time**: API response time
- **Error Rate**: Failed matching attempts
- **Review Queue Size**: Orders awaiting manual review

### Alerts
- API health check failures
- High error rate (>5%)
- Low match rate (<80%)
- Review queue backlog (>50 orders)

---

## Future Enhancements

1. **Machine Learning**: Train model on historical matches to improve accuracy
2. **Real-time Processing**: WebSocket for instant attribution
3. **Multi-tenancy**: Support multiple organizations
4. **Advanced Analytics**: Dashboard with attribution insights
5. **A/B Testing**: Compare different matching strategies
6. **Product Matching**: Use product SKUs for better matching
7. **Contact Matching**: Match based on contact person involved

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | n8n | Workflow automation |
| **API** | FastAPI | REST API framework |
| **Logic** | Python 3.11+ | Core matching algorithm |
| **Data Processing** | pandas | Data manipulation |
| **Validation** | Pydantic | Data models & validation |
| **Logging** | Loguru | Structured logging |
| **Testing** | pytest | Unit & integration tests |
| **Containerization** | Docker | Deployment |
| **Storage (dev)** | JSON files | Simple storage |
| **Storage (prod)** | PostgreSQL | Relational database |

---

## Deployment Options

### Option 1: Local Development
```bash
# Python API
cd matching-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# n8n
docker-compose up -d
```

### Option 2: Cloud Deployment
- **API**: AWS Lambda / Google Cloud Run / Heroku
- **n8n**: n8n Cloud / Self-hosted on EC2
- **Database**: AWS RDS / Google Cloud SQL
- **Monitoring**: CloudWatch / Stackdriver

### Option 3: Kubernetes
- Deploy Python API as microservice
- n8n as separate service
- PostgreSQL as StatefulSet
- Ingress for routing
