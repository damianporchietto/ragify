# Qdrant Vector Store Setup Guide

This document explains how to set up and use Qdrant as the vector store for the Ragify RAG system.

## Overview

The system has been migrated from FAISS to Qdrant for improved scalability, persistence, and production readiness. Qdrant is a vector similarity search engine that provides:

- **REST API**: Easy integration and management
- **Persistence**: Data survives container restarts
- **Scalability**: Better performance for large datasets
- **Production Ready**: Built for enterprise use

## Configuration

### Vector Store Settings in config.yaml

```yaml
# Vector Store Configuration
vector_store:
  provider: "qdrant"  # qdrant or faiss
  qdrant_url: "http://localhost:6333"
  qdrant_collection_name: "my_collection"
  qdrant_distance_metric: "Cosine"  # Cosine, Euclidean, or Dot
```

### Environment Variables

You can override configuration via environment variables:

```bash
export QDRANT_URL="http://localhost:6333"
export QDRANT_COLLECTION_NAME="my_collection"
export QDRANT_DISTANCE_METRIC="Cosine"
```

## Quick Start

### 1. Start Qdrant Server

Using Docker Compose (recommended):

```bash
docker-compose up -d qdrant
```

Or using Docker directly:

```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Ingest Documents

```bash
python ingest.py
```

Or with custom options:

```bash
python ingest.py --collection my_custom_collection --provider openai --force-rebuild
```

### 4. Start the RAG API

```bash
python app.py
```

## Advanced Usage

### Force Rebuild Collection

To recreate the collection and re-ingest all documents:

```bash
python ingest.py --force-rebuild
```

### Custom Collection Name

```bash
python ingest.py --collection my_custom_collection
```

### Different Embedding Provider

```bash
python ingest.py --provider vertexai --model textembedding-gecko@latest
```

## Qdrant Management

### Check Collection Status

```bash
curl http://localhost:6333/collections/my_collection
```

### View Collection Info

```bash
curl http://localhost:6333/collections/my_collection/info
```

### Delete Collection

```bash
curl -X DELETE http://localhost:6333/collections/my_collection
```

## Persistence

- **Data Location**: `./qdrant_data/` (created automatically)
- **Backup**: Simply copy the `qdrant_data` directory
- **Restore**: Place backup in `qdrant_data` directory before starting Qdrant

## Distance Metrics

Choose the appropriate distance metric for your use case:

- **Cosine**: Best for normalized vectors (default for most embeddings)
- **Euclidean**: Good for absolute distance measurements
- **Dot**: Efficient for high-dimensional spaces

## Troubleshooting

### Connection Issues

1. Ensure Qdrant is running: `curl http://localhost:6333/health`
2. Check Docker logs: `docker-compose logs qdrant`
3. Verify port 6333 is not blocked

### Collection Not Found

1. Run ingestion: `python ingest.py`
2. Check collection exists: `curl http://localhost:6333/collections`

### Performance Issues

1. Increase Qdrant memory limits in docker-compose.yaml
2. Use appropriate distance metric for your embeddings
3. Consider adjusting chunk_size in config.yaml

## Migration from FAISS

The migration is complete and automatic. Key changes:

- **Storage**: From local files to Qdrant database
- **Persistence**: Automatic via Qdrant's built-in persistence
- **Scalability**: Better performance for large document collections
- **API**: Same LangChain interface, no code changes needed

## Production Deployment

For production use:

1. Use external Qdrant instance or cluster
2. Configure authentication if needed
3. Set up monitoring and backups
4. Use environment variables for configuration
5. Consider using Qdrant Cloud for managed service

## API Compatibility

The RAG API remains fully compatible. All existing endpoints work unchanged:

- `POST /ask` - Ask questions
- `GET /health` - Health check
- `GET /config` - View configuration

The vector store change is transparent to API users.