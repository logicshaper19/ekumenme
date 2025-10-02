1# Ekumen Conversation Architecture

## Overview
Ekumen follows the **ChatGPT conversation pattern** for simplicity and familiarity.

**Key Principle:** Leverage existing LangChain infrastructure - no new frameworks or tools needed.

---

## 1. Conversation Lifecycle

### Creating Conversations
- **Trigger 1**: User clicks "New Chat" button
- **Trigger 2**: User sends first message (auto-creates conversation)
- **Auto-title**: Generate title from first 1-2 messages (e.g., "Wheat fungicide recommendations")

### Conversation States
- **ACTIVE**: Default state, conversation is ongoing
- **ARCHIVED**: User manually archives (optional feature)
- **DELETED**: User deletes conversation (soft delete)

### Soft Delete Implementation

**When user deletes a conversation:**
```python
async def soft_delete_conversation(conversation_id: str, db: AsyncSession):
    """Soft delete conversation - keeps data for audit trail"""

    # Update conversation status
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(
            status='deleted',
            deleted_at=datetime.now()
        )
    )
    await db.commit()

    # Messages are NOT deleted - kept for audit trail
    # Messages remain in database but conversation is hidden from user

    # Schedule permanent deletion after 30 days (optional)
    # await schedule_permanent_deletion(conversation_id, days=30)
```

**What happens to messages:**
- ✅ Messages remain in database (for audit trail)
- ✅ Conversation hidden from user's conversation list
- ✅ Messages not accessible through UI
- ✅ Can be restored by changing status back to 'active'
- ✅ Optional: Hard delete after 30 days (GDPR compliance)

**Permanent deletion (optional):**
```python
async def permanently_delete_conversation(conversation_id: str, db: AsyncSession):
    """Hard delete conversation and all messages (GDPR right to be forgotten)"""

    # Delete messages first (foreign key constraint)
    await db.execute(
        delete(Message).where(Message.conversation_id == conversation_id)
    )

    # Delete conversation
    await db.execute(
        delete(Conversation).where(Conversation.id == conversation_id)
    )

    await db.commit()
```

### No Explicit "End"
- Conversations never "end" automatically
- Users can return to any conversation and continue
- Context is maintained per conversation

---

## 2. LangChain Integration (Existing Infrastructure)

### ✅ Already Implemented: RunnableWithMessageHistory

```python
# From lcel_chat_service.py - ALREADY WORKING
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: get_session_history(session_id, db_session),
    input_messages_key="input",
    history_messages_key="chat_history",
)
```

**This automatically:**
- ✅ Loads conversation history from `messages` table
- ✅ Adds new messages to context
- ✅ Saves messages back to database
- ✅ Handles entire ChatGPT-style conversation flow

**No changes needed!** Current `conversations` and `messages` tables work perfectly.

---

## 3. Message Threading

### Pattern: Linear History (Like ChatGPT)
```
Conversation:
  Message 1: User: "What fungicide for wheat?"
  Message 2: Agent: "I recommend..."
  Message 3: User: "Tell me more about product X"
  Message 4: Agent: "Product X is..."
```

### NO Sub-Threading
- No parent_message_id threading within a conversation
- "New Chat" button creates a NEW conversation (not a thread)
- Keep it simple: linear message flow

---

## 3. Context Management

### Context Window Strategy (ChatGPT Approach)
1. **Load entire conversation history** into context
2. **Token limit**: ~8K-32K tokens (model dependent)
3. **When limit reached**: Truncate oldest messages (FIFO)
4. **No summarization** (keep it simple for now)

### What to Store in Context
```python
context = {
    "conversation_id": "uuid",
    "farm_siret": "12345678901234",  # Farm context
    "user_role": "farmer",
    "organization_id": "uuid",
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "...", "tool_calls": [...]},
    ]
}
```

### Tool Calls Storage
- ✅ **Store tool calls WITH messages** in `message_metadata`
- ✅ **Store tool results** in `message_metadata`
- ✅ **Display in UI** (like ChatGPT shows "Used tools: X, Y, Z")

