# Embedding and Vector Store Database Architecture

## High-Level Overview

```mermaid
graph LR
    subgraph "Data Ingestion"
        ID[Item Data<br/>name, examine, members]
        TP[Text Processing<br/>Format searchable text]
        EG[Embedding Generation<br/>SentenceTransformer<br/>384-dim vectors]
        VS[Vector Storage<br/>PostgreSQL + pgvector]
        
        ID --> TP
        TP --> EG
        EG --> VS
    end
    
    subgraph "Search Flow"
        UQ[User Query]
        QE[Query Embedding<br/>384-dim vector]
        VS2[Vector Similarity Search<br/>Cosine distance]
        RES[Search Results<br/>Ranked by similarity]
        
        UQ --> QE
        QE --> VS2
        VS -->|compare| VS2
        VS2 --> RES
    end
    
    style EG fill:#e1f5ff,color:#000000
    style VS fill:#fff4e1,color:#000000
    style VS2 fill:#f3e5f5,color:#000000
    style QE fill:#f3e5f5,color:#000000
```

## Detailed Architecture

```mermaid
graph TB
    subgraph "Embedding Service Layer"
        ES[EmbeddingService]
        ST[SentenceTransformer Model<br/>all-MiniLM-L6-v2<br/>384 dimensions]
        ES -->|loads| ST
        
        ET[embed_text<br/>Single text → Vector]
        ETS[embed_texts<br/>Batch texts → Vectors]
        ES --> ET
        ES --> ETS
        ST -->|encodes| ET
        ST -->|encodes batch| ETS
    end
    
    subgraph "Text Processing"
        ID[Item Data<br/>name, examine, members]
        CST[create_searchable_text<br/>Format: Item Name + Description]
        FQ[format_query_for_embedding<br/>Format user queries]
        
        ID --> CST
        CST -->|generates| STXT[Searchable Text String]
        UQ[User Query] --> FQ
        FQ -->|generates| FQT[Formatted Query Text]
    end
    
    subgraph "Embedding Generation Flow"
        STXT -->|input| ET
        FQT -->|input| ET
        STXT -->|batch input| ETS
        ET -->|output| EV[Embedding Vector<br/>List of 384 floats]
        ETS -->|output| EVB[Batch Embedding Vectors]
    end
    
    subgraph "PostgreSQL Database with pgvector"
        PG[(PostgreSQL Database)]
        PGV[pgvector Extension<br/>Vector similarity operations]
        PG -->|enables| PGV
        
        subgraph "Item Table (game_items)"
            IT[Item Model]
            ITF1[item_id: Integer PK]
            ITF2[name: String]
            ITF3[examine: Text]
            ITF4[members: Boolean]
            ITF5[embedding: Vector 384]
            ITF6[Other fields:<br/>lowalch, highalch, limit, value, icon]
            
            IT --> ITF1
            IT --> ITF2
            IT --> ITF3
            IT --> ITF4
            IT --> ITF5
            IT --> ITF6
        end
        
        subgraph "Price History Table"
            PH[PriceHistory Model]
            PHF1[id: Integer PK]
            PHF2[item_id: Foreign Key]
            PHF3[timestamp: TIMESTAMP]
            PHF4[high_price: BigInteger]
            PHF5[low_price: BigInteger]
            
            PH --> PHF1
            PH --> PHF2
            PH --> PHF3
            PH --> PHF4
            PH --> PHF5
        end
        
        ITF1 -.->|1:N| PHF2
    end
    
    EV -->|stores| ITF5
    EVB -->|batch stores| ITF5
    ID -->|creates/updates| IT
    
    subgraph "Vector Search Process"
        SQ[Search Query]
        SQ --> FQ
        FQT --> ET
        ET -->|generates| QEV[Query Embedding Vector]
        
        VS[Vector Similarity Search<br/>ORDER BY embedding cosine distance query_vector]
        QEV -->|input| VS
        ITF5 -->|compared with| VS
        PGV -->|provides cosine distance operator| VS
        
        VS -->|returns| SR[Search Results<br/>with similarity scores]
        
        KW[Keyword Matching<br/>Name/description boost]
        SQ -->|also used for| KW
        SR -->|combined with| KW
        KW -->|final| FR[Final Ranked Results]
    end
    
    subgraph "Polling Service Integration"
        PS[Polling Service]
        API[OSRS Wiki API]
        API -->|fetches| PS
        PS -->|processes| ID
        PS -->|batch generates| ETS
        PS -->|stores| IT
    end
    
    style ES fill:#e1f5ff,color:#000000
    style ST fill:#e1f5ff,color:#000000
    style PG fill:#fff4e1,color:#000000
    style PGV fill:#fff4e1,color:#000000
    style IT fill:#e8f5e9,color:#000000
    style ITF5 fill:#ffebee,color:#000000
    style VS fill:#f3e5f5,color:#000000
    style QEV fill:#f3e5f5,color:#000000
```

## Key Components

### 1. Embedding Service
- **EmbeddingService**: Singleton service managing embedding generation
- **SentenceTransformer Model**: Uses `all-MiniLM-L6-v2` (384 dimensions) by default
- **Methods**: 
  - `embed_text()`: Single text → vector
  - `embed_texts()`: Batch processing for efficiency

### 2. Text Processing
- **create_searchable_text()**: Formats item data as "Item Name: X | Description: Y"
- **format_query_for_embedding()**: Formats user queries to match item embedding structure

### 3. Database Schema
- **Item Table**: Stores items with vector embeddings in `embedding` column (Vector(384))
- **pgvector Extension**: Enables vector similarity operations (<=> operator)
- **PriceHistory Table**: Tracks price changes over time (separate from embeddings)

### 4. Vector Search
- Uses PostgreSQL's `<=>` operator for cosine distance
- Hybrid search: Combines vector similarity (70%) with keyword matching (30%)
- Returns results ordered by combined similarity score

### 5. Data Flow
1. Item data → Searchable text → Embedding vector → Stored in database
2. User query → Formatted query → Query embedding → Vector similarity search → Results

