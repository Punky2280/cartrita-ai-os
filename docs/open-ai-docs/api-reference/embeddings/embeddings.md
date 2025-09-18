# Embeddings API

> **Source**: https://platform.openai.com/docs/api-reference/embeddings
> **Last Updated**: September 17, 2025

## Overview

Get a vector representation of a given input that can be easily consumed by machine learning models and algorithms. Embeddings are commonly used for:

- **Search** (where results are ranked by relevance to a query string)
- **Clustering** (where text strings are grouped by similarity)
- **Recommendations** (where items with related text strings are recommended)
- **Anomaly detection** (where outliers with little relatedness are identified)
- **Diversity measurement** (where similarity distributions are analyzed)
- **Classification** (where text strings are classified by their most similar label)

## Create Embeddings

Creates an embedding vector representing the input text.

### HTTP Request
```
POST https://api.openai.com/v1/embeddings
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input` | string or array | Yes | Input text to embed, encoded as a string or array of tokens. To embed multiple inputs in a single request, pass an array of strings or array of token arrays. |
| `model` | string | Yes | ID of the model to use. You can use the List models API to see all of your available models. |
| `encoding_format` | string | No | The format to return the embeddings in. Can be either `float` or `base64`. Defaults to `float`. |
| `dimensions` | integer | No | The number of dimensions the resulting output embeddings should have. Only supported in `text-embedding-3-small` and `text-embedding-3-large` models. |
| `user` | string | No | A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse. |

### Example Request

#### Basic Embedding
```python
from openai import OpenAI

client = OpenAI()

response = client.embeddings.create(
    input="The food was delicious and the waiter...",
    model="text-embedding-3-small"
)

print(response.data[0].embedding)
```

#### Multiple Inputs
```python
from openai import OpenAI

client = OpenAI()

response = client.embeddings.create(
    input=[
        "The food was delicious and the waiter...",
        "I love this restaurant",
        "The service was terrible"
    ],
    model="text-embedding-3-small"
)

for i, embedding in enumerate(response.data):
    print(f"Embedding {i}: {embedding.embedding[:5]}...")  # First 5 dimensions
```

#### Custom Dimensions
```python
from openai import OpenAI

client = OpenAI()

# Reduce dimensions for smaller storage/faster computation
response = client.embeddings.create(
    input="Sample text for embedding",
    model="text-embedding-3-small",
    dimensions=512  # Reduced from default 1536
)

print(f"Embedding dimensions: {len(response.data[0].embedding)}")
```

#### Using cURL
```bash
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The food was delicious and the waiter...",
    "model": "text-embedding-3-small"
  }'
```

### Response Object

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [
        0.0023064255,
        -0.009327292,
        -0.0028842222,
        // ... (1536 dimensions for text-embedding-3-small)
      ],
      "index": 0
    }
  ],
  "model": "text-embedding-3-small",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | The object type, which is always "list". |
| `data` | array | A list of embedding objects. |
| `model` | string | The name of the model used to generate the embedding. |
| `usage` | object | The usage information for the request. |

### Embedding Object

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | The object type, which is always "embedding". |
| `embedding` | array | The embedding vector, which is a list of floats. |
| `index` | integer | The index of the embedding in the list of embeddings. |

## Available Models

### Current Models

| Model | Description | Dimensions | Max Input Tokens | Price per 1M tokens |
|-------|-------------|------------|------------------|---------------------|
| `text-embedding-3-large` | Most capable embedding model | 3072 | 8191 | $0.13 |
| `text-embedding-3-small` | Improved performance over ada v2 | 1536 | 8191 | $0.02 |
| `text-embedding-ada-002` | Legacy model (not recommended) | 1536 | 8191 | $0.10 |

### Model Comparison

**text-embedding-3-large**
- Highest performance and capability
- Largest vector dimensions (3072)
- Best for applications requiring maximum accuracy
- Higher cost but superior quality

**text-embedding-3-small**
- Great performance-to-cost ratio
- Standard dimensions (1536)
- Recommended for most applications
- 5x cheaper than text-embedding-3-large

**text-embedding-ada-002**
- Legacy model, use new models instead
- Being phased out
- Similar performance to text-embedding-3-small but more expensive

## Common Use Cases

### Semantic Search

```python
import numpy as np
from openai import OpenAI

client = OpenAI()

def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Example documents
documents = [
    "The cat sat on the mat",
    "Python is a programming language",
    "Machine learning is fascinating",
    "I love cats and dogs"
]

# Get embeddings for all documents
doc_embeddings = [get_embedding(doc) for doc in documents]

# Search query
query = "pets and animals"
query_embedding = get_embedding(query)

# Calculate similarities
similarities = [cosine_similarity(query_embedding, doc_emb) for doc_emb in doc_embeddings]

# Rank results
results = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)

print("Search results:")
for doc, score in results:
    print(f"Score: {score:.3f} - {doc}")
```