Example:
```json
{
  "message_id": "uuid",
  "content": "Based on your wheat parcel...",
  "message_metadata": {
    "tool_calls": [
      {
        "tool": "get_parcel_info",
        "arguments": {"parcel_id": "uuid"},
        "result": {"name": "Tuferes", "surface_ha": 228.54}
      },
      {
        "tool": "search_ephy_products",
        "arguments": {"crop": "wheat", "pest": "fusarium"},
        "result": [{"name": "OPUS", "amm": "123456"}]
      }
    ],
    "processing_time_ms": 1250,
    "token_count": 450
  }
}
```

---

## 4. Multi-Organization Context

### Pattern: ONE Organization Per Session (Like ChatGPT Teams)

**Decision:** NO organization selector dropdown during session.

**Why?** ChatGPT doesn't let you switch workspaces mid-session. You log in to ONE workspace and stay there.

### How It Works

#### Scenario 1: User Belongs to ONE Organization (Most Common)
```
User logs in → Automatically in their organization context
No selection needed!
All conversations scoped to that organization
```

#### Scenario 2: User Belongs to MULTIPLE Organizations (Rare)
```
User logs in → Sees "Select Organization" screen ONCE
User selects organization → Gets token with org_id embedded
Stays in that organization for entire session
To switch → Log out and log back in (or use different browser tab)
```

### Implementation

```python
# At login, if user has multiple orgs:
POST /api/v1/auth/login
{
    "email": "farmer@example.com",
    "password": "..."
}

Response:
{
    "access_token": "...",
    "user": {...},
    "organizations": [
        {"id": "uuid1", "name": "Ferme Dupont", "type": "farm"},
        {"id": "uuid2", "name": "Coopérative ABC", "type": "cooperative"}
    ],
    "requires_org_selection": true  # If multiple orgs
}

# User selects organization:
POST /api/v1/auth/select-organization
{
    "organization_id": "uuid1"
}

Response:
{
    "access_token": "...",  # New token with org_id embedded
    "organization": {"id": "uuid1", "name": "Ferme Dupont"}
}

# All subsequent requests use this org context
# JWT token contains: user_id + organization_id
# No switching during session!
```

### Database Queries
```sql
-- Get conversations for user in their current organization
SELECT * FROM conversations
WHERE user_id = :user_id
AND organization_id = :org_id  -- From JWT token
ORDER BY last_message_at DESC;

-- Get messages for a conversation
SELECT * FROM messages
WHERE conversation_id = :conversation_id
ORDER BY created_at ASC;
```

### Data Isolation
- ✅ Conversations scoped to organization (from JWT)
- ✅ User can only see conversations in current organization
- ✅ Switching organization = different conversation list
- ✅ Simple, secure, no complex UI

---

## 5. Knowledge Base Integration (RAG with LangChain)

### ✅ Already Implemented: Vector Store & RAG

```python
# From lcel_chat_service.py - ALREADY WORKING
self.vectorstore = Chroma(
    embedding_function=self.embeddings,
    persist_directory="./chroma_db"
)

# RAG chain with history
rag_chain_with_history = RunnableWithMessageHistory(
    rag_chain,
    lambda session_id: get_session_history(session_id, db_session),
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)
```

### Knowledge Base Sharing Model

Each document has **visibility level**:

#### 1. **INTERNAL** (Default)
- Only organization members can access
- Example: Farmer's invoices, internal records

#### 2. **SHARED**
- Shared with specific organizations or users
- Example: Phyto company shares product specs with customers

#### 3. **PUBLIC** (Ekumen-provided)
- Available to ALL Ekumen users
- Example: Regulations, general guides

