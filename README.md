# EzMetaServer

EzMetaServer is a comprehensive microservices-based platform for biological metadata processing, combining natural language processing (NLP) capabilities with metadata fetching from NCBI databases. This system provides a unified API gateway that manages two core services: a NLP service for entity recognition in biomedical text and a metadata fetch service that retrieves structured data from biological databases.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Services](#services)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [License](#license)

## Overview

EzMetaServer combines two powerful services into a unified platform:

1. **EzMetaFetch** - Retrieves metadata from NCBI databases (SRA, BioSample, etc.) using the NCBI EUtils API
2. **EzMetaNLP** - Processes biomedical text to identify named entities such as genes, diseases, species, cell lines, variants, and chemicals

These services are exposed through a REST API gateway, making it easy to integrate biological metadata processing into your research or application workflows.

## Architecture

The system follows a microservices architecture with three main components:

- **Dump Service**: Handles metadata retrieval from NCBI databases
- **NLP Service**: Processes text for entity recognition
- **Nginx Gateway**: Routes requests to appropriate services and provides unified API access

All components are containerized using Docker for ease of deployment and scalability.

## Services

### EzMetaDump (Port 8001)

The metadata fetching service provides functionality to:

- Search NCBI databases using terms
- Fetch detailed metadata for specific NCBI IDs
- Process and normalize the returned XML data into structured formats
- Extract and organize download links for SRA data files

The service is built with FastAPI and provides both synchronous and asynchronous endpoints for efficient processing of metadata requests.

### EzMetaNLP (Port 8000)

The NLP service uses advanced biomedical language models to:

- Identify named entities in text
- Categorize entities into predefined categories (Gene, Disease, Species, etc.)
- Process multiple text entries in batch mode

## Prerequisites

- Docker and Docker Compose
- At least 4GB of RAM for running the NLP models
- Internet connection for fetching metadata from NCBI

## Installation

1. Clone the repository:
   ```commandline
   git clone https://github.com/yourusername/ezmetaserver.git
   cd ezmetaserver
   ```

2. Download the [AIONER pretrained models](https://huggingface.co/lingbionlp/AIONER-0415/tree/main) and
   unpack `pretrained_models.zip`. Move the `pretrained_models` folder in `ezmetaserver/nlp/pretrained_models`.

3. Build and start the services:
   ```commandline
   docker-compose up -d
   ```

4. Verify that all services are running:
   ```commandline
   docker-compose ps
   ```

The API will be available at http://localhost:9090

## Configuration

### NLP Service Configuration

The NLP service configuration is located in `nlp/instance/config.yaml`:

```yaml
models:
  aioner:
    path: "/app/pretrained_models/AIONER/Bioformer-softmax-AIONER.h5"
    checkpoint: "/app/pretrained_models/bioformer-cased-v1.0"
    lowercase: false
    model_type: 1
```

### NCBI API Configuration

For higher rate limits when accessing NCBI databases, you can provide an API key through the API requests. Register for an NCBI API key at: https://www.ncbi.nlm.nih.gov/account/settings/

## Usage

### Fetching Metadata from NCBI

```bash
curl -X POST "http://localhost:9090/api/v1/dump/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "terms": ["SARS-CoV-2", "human"],
    "db": "sra",
    "max_results": 10
  }'
```

The dump service can be configured through API parameters, including:
- Database selection
- Rate limits
- Maximum results
- API key for higher rate limits

### Checking Record Availability

```bash
curl -X GET "http://localhost:9090/api/v1/dump/peek?term=SARS-CoV-2" \
  -H "Content-Type: application/json"
```

### Processing Text with NLP

```bash
curl -X POST "http://localhost:9090/api/v1/nlp/process" \
  -H "Content-Type: application/json" \
  -d '{
    "entries": [
      {
        "id": "sample1",
        "text": "PRMT5 deficiency enforces the transcriptional and epigenetic programs of Klrg1+CD8+ terminal effector T cells"
      }
    ],
    "model_type": "aioner"
  }'
```

## API Documentation

Interactive API documentation is available at:

- EzMetaDump API: http://localhost:9090/api/v1/dump/docs
- EzMetaNLP API: http://localhost:9090/api/v1/nlp/docs

### Key Endpoints

#### EzMetaDump Service

- `POST /api/v1/dump/fetch` - Fetch metadata from NCBI databases
- `GET /api/v1/dump/peek` - Check record availability in NCBI databases
- `GET /api/v1/dump/health` - Check the health status of the dump service

#### EzMetaNLP Service

- `POST /api/v1/nlp/process` - Process text to identify named entities
- `GET /api/v1/nlp/health` - Check the health status of the NLP service

#### Health Check

- `GET /health` - Check the health status of all services

### Gateway
Modify `nginx/nginx.conf` to adjust routing, rate limiting, or add additional services.

## Extended Use Cases

1. **Automated Metadata Enrichment**: Process research abstracts to identify key biological entities, then automatically fetch related metadata from NCBI.

2. **Dataset Building**: Construct curated datasets by searching for specific biological terms and collecting their associated metadata.

3. **Integration with Analysis Pipelines**: Use as a component in bioinformatics workflows to augment raw data with contextual information.

4. **Metadata Standardization**: Extract entities from free-text descriptions and connect them to standard database identifiers.

## Scaling

For production deployments:
- Consider using Kubernetes for orchestration
- Add a Redis cache to reduce API calls to NCBI
- Implement a dedicated database for storing processed results
- Deploy multiple instances of each service behind a load balancer

## License

This project is licensed under the MIT License - see the LICENSE file for details.

Parts of this project are based on [AIONER](https://github.com/ncbi/AIONER), which is licensed under its own terms.

## Acknowledgements

- NCBI E-utilities for providing the API to access biological databases
- Bioformer and AIONER for the pre-trained models used in entity recognition
