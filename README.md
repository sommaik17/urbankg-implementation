# UrbanKG Implementation
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the complete implementation code for the UrbanKG framework.

## Overview

UrbanKG is a knowledge graph framework for semantic integration of heterogeneous urban data across five domains:
- 🚌 **Mobility** - Transit systems, traffic, vehicles
- ⚡ **Energy** - Power grids, smart meters, demand
- 🌳 **Environment** - Air quality, sensors, monitoring
- 🚑 **Public Safety** - Emergency services, incidents, hospitals
- 🏛️ **Civic Services** - Government offices, public facilities

### Key Features

✅ **Semantic Interoperability** - Federated cross-domain SPARQL queries  
✅ **Ontology-First Construction** - Aligned with W3C/OGC standards (SSN/SOSA, SAREF, GeoSPARQL)  
✅ **Temporal Awareness** - Named graph timestamping for dynamic data  
✅ **Federated Governance** - Independent domain partition management  
✅ **Hybrid Reasoning** - OWL-RL deductive + GNN inductive inference

## Repository Structure

```
urbankg-implementation/
├── ontology/
│   └── urbankg-core.ttl          # Complete ontology (Appendix A)
├── queries/
│   ├── query-cascade-impact.sparql          # B.1: Multi-domain impact
│   ├── query-transit-environment.sparql     # B.2: Transit-environment
│   ├── query-emergency-resource.sparql      # B.3: Emergency optimization
│   ├── query-digital-twin-staleness.sparql  # B.4: Digital twin sync
│   └── query-federated-example.sparql       # B.5: Federated governance
├── data/
│   └── sample-instances.ttl      # Sample RDF instances
├── src/
│   ├── accessibility_analysis.py # Service accessibility metrics (Section 6.4)
│   ├── data_ingestion.py         # RDF mapping pipeline
│   └── query_executor.py         # SPARQL query utilities
├── docs/
│   ├── ONTOLOGY.md              # Ontology documentation
│   ├── QUERIES.md               # Query pattern documentation
│   └── DEPLOYMENT.md            # Deployment guide
├── docker/
│   ├── docker-compose.yml       # Fuseki + data stack
│   └── Dockerfile
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for triple store)
- Java 11+ (for Apache Jena Fuseki)

### 1. Clone Repository

```bash
git clone https://github.com/sommaik17/urbankg-implementation.git
cd urbankg-implementation
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Triple Store

```bash
cd docker
docker-compose up -d
```

This starts Apache Jena Fuseki at `http://localhost:3030`

### 4. Load Ontology and Data

```bash
# Load core ontology
curl -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/urbankg-core.ttl \
  http://localhost:3030/urbankg/data

# Load sample instances
curl -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @data/sample-instances.ttl \
  http://localhost:3030/urbankg/data
```

### 5. Run Example Queries

```bash
# Execute cascade impact analysis (Query B.1)
python src/query_executor.py queries/query-cascade-impact.sparql

# Run accessibility analysis (Section 6.4)
python src/accessibility_analysis.py
```

## Paper Implementation Correspondence

This implementation directly corresponds to the paper sections:

| Paper Section | Implementation Files |
|--------------|---------------------|
| **Appendix A** - Ontology | `ontology/urbankg-core.ttl` |
| **Appendix B.1** - Cascade Impact | `queries/query-cascade-impact.sparql` |
| **Appendix B.2** - Transit-Environment | `queries/query-transit-environment.sparql` |
| **Appendix B.3** - Emergency Resource | `queries/query-emergency-resource.sparql` |
| **Appendix B.4** - Digital Twin Staleness | `queries/query-digital-twin-staleness.sparql` |
| **Appendix B.5** - Federated Query | `queries/query-federated-example.sparql` |
| **Section 6.4** - Accessibility Analysis | `src/accessibility_analysis.py` |
| **Section 5.5** - Data Ingestion | `src/data_ingestion.py` |

## Design Objectives Validation

The implementation validates all five design objectives (DO1-DO5):

### DO1: Semantic Interoperability ✅
```sparql
# Cross-domain query spanning Mobility + Energy + Environment
SELECT ?incident ?substation ?sensor
WHERE {
  ?incident a urb:Incident ;
            urb:severityLevel ?severity .
  ?substation a urb:PowerSubstation .
  ?sensor a urb:AirQualityStation .
  # Spatial joins via GeoSPARQL
}
```

### DO2: Ontology-First Construction ✅
- Core ontology aligned with 8 W3C/OGC standards
- T-Box defined before A-Box population
- SHACL constraints for validation

### DO3: Temporal Awareness ✅
```turtle
# Named graph with timestamp
GRAPH <http://urbankg.org/observations/2024-05-08T09:00:00Z> {
  urb:Obs_PM25 sosa:resultTime "2024-05-08T09:00:00Z"^^xsd:dateTime .
}
```

### DO4: Federated Governance ✅
```sparql
# Query across independent partitions
SERVICE <http://urbankg.org/sparql/mobility> { ... }
SERVICE <http://urbankg.org/sparql/energy> { ... }
```

### DO5: Hybrid Reasoning ✅
- OWL-RL inference via Apache Jena
- Property chain axioms for emergency response
- GNN embeddings (see `src/graph_embeddings.py`)

## Data Sources

The proof-of-concept uses publicly available datasets:

| Domain | Source | Description |
|--------|--------|-------------|
| Mobility | Bangkok GTFS | Transit schedules, stops, routes |
| Energy | UCI ML Repo | Household power consumption |
| Environment | Thailand PCD | Air quality (PM2.5, NO2, CO) |
| Safety | Thailand Road Safety | Geocoded accident records |
| Civic | Traffy Fondue | Citizen service requests |