### Document Schema
```sql
CREATE TABLE knowledge_base_documents (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    uploaded_by UUID REFERENCES users(id),

    filename VARCHAR(500),
    file_path VARCHAR(500),  -- Supabase Storage
    document_type VARCHAR(50),  -- 'invoice', 'product_spec', 'regulation', 'manual'

    -- SHARING PERMISSIONS
    visibility VARCHAR(50) DEFAULT 'internal',  -- 'internal', 'shared', 'public'
    shared_with_organizations UUID[],  -- Array of org IDs
    shared_with_users UUID[],  -- Array of user IDs
    is_ekumen_provided BOOLEAN DEFAULT FALSE,

    -- Analytics
    query_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,

    processing_status VARCHAR(50),
    chunk_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Permission-Filtered Retrieval

```python
# LangChain retrieves ONLY accessible documents
async def get_accessible_documents(db, user_id, org_id):
    """Get document IDs accessible to this user/org"""
    query = text("""
        SELECT id FROM knowledge_base_documents
        WHERE
            -- Internal documents from user's org
            (organization_id = :org_id AND visibility = 'internal')

            -- Documents shared with user's org
            OR (:org_id = ANY(shared_with_organizations))

            -- Documents shared with user directly
            OR (:user_id = ANY(shared_with_users))

            -- Public Ekumen documents
            OR (visibility = 'public' AND is_ekumen_provided = true)

        AND processing_status = 'completed'
    """)
    result = await db.execute(query, {"org_id": org_id, "user_id": user_id})
    return [str(row[0]) for row in result.fetchall()]

# IMPORTANT: Chroma uses metadata-based filtering
# When ingesting documents, store document_id in chunk metadata:
for chunk in chunks:
    chunk.metadata["document_id"] = str(doc.id)
    chunk.metadata["organization_id"] = str(doc.organization_id)
    chunk.metadata["filename"] = doc.filename
    chunk.metadata["page_number"] = chunk.metadata.get("page", 0)

# CORRECT Chroma filter syntax (Chroma 0.4.x+):
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,
        "where": {
            "document_id": {
                "$in": accessible_docs  # Use 'where' parameter, not 'filter'
            }
        }
    }
)

# Alternative for complex filters:
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,
        "where": {
            "$or": [
                {"document_id": {"$eq": doc_id}}
                for doc_id in accessible_docs
            ]
        }
    }
)
```

### Use Cases

**Phyto Company (Bayer):**
```python
# Upload product spec, share with customers
{
    "filename": "roundup_technical_sheet.pdf",
    "visibility": "shared",
    "shared_with_organizations": ["cooperative_abc", "farm_dupont"],
    "document_type": "product_spec"
}
```

**Cooperative:**
```python
# Upload best practices, share with all members
{
    "filename": "wheat_cultivation_guide.pdf",
    "visibility": "shared",
    "shared_with_organizations": [],  # All members
    "document_type": "manual"
}
```

**Farmer:**
```python
# Upload invoice, keep private
{
    "filename": "fertilizer_invoice_2024.pdf",
    "visibility": "internal",  # Only this farm
    "document_type": "invoice"
}
```

**Ekumen:**
```python
# Upload regulations, public for all
{
    "filename": "french_phyto_regulations_2024.pdf",
    "visibility": "public",
    "is_ekumen_provided": true,
    "document_type": "regulation"
}
```

---

## 6. Conversation Features

### ✅ Implemented Now
- [x] Create new conversation
- [x] List user's conversations
- [x] Load conversation history
- [x] Send message and get response
- [x] Store tool calls with messages
- [x] Auto-generate conversation title

### ✅ Phase 2
- [ ] Search conversations ("Find when I talked about wheat fungicide")
- [ ] Copy conversation to clipboard
- [ ] Delete conversation
- [ ] Archive conversation (optional)

### ❌ Not Now
- Sharing conversations with advisors
- Bookmarking messages
- Exporting to PDF/CSV

---

## 6. Document Processing & RAG Configuration (CRITICAL)

### LangChain Chunking Strategy

**Use these EXACT parameters for agricultural PDFs:**

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib

# CRITICAL: These parameters are optimized for technical agricultural content
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,           # Good balance for technical content
    chunk_overlap=200,         # 20% overlap captures context across chunks
    length_function=len,
    separators=[
        "\n\n",                # Paragraph breaks (highest priority)
        "\n",                  # Line breaks
        ". ",                  # Sentence ends
        " ",                   # Words
        ""                     # Characters (fallback)
    ],
    keep_separator=True        # Preserve separators for better context
)

async def process_pdf_document(
    doc_id: str,
    file_path: str,
    organization_id: str,
    filename: str,
    db: AsyncSession
) -> int:
    """Process PDF and add to vector store with proper metadata"""

    try:
        # 1. Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # 2. Split into chunks
        chunks = text_splitter.split_documents(documents)

        # 3. Add metadata to EVERY chunk (required for filtering)
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "document_id": str(doc_id),
                "organization_id": str(organization_id),
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "page_number": chunk.metadata.get("page", 0),
                "chunk_hash": hashlib.md5(chunk.page_content.encode()).hexdigest()
            })

        # 4. Add to vector store
        vectorstore.add_documents(chunks)

        # 5. Update document status
        await db.execute(
            update(KnowledgeBaseDocument)
            .where(KnowledgeBaseDocument.id == doc_id)
            .values(processing_status="completed", chunk_count=len(chunks))
        )
        await db.commit()

        return len(chunks)

    except Exception as e:
        # Mark as failed
        await db.execute(
            update(KnowledgeBaseDocument)
            .where(KnowledgeBaseDocument.id == doc_id)
            .values(processing_status="failed", error_message=str(e))
        )
        await db.commit()

        # Clean up partial data
        vectorstore.delete(where={"document_id": {"$eq": str(doc_id)}})

        raise
```