### Text Classification

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

client = OpenAI()

# Define categories with example texts
categories = {
    "technology": "Artificial intelligence and machine learning advances",
    "sports": "Football basketball tennis soccer games",
    "cooking": "Recipes ingredients cooking baking food preparation",
    "travel": "Vacation destinations hotels flights tourism"
}

# Get embeddings for categories
category_embeddings = {}
for category, text in categories.items():
    embedding = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    ).data[0].embedding
    category_embeddings[category] = embedding

def classify_text(text):
    # Get embedding for input text
    text_embedding = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    ).data[0].embedding

    # Calculate similarity to each category
    similarities = {}
    for category, cat_embedding in category_embeddings.items():
        similarity = cosine_similarity([text_embedding], [cat_embedding])[0][0]
        similarities[category] = similarity

    # Return the most similar category
    return max(similarities, key=similarities.get), similarities

# Example classification
text = "I'm planning a trip to Japan next summer"
category, scores = classify_text(text)

print(f"Text: {text}")
print(f"Predicted category: {category}")
print("All scores:")
for cat, score in scores.items():
    print(f"  {cat}: {score:.3f}")
```

### Recommendation System

```python
import numpy as np
from openai import OpenAI

client = OpenAI()

class RecommendationSystem:
    def __init__(self):
        self.items = {}
        self.embeddings = {}

    def add_item(self, item_id, description):
        """Add an item to the recommendation system"""
        self.items[item_id] = description
        embedding = client.embeddings.create(
            input=description,
            model="text-embedding-3-small"
        ).data[0].embedding
        self.embeddings[item_id] = np.array(embedding)

    def get_recommendations(self, query, top_k=5):
        """Get top-k recommendations based on query"""
        query_embedding = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        ).data[0].embedding
        query_embedding = np.array(query_embedding)

        # Calculate similarities
        similarities = {}
        for item_id, item_embedding in self.embeddings.items():
            similarity = np.dot(query_embedding, item_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(item_embedding)
            )
            similarities[item_id] = similarity

        # Sort and return top-k
        sorted_items = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:top_k]

# Example usage
rec_system = RecommendationSystem()

# Add some products
rec_system.add_item("laptop1", "High-performance gaming laptop with RTX 4090")
rec_system.add_item("phone1", "Latest smartphone with excellent camera")
rec_system.add_item("tablet1", "Lightweight tablet perfect for reading and drawing")
rec_system.add_item("watch1", "Smartwatch with health monitoring features")

# Get recommendations
query = "I need something for creative work and design"
recommendations = rec_system.get_recommendations(query, top_k=3)

print(f"Query: {query}")
print("Recommendations:")
for item_id, score in recommendations:
    print(f"  {item_id}: {rec_system.items[item_id]} (Score: {score:.3f})")
```

### Clustering Documents

```python
import numpy as np
from sklearn.cluster import KMeans
from openai import OpenAI

client = OpenAI()

def cluster_texts(texts, n_clusters=3):
    """Cluster texts using K-means on their embeddings"""

    # Get embeddings for all texts
    embeddings = []
    for text in texts:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embeddings.append(response.data[0].embedding)

    # Perform clustering
    embeddings_array = np.array(embeddings)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(embeddings_array)

    # Group texts by cluster
    clusters = {}
    for i, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(texts[i])

    return clusters

# Example texts
texts = [
    "Python programming tutorial",
    "Machine learning algorithms",
    "Cooking pasta recipes",
    "JavaScript web development",
    "Baking bread at home",
    "Deep learning neural networks",
    "Italian cuisine guide",
    "React.js components",
    "Data science projects",
    "French cooking techniques"
]

# Cluster the texts
clusters = cluster_texts(texts, n_clusters=3)

print("Document clusters:")
for cluster_id, cluster_texts in clusters.items():
    print(f"\nCluster {cluster_id}:")
    for text in cluster_texts:
        print(f"  - {text}")
```

## Optimization and Best Practices

### Reducing Costs

#### Use Smaller Dimensions
```python
# For text-embedding-3-small and text-embedding-3-large only
response = client.embeddings.create(
    input="Your text here",
    model="text-embedding-3-small",
    dimensions=512  # Reduced from default 1536
)
```

#### Batch Processing
```python
# Process multiple texts in one request
texts = ["Text 1", "Text 2", "Text 3", "Text 4"]