See `docs/DATA_SOURCES.md` for complete details.

## Accessibility Analysis

The Service Accessibility Analysis (Section 6.4) implements:

### Metrics

1. **Transit-Based Accessibility (TBA)**
   ```
   TBA(d,t) = Area(R_{d,t}) / Area(d)
   ```

2. **Service Coverage Index (SCI)**
   ```
   SCI(d,s) = |{p ∈ S_s : distance(d,p) ≤ θ}| / Population(d)
   ```

3. **Multi-Modal Accessibility Score (MMAS)**
   ```
   MMAS = 0.30×Hospital + 0.30×Emergency + 0.20×Govt 
          + 0.15×Facility + 0.05×Environment
   ```

### Example Usage

```python
from src.accessibility_analysis import AccessibilityAnalyzer

analyzer = AccessibilityAnalyzer("http://localhost:3030/urbankg/sparql")

metrics = analyzer.analyze_district(
    district_uri="http://urbankg.org/ontology#District_Central",
    district_name="District 1",
    population=150000,
    area_km2=25.0
)

print(f"MMAS Score: {metrics.mmas_score}")  # Output: 8.2
```

## Query Examples

### Cross-Domain Cascade Impact (Query B.1)

Finds all infrastructure affected by a traffic incident:

```sparql
PREFIX urb: <http://urbankg.org/ontology#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>

SELECT ?incident ?affectedType ?affectedEntity ?distance
WHERE {
  ?incident a urb:Incident ;
            urb:severityLevel ?severity .
  FILTER(?severity >= 4)
  
  {?affectedEntity a urb:PowerSubstation}
  UNION {?affectedEntity a urb:AirQualityStation}
  UNION {?affectedEntity a urb:TransitStop}
  
  FILTER(geof:distance(?incidentGeom, ?affectedGeom) <= 500)
}
```

See `queries/` directory for all 5 complete queries from Appendix B.

## Performance Metrics

### Query Response Times

| Query | Triple Count | Response Time | Domains |
|-------|-------------|---------------|---------|
| B.1 Cascade Impact | 287,000 | 124ms | 3 |
| B.2 Transit-Environment | 287,000 | 89ms | 2 |
| B.3 Emergency Resource | 287,000 | 156ms | 2 |
| B.4 Digital Twin Staleness | 287,000 | 203ms | 5 |
| B.5 Federated | 287,000 | 178ms | 2 |

*Hardware: 16GB RAM, Intel i7-10700K, Apache Jena Fuseki 4.7.0*

### Graph Statistics

- **Total Triples**: 287,000
- **Ontology Classes**: 25
- **Object Properties**: 15
- **Data Properties**: 12
- **Instances**: 5,420 (transit stops, sensors, facilities)

## Ontology Standards

UrbanKG aligns with the following W3C/OGC standards:

- **SSN/SOSA** - Sensor network observations
- **SAREF** - Smart appliances (energy devices)
- **GeoSPARQL** - Spatial queries and geometry
- **PROV-O** - Provenance and lineage
- **OWL-Time** - Temporal concepts
- **QUDT** - Units of measurement
- **GTFS** - General Transit Feed Specification

## Testing

```bash
# Run unit tests
pytest tests/

# Run SPARQL query validation
python tests/validate_queries.py

# Run ontology consistency checks
robot verify --input ontology/urbankg-core.ttl
```

## Docker Deployment

```bash
# Build and start full stack
docker-compose up --build

# Services available at:
# - Fuseki: http://localhost:3030
# - Query UI: http://localhost:8080
```

## Citation

If you use this implementation, please cite our paper:

```bibtex
@article{khantong2026urbankg,
  title={Knowledge Graphs for Integrated Urban Data Management in Smart Cities: 
         A Framework for Semantic Interoperability Across Urban Domains},
  author={Khantong, Sommai and Savithi, Charuay and Ahmad, Mohammad Nazir},
  journal={Urban Science},
  year={2026},
  publisher={MDPI}
}
```

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

Areas for contribution:
- Additional domain ontologies (health, water, waste)
- Real-time data ingestion pipelines
- Graph embedding models (TransE, RotatE, GraphSAGE)
- Visualization dashboards
- Performance benchmarks

## Documentation

- **[Ontology Reference](docs/ONTOLOGY.md)** - Complete class/property documentation
- **[Query Patterns](docs/QUERIES.md)** - SPARQL patterns and examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment
- **[Data Sources](docs/DATA_SOURCES.md)** - Dataset documentation
- **[API Reference](docs/API.md)** - Python API documentation

## Support

- 📧 Email: sommai.k@acc.msu.ac.th
- 🐛 Issues: [GitHub Issues](https://github.com/sommaik17/urbankg-implementation/issues)
- 📖 Paper: [Urban Science Journal](https://www.mdpi.com/journal/urbansci)

## Acknowledgments

- Mahasarakham Business School for funding
- W3C/OGC for ontology standards
- Bangkok Metropolitan Administration for data access
- Apache Jena project for triple store infrastructure

## Roadmap

### Phase 1 (Current) ✅
- [x] Core ontology implementation
- [x] Five domain sub-graphs
- [x] Cross-domain SPARQL queries
- [x] Accessibility analysis metrics

### Phase 2 (In Progress) 🚧
- [ ] Real-time IoT data ingestion
- [ ] Graph embedding training pipeline
- [ ] Web-based query interface
- [ ] Benchmark dataset creation

### Phase 3 (Planned) 📋
- [ ] Mobile app integration
- [ ] Privacy-preserving SPARQL
- [ ] Multi-city deployment
- [ ] Transfer learning framework

---

**Last Updated:** May 2026  
**Version:** 1.0.0  
**Status:** Active Development