### RAG Prompt Template

**Use this prompt to prevent hallucinations:**

```python
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """Tu es un conseiller agricole expert spécialisé dans l'agriculture française.

RÈGLES CRITIQUES:
1. Utilise UNIQUEMENT les informations dans le contexte fourni ci-dessous
2. Si l'information n'est pas dans le contexte, dis clairement "Je n'ai pas cette information dans ma base de connaissances"
3. Cite TOUJOURS tes sources (nom du document et page)
4. Ne fais JAMAIS de suppositions ou d'extrapolations
5. Pour les produits phytosanitaires, vérifie toujours dans la base EPHY

Contexte disponible:
{context}

Si le contexte est vide, réponds: "Je n'ai pas trouvé d'information pertinente dans la base de connaissances. Puis-je vous aider autrement?"
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# Create RAG chain
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

question_answer_chain = create_stuff_documents_chain(llm, rag_prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)
```

### Complete RAG Service Implementation

```python
async def get_rag_response(
    user_question: str,
    user_id: str,
    org_id: str,
    conversation_history: List[BaseMessage],
    db: AsyncSession
) -> Dict:
    """
    Get RAG response with permission filtering and source tracking
    """

    # 1. Get accessible documents
    accessible_docs = await get_accessible_documents(db, user_id, org_id)

    # 2. Create permission-filtered retriever
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 5,
            "where": {
                "document_id": {
                    "$in": accessible_docs
                }
            }
        }
    )

    # 3. Create RAG chain
    question_answer_chain = create_stuff_documents_chain(llm, rag_prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 4. Invoke with history
    response = await rag_chain.ainvoke({
        "input": user_question,
        "chat_history": conversation_history
    })

    # 5. Extract source documents
    documents_retrieved = []
    for doc in response.get("context", []):
        documents_retrieved.append({
            "document_id": doc.metadata.get("document_id"),
            "filename": doc.metadata.get("filename"),
            "page_number": doc.metadata.get("page_number", 0),
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "chunk_text": doc.page_content[:200],  # First 200 chars
            "relevance_score": 0.0  # Chroma doesn't return scores by default
        })

    return {
        "answer": response["answer"],
        "documents_retrieved": documents_retrieved,
        "knowledge_base_used": len(documents_retrieved) > 0
    }
```

---

## 7. Message Metadata Schema (CRITICAL)

### Exact JSON Structure for `messages.message_metadata`

**All developers MUST use this exact structure:**

```json
{
  "tool_calls": [
    {
      "tool_name": "get_parcel_info",
      "arguments": {"parcel_id": "uuid"},
      "result": {"name": "Tuferes", "surface_ha": 228.54},
      "execution_time_ms": 45,
      "status": "success"
    }
  ],
  "knowledge_base_used": true,
  "documents_retrieved": [
    {
      "document_id": "uuid",
      "filename": "roundup_spec.pdf",
      "relevance_score": 0.89,
      "chunk_index": 2,
      "chunk_text": "Roundup is a glyphosate-based...",
      "page_number": 5
    }
  ],
  "processing_time_ms": 1250,
  "token_count": {
    "prompt_tokens": 450,
    "completion_tokens": 120,
    "total_tokens": 570
  },
  "model": "gpt-4",
  "temperature": 0.1,
  "cost_usd": 0.0342
}
```