response = client.embeddings.create(
    input=texts,
    model="text-embedding-3-small"
)

# Extract embeddings
embeddings = [data.embedding for data in response.data]
```

#### Caching Embeddings
```python
import pickle
import hashlib

class EmbeddingCache:
    def __init__(self, cache_file="embeddings_cache.pkl"):
        self.cache_file = cache_file
        try:
            with open(cache_file, 'rb') as f:
                self.cache = pickle.load(f)
        except FileNotFoundError:
            self.cache = {}

    def get_embedding(self, text, model="text-embedding-3-small"):
        # Create cache key
        key = hashlib.md5(f"{text}:{model}".encode()).hexdigest()

        if key in self.cache:
            return self.cache[key]

        # Get embedding from API
        response = client.embeddings.create(input=text, model=model)
        embedding = response.data[0].embedding

        # Cache the result
        self.cache[key] = embedding
        self.save_cache()

        return embedding

    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

# Usage
cache = EmbeddingCache()
embedding = cache.get_embedding("Sample text")
```

### Performance Tips

#### Preprocessing Text
```python
import re

def preprocess_text(text):
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters if needed
    text = re.sub(r'[^\w\s]', '', text)
    # Convert to lowercase
    text = text.lower().strip()
    return text

def get_embedding_with_preprocessing(text, model="text-embedding-3-small"):
    processed_text = preprocess_text(text)
    response = client.embeddings.create(input=processed_text, model=model)
    return response.data[0].embedding
```

#### Handling Long Texts
```python
def chunk_text(text, max_tokens=8000):
    """Split text into chunks that fit within token limits"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        # Rough token estimation (1 token ≈ 4 characters)
        word_tokens = len(word) // 4 + 1

        if current_length + word_tokens > max_tokens:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_tokens
        else:
            current_chunk.append(word)
            current_length += word_tokens

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def get_embedding_for_long_text(text, model="text-embedding-3-small"):
    """Get embeddings for long text by chunking and averaging"""
    chunks = chunk_text(text)

    if len(chunks) == 1:
        response = client.embeddings.create(input=chunks[0], model=model)
        return response.data[0].embedding

    # Get embeddings for all chunks
    chunk_embeddings = []
    for chunk in chunks:
        response = client.embeddings.create(input=chunk, model=model)
        chunk_embeddings.append(response.data[0].embedding)

    # Average the embeddings
    averaged_embedding = np.mean(chunk_embeddings, axis=0)
    return averaged_embedding.tolist()
```

## Error Handling

### Common Errors

#### Token Limit Exceeded
```json
{
  "error": {
    "message": "This model's maximum context length is 8191 tokens, however you requested 8192 tokens.",
    "type": "invalid_request_error",
    "param": null,
    "code": null
  }
}
```

#### Invalid Model
```json
{
  "error": {
    "message": "The model `invalid-model` does not exist",
    "type": "invalid_request_error",
    "param": null,
    "code": "model_not_found"
  }
}
```

### Python Error Handling
```python
import openai

def safe_get_embedding(text, model="text-embedding-3-small", max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding

        except openai.RateLimitError as e:
            print(f"Rate limit exceeded, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

        except openai.APIError as e:
            print(f"API error: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise

        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    return None
```

## Integration Examples

### Vector Database Integration

#### Pinecone
```python
import pinecone
from openai import OpenAI

# Initialize Pinecone
pinecone.init(api_key="your-pinecone-api-key", environment="your-env")

# Create or connect to index
index_name = "embeddings-index"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=1536, metric="cosine")

index = pinecone.Index(index_name)

# OpenAI client
client = OpenAI()

def store_embedding(doc_id, text, metadata=None):
    """Store document embedding in Pinecone"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding

    index.upsert(vectors=[(doc_id, embedding, metadata or {})])

def search_similar(query, top_k=5):
    """Search for similar documents"""
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding

    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return results
```

#### Chroma
```python
import chromadb
from openai import OpenAI

# Initialize Chroma
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="documents")

client = OpenAI()

def add_documents(documents, ids):
    """Add documents to Chroma collection"""
    # Get embeddings
    response = client.embeddings.create(
        input=documents,
        model="text-embedding-3-small"
    )
    embeddings = [data.embedding for data in response.data]

    # Add to collection
    collection.add(
        embeddings=embeddings,
        documents=documents,
        ids=ids
    )

def search_documents(query, n_results=5):
    """Search documents in Chroma"""
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results
```

---

*This documentation covers the Embeddings API and common use cases. Embeddings are powerful tools for semantic understanding and can significantly enhance search and recommendation systems.*
