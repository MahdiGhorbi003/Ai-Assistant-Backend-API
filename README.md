# AI Assistant Backend API

A RESTful backend API for an AI Assistant built with Django REST Framework.

The project allows authenticated users to create conversations, send messages to an AI assistant, receive responses from an LLM, and store conversation history.

The project is being developed incrementally, with each version adding a new layer of backend and AI functionality.

---

## Current Version

**V2.0.0 — Backend Hardening + AI Context**

V2 builds on the core backend foundation introduced in V1, adding Redis integration, AI context management, conversation summarization, streaming responses, structured output, improved testing, API documentation, and structured logging.

---

## Features

### Authentication

* User registration
* Email-based authentication
* JWT authentication
* Access token
* Refresh token
* Password validation
* Duplicate email validation
* Custom User model

### Conversations

Authenticated users can:

* Create conversations
* List their conversations
* Retrieve a conversation
* Update a conversation
* Delete a conversation
* Search and filter conversations
* Paginate conversation results

Each conversation belongs to its owner.

Conversation list results are cached using Redis, with cache invalidation when conversations are created, updated, or deleted.

### Messages

Users can:

* Send messages to a conversation
* Receive an AI-generated response
* Store user messages
* Store assistant messages
* Retrieve conversation messages
* Keep conversation history
* Receive streaming AI responses

The API also supports idempotency for message creation through the `Idempotency-Key` header.

### LLM Integration

The project integrates with an LLM through **OpenRouter** using the OpenAI Python SDK.

The LLM integration includes:

* LLM client
* Conversation history
* LLM service layer
* Context management
* Error handling
* Provider error mapping
* System prompts
* Token management
* Structured JSON output

### Permissions

Authenticated users can only access their own conversations and messages.

The API uses Django REST Framework's `IsAuthenticated` permission and user-scoped querysets.

### Validation

The API validates:

* Email format
* Duplicate email
* Password requirements
* Empty conversation titles
* Empty message content
* Structured LLM output using Pydantic schemas

Message roles are read-only so clients cannot manually create assistant messages through the API.

### Rate Limiting

The project uses scoped per-user rate limiting.

* Message creation: `10 requests / minute`
* Message streaming: `5 requests / minute`

### Redis

Redis is used for:

* Conversation list caching
* Cache invalidation
* Message idempotency
* Idempotency locking

### Testing

The project includes tests for:

* User creation
* Superuser creation
* Registration
* Duplicate email registration
* Login
* Invalid login
* Refresh token
* Conversation CRUD
* Conversation ownership
* Message operations
* Message ownership
* Authentication requirements
* LLM service
* Conversation history
* Context management
* Conversation summarization
* Streaming responses
* Structured output
* Redis caching
* Message idempotency
* Rate limiting

### API Documentation

The API is documented using OpenAPI and Swagger UI through `drf-spectacular`.

Swagger UI:

```text
http://127.0.0.1:8000/api/docs/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

A generated OpenAPI schema is also included in:

```text
schema.yml
```

### Logging

The project uses structured JSON logging through `python-json-logger`.

Application logs include timestamps, log levels, logger names, and messages.

### Docker

The project includes:

* Dockerfile
* Docker Compose
* PostgreSQL container
* Django application container
* Redis container

---

## Tech Stack

* Python 3.12
* Django 6.1
* Django REST Framework 3.18
* PostgreSQL 16
* Redis 7
* Simple JWT
* OpenRouter
* OpenAI Python SDK
* Pydantic
* drf-spectacular
* django-filter
* python-json-logger
* Docker
* Docker Compose
* python-dotenv

---

## Architecture Overview

The project follows a simple layered structure.

```text
Client
  │
  ▼
Django REST Framework
  │
  ├── Authentication
  ├── Permissions
  ├── Validation
  └── Rate Limiting
  │
  ▼
Views / ViewSets
  │
  ▼
Serializers
  │
  ▼
Services
  │
  ├── Context Management
  │     ├── Recent Messages
  │     ├── System Prompt
  │     ├── Token Management
  │     └── Conversation Summary
  │
  ├── LLM Service
  │     ├── LLM Client
  │     └── Structured Output
  │
  ▼
OpenRouter
  │
  ▼
LLM
```

Conversation and message data are stored in PostgreSQL.

Redis is used for caching and idempotency.

The LLM integration is separated into client and service layers so that application logic is not directly coupled to the external LLM provider.

---

## Project Structure

```text
AI-Assistant-Backend-API/
│
├── apps/
│   ├── accounts/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── managers.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   └── chat/
│       ├── migrations/
│       ├── services/
│       │   ├── context/
│       │   │   ├── manager.py
│       │   │   ├── recent_messages.py
│       │   │   ├── summary.py
│       │   │   ├── system_prompt.py
│       │   │   └── token_manager.py
│       │   │
│       │   ├── llm/
│       │   │   ├── client.py
│       │   │   ├── exceptions.py
│       │   │   ├── schemas.py
│       │   │   └── structured_output.py
│       │   │
│       │   └── llm_service.py
│       │
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── serializers.py
│       ├── tests.py
│       ├── urls.py
│       └── views.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── requirements.txt
├── schema.yml
├── .env.example
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd AI-Assistant-Backend-API
```

### 2. Create environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then configure the required variables:

```env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=5432

DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

OPENROUTER_API_KEY=
```

Do not commit `.env` to Git.

---

## Running with Docker

Build and start the containers:

```bash
docker compose up --build -d
```

Run database migrations:

```bash
docker compose exec web python manage.py migrate
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

Swagger:

```text
http://127.0.0.1:8000/api/docs/
```

---

## Running the Tests

With Docker:

```bash
docker compose exec web python manage.py test
```

Or with the local virtual environment:

```bash
python manage.py test
```

---

## API Endpoints

All application API endpoints are available under:

```text
/api/v1/
```

### Authentication

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/api/v1/auth/register/` | Register a new user |
| POST | `/api/v1/auth/login/` | Obtain access and refresh tokens |
| POST | `/api/v1/auth/refresh/` | Refresh an access token |

### Conversations

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/v1/conversations/` | List user's conversations |
| POST | `/api/v1/conversations/` | Create a conversation |
| GET | `/api/v1/conversations/{id}/` | Retrieve a conversation |
| PUT | `/api/v1/conversations/{id}/` | Update a conversation |
| PATCH | `/api/v1/conversations/{id}/` | Partially update a conversation |
| DELETE | `/api/v1/conversations/{id}/` | Delete a conversation |

### Messages

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/v1/messages/` | List user's messages |
| POST | `/api/v1/messages/` | Send a message and receive an AI response |
| GET | `/api/v1/messages/{id}/` | Retrieve a message |
| PUT | `/api/v1/messages/{id}/` | Update a message |
| PATCH | `/api/v1/messages/{id}/` | Partially update a message |
| DELETE | `/api/v1/messages/{id}/` | Delete a message |
| POST | `/api/v1/messages/stream/` | Stream an AI response |

---

## Authentication

Protected endpoints require a JWT access token.

Send the token using the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

Example:

```text
POST /api/v1/auth/login/
```

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

Response:

```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

---

## Sending a Message

Create a conversation first:

```text
POST /api/v1/conversations/
```

Example:

```json
{
  "title": "Django Learning"
}
```

Then send a message:

```text
POST /api/v1/messages/
```

Example:

```json
{
  "conversation": 1,
  "content": "What is Django REST Framework?"
}
```

The backend builds the conversation context and sends it to the LLM.

The user message and assistant response are stored in the database.

For message creation requests, an `Idempotency-Key` header can be used to prevent duplicate processing.

---

## Environment Variables

The following environment variables are required:

| Variable | Description |
| -------- | ----------- |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | Enable or disable Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | Allowed hostnames |
| `OPENROUTER_API_KEY` | OpenRouter API key |

---

## Version Roadmap

### V1.0.0 — Core AI Backend

* Django
* Django REST Framework
* PostgreSQL
* Custom User
* JWT Authentication
* User registration
* Login
* Refresh token
* Conversation CRUD
* Message handling
* Conversation history
* LLM API integration
* Permissions
* Validation
* Error handling
* Basic rate limiting
* Environment variables
* Basic testing
* Swagger / OpenAPI
* Basic logging
* Docker
* Docker Compose

### V2.0.0 — Backend Hardening + AI Context

* Recent message context
* System prompts
* Token management
* Conversation summarization
* Streaming responses
* Structured JSON output
* Pydantic schema validation
* Pagination
* Search
* Filtering
* Ordering
* Scoped rate limiting
* Redis caching
* Message idempotency
* Expanded testing
* Improved API documentation
* Structured JSON logging

### V3.0.0 — Tool Calling

Planned features:

* Tool calling engine
* Tool interface
* Tool registry
* Tool schemas
* Tool validation
* Tool execution
* Tool error handling
* Tool result handling
* Calculator tool
* Weather tool
* Web search tool
* Custom tools
* Tool calling tests

### V4.0.0 — RAG + Background Processing

Planned features:

* Document upload
* Document management
* File upload security
* PDF and TXT extraction
* Text chunking
* Embeddings
* PostgreSQL + pgvector
* Vector search
* Semantic search
* Retrieval
* RAG pipeline
* Context injection
* Source citations
* Celery
* Background document processing
* Embedding jobs
* RAG tests

---

## Project Goals

The main goal of this project is to progressively build a production-oriented backend for an AI Assistant while learning and applying backend engineering concepts.

The project will gradually evolve from a basic REST API into a system supporting:

```text
REST API
   ↓
Authentication & Authorization
   ↓
LLM Integration
   ↓
Context Management
   ↓
Streaming & Structured Output
   ↓
Tool Calling
   ↓
RAG
   ↓
Background Processing
```

---

## Development Approach

The project is developed incrementally.

Each version introduces new backend or AI concepts while keeping the previous functionality as a foundation.

The focus is on learning and applying:

* Backend architecture
* API design
* Authentication
* Authorization
* Database design
* External API integration
* Testing
* Docker
* API documentation
* Logging
* AI application development
* Git and version control

---

## Project Status

**Current release: V2.0.0**

V2 builds on the core backend foundation and adds Redis integration, context management, conversation summarization, streaming, structured output, expanded testing, improved API documentation, and structured logging.

Future versions will extend the system with tool calling, RAG, and background processing.

---

## License

This project is currently developed as a personal learning and portfolio project.