**Field Requirements:**
- `tool_calls`: Array of tool executions (empty if none)
- `knowledge_base_used`: Boolean (always present)
- `documents_retrieved`: Array (empty if KB not used)
- `processing_time_ms`: Integer (total response time)
- `token_count`: Object with prompt/completion/total
- `model`: String (LLM model name)
- `temperature`: Float (LLM temperature)
- `cost_usd`: Float (calculated cost)

**Cost Calculation:**
```python
# OpenAI pricing (2024)
GPT4_INPUT_COST_PER_1K = 0.03
GPT4_OUTPUT_COST_PER_1K = 0.06

cost_usd = (
    (prompt_tokens / 1000) * GPT4_INPUT_COST_PER_1K +
    (completion_tokens / 1000) * GPT4_OUTPUT_COST_PER_1K
)
```

---

## 8. Analytics (For Ekumen Admin & Partners)

### Knowledge Base Analytics

**Focus:** How well is knowledge base being used? What are the gaps?

```sql
-- 1. Most used documents by organization
SELECT
    o.name as organization,
    kb.filename,
    kb.document_type,
    kb.query_count,
    kb.visibility
FROM knowledge_base_documents kb
JOIN organizations o ON kb.organization_id = o.id
ORDER BY kb.query_count DESC
LIMIT 20;

-- 2. Knowledge gaps (questions with no KB results)
SELECT
    m.content as question,
    COUNT(*) as frequency,
    o.name as organization
FROM messages m
JOIN conversations c ON m.conversation_id = c.id
JOIN organizations o ON c.organization_id = o.id
WHERE m.sender = 'user'
AND (m.message_metadata->>'knowledge_base_used')::boolean = false
GROUP BY m.content, o.name
ORDER BY frequency DESC
LIMIT 50;

-- 3. Query coverage by organization
SELECT
    o.name as organization,
    COUNT(CASE WHEN (m.message_metadata->>'knowledge_base_used')::boolean = true THEN 1 END) * 100.0 / COUNT(*) as coverage_percent,
    COUNT(*) as total_queries
FROM messages m
JOIN conversations c ON m.conversation_id = c.id
JOIN organizations o ON c.organization_id = o.id
WHERE m.sender = 'user'
GROUP BY o.name
ORDER BY coverage_percent DESC;

-- 4. Shared document effectiveness (for phyto companies)
SELECT
    kb.filename,
    o.name as owner_org,
    kb.query_count,
    array_length(kb.shared_with_organizations, 1) as shared_with_count,
    kb.visibility
FROM knowledge_base_documents kb
JOIN organizations o ON kb.organization_id = o.id
WHERE kb.visibility = 'shared'
ORDER BY kb.query_count DESC;

-- 5. Ekumen-provided content usage
SELECT
    kb.filename,
    kb.document_type,
    kb.query_count,
    COUNT(DISTINCT c.organization_id) as used_by_orgs
FROM knowledge_base_documents kb
LEFT JOIN messages m ON m.message_metadata::jsonb @> jsonb_build_array(jsonb_build_object('doc_id', kb.id::text))
LEFT JOIN conversations c ON m.conversation_id = c.id
WHERE kb.is_ekumen_provided = true
GROUP BY kb.id, kb.filename, kb.document_type, kb.query_count
ORDER BY kb.query_count DESC;
```

### User Satisfaction Tracking
```sql
-- User satisfaction (thumbs up/down)
SELECT
  feedback_type,
  COUNT(*) as count
FROM response_feedback
GROUP BY feedback_type;

-- Questions AI couldn't answer well
SELECT
  m.content as question,
  rf.feedback_type,
  rf.comment
FROM messages m
JOIN response_feedback rf ON rf.message_id = m.id
WHERE rf.feedback_type = 'thumbs_down'
AND rf.feedback_category = 'incomplete';
```

### For Phyto Product Companies
- Track how often their shared documents are used
- See which products are mentioned most
- Identify customer questions about their products
- Measure effectiveness of shared technical sheets

---

## 9. JWT Token Structure (CRITICAL)

### Token Payload

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "farmer@example.com",
  "organization_id": "660e8400-e29b-41d4-a716-446655440001",
  "organization_role": "owner",
  "user_role": "farmer",
  "iat": 1234567890,
  "exp": 1234571490,
  "token_type": "access"
}
```

### Authentication Flow

**Single Organization:**
```
POST /api/v1/auth/login → Returns token with organization_id
```

**Multiple Organizations:**
```
POST /api/v1/auth/login → Returns token with organization_id=null, requires_org_selection=true
POST /api/v1/auth/select-organization → Returns token with organization_id
```

### Middleware (Required Dependencies)

**Configuration (app/core/config.py):**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str  # Min 32 chars, store in .env
    ALGORITHM: str = "HS256"  # Use RS256 for production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

**Complete Middleware Implementation:**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

security = HTTPBearer()

class OrganizationContext(BaseModel):
    organization_id: str
    organization_role: str

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: str):
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extract and validate user from JWT token
    Raises 401 if token invalid, expired, or user not found
    """
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Validate token type
        if payload.get("token_type") != "access":
            raise credentials_exception

        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    # Get user from database
    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception

    # Check user status
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user.status}"
        )

    return user

async def get_org_context(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> OrganizationContext:
    """
    Extract organization context from JWT token
    Raises 403 if organization_id not in token
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        org_id = payload.get("organization_id")
        if org_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context required. Please select an organization."
            )

        return OrganizationContext(
            organization_id=org_id,
            organization_role=payload.get("organization_role", "member")
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def verify_refresh_token(refresh_token: str) -> str:
    """
    Verify refresh token and return user_id
    Raises 401 if invalid or expired
    """
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return user_id

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )
```

**Environment Variables (.env):**
```bash
# NEVER commit this file to git!
SECRET_KEY=your-secret-key-min-32-chars-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### Usage in Endpoints

```python
@router.get("/api/v1/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    org_context: OrganizationContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db)
):
    """List conversations - automatically filtered by org_id from JWT"""
    conversations = await db.execute(
        select(Conversation).where(
            Conversation.user_id == current_user.id,
            Conversation.organization_id == org_context.organization_id,
            Conversation.status == 'active'
        )
    )
    return {"conversations": conversations.scalars().all()}
```

---

## 10. Auto-Generate Conversation Titles

### Implementation

```python
async def auto_generate_title(conversation_id: str, db: AsyncSession):
    """Generate title from first 1-2 messages"""

    # Get first 2 messages
    messages = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(2)
    )
    messages = messages.scalars().all()

    if len(messages) < 1:
        return

    # Create prompt
    prompt = f"""Generate a short title (max 50 chars) for this conversation:
User: {messages[0].content}
Assistant: {messages[1].content if len(messages) > 1 else ''}

Title (no quotes):"""

    # Call LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
    title = await llm.ainvoke(prompt)
    title = title.content.strip()[:50]

    # Update conversation
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(title=title)
    )
    await db.commit()
```

### Trigger

- **When:** After 2nd message in conversation
- **Async:** Run in background task (don't block response)
- **Fallback:** If LLM fails, use first 50 chars of user's first message

---

## 11. Implementation Checklist

### Database Changes Needed
- [ ] Add `organization_id` to `conversations` table
- [ ] Add `title` to `conversations` table (auto-generated)
- [ ] Add `status` to `conversations` table ('active', 'archived', 'deleted')
- [ ] Add `deleted_at` to `conversations` table (soft delete timestamp)
- [ ] Add `last_message_at` to `conversations` table
- [ ] Ensure `message_metadata` JSONB stores tool calls (use exact schema above)
- [ ] Create `response_feedback` table (thumbs up/down)

### API Endpoints Needed
```
POST   /api/v1/conversations              # Create new conversation
GET    /api/v1/conversations              # List user's conversations
GET    /api/v1/conversations/:id          # Get conversation details
DELETE /api/v1/conversations/:id          # Delete conversation
POST   /api/v1/conversations/:id/messages # Send message
GET    /api/v1/conversations/:id/messages # Get conversation history
POST   /api/v1/conversations/:id/feedback # Thumbs up/down
GET    /api/v1/conversations/search       # Search conversations
```

### Frontend Components Needed
```
<ConversationSidebar>
  - Organization selector
  - "New Chat" button
  - Conversation list (grouped by date)
  - Search bar

<ChatInterface>
  - Message list
  - Input box
  - Tool call indicators
  - Thumbs up/down buttons

<OrganizationSelector>
  - Dropdown with user's organizations
  - Switch organization context
```

---

## 8. File Storage (Supabase Storage)

### Audio Files (Voice Journal)
```
Bucket: voice-journal
Path: /{organization_id}/{user_id}/{year}/{month}/{filename}.mp3
Size limit: 10MB per file
Retention: 1 year (configurable)
```

### Field Photos
```
Bucket: field-photos
Path: /{organization_id}/{farm_siret}/{parcel_id}/{filename}.jpg
Size limit: 5MB per file
Retention: Permanent
```

### PDF Reports
```
Bucket: reports
Path: /{organization_id}/{report_type}/{year}/{filename}.pdf
Size limit: 20MB per file
Retention: 5 years (regulatory requirement)
```

### Best Practices
- Use Supabase Storage (integrated with auth)
- Generate signed URLs for temporary access
- Implement file size limits
- Compress images before upload
- Use CDN for frequently accessed files

---

## 9. Weather Integration (weatherapi.com)

### Already Integrated
- ✅ Real-time weather data
- ✅ Historical weather
- ✅ Forecasts

### Store Weather Data
```sql
-- Cache weather data to reduce API calls
CREATE TABLE weather_cache (
  id UUID PRIMARY KEY,
  location_lat NUMERIC(10, 6),
  location_lon NUMERIC(10, 6),
  date DATE,
  temperature_celsius NUMERIC(4, 1),
  humidity_percent NUMERIC(5, 2),
  wind_speed_kmh NUMERIC(5, 2),
  precipitation_mm NUMERIC(6, 2),
  weather_condition VARCHAR(50),
  forecast_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_weather_cache_location_date 
ON weather_cache(location_lat, location_lon, date);
```

### Weather Alerts (Future)
- Frost warnings
- Heavy rain alerts
- High wind warnings
- Optimal spraying conditions

---

## Summary

**Keep it simple. Follow ChatGPT's pattern. Leverage existing LangChain infrastructure.**

### Core Principles
1. ✅ **Linear conversation history** (no sub-threading)
2. ✅ **"New Chat" creates new conversation**
3. ✅ **Unlimited conversations per user**
4. ✅ **ONE organization per session** (no mid-session switching)
5. ✅ **Store tool calls with messages** in message_metadata
6. ✅ **Truncate old messages** when context is full
7. ✅ **Auto-generate conversation titles**
8. ✅ **Simple search and copy** features
9. ✅ **Supabase Storage** for files

### LangChain Integration (No New Infrastructure)
1. ✅ **RunnableWithMessageHistory** - Already handles conversation memory
2. ✅ **Chroma vector store** - Already set up for RAG
3. ✅ **Permission-filtered retrieval** - Simple SQL + filter in retriever
4. ✅ **PostgresChatMessageHistory** - Already saves to messages table

### Knowledge Base
1. ✅ **Internal** - Organization-private documents
2. ✅ **Shared** - Share with specific orgs/users (phyto companies, cooperatives)
3. ✅ **Public** - Ekumen-curated content for all users
4. ✅ **Analytics** - Track usage, gaps, coverage per organization

### Voice Journal → Interventions
1. ✅ **Capture all required fields** in voice_journal_entries table
2. ✅ **Auto-create interventions** with complete data
3. ✅ **Link back to journal** for audit trail
4. ✅ **Whisper + ElevenLabs** integration (existing service stubs)

