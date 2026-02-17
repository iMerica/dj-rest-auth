# dj-rest-auth Demo Architecture

This directory contains a complete demonstration of a modern Single Page Application (SPA) authentication flow using `dj-rest-auth`.

## Overview

The demo consists of two main components:

1.  **Backend (`demo/backend`)**: A Django project using `dj-rest-auth`, `django-allauth`, and `djangorestframework-simplejwt`. It exposes REST APIs for registration, login, and Multi-Factor Authentication (MFA).
2.  **Frontend (`demo/spa-client`)**: A Next.js application that consumes the backend APIs. It demonstrates a complete user flow including registration, login, MFA setup (QR code), and MFA verification.

## Architecture Diagram

```mermaid
graph TD
    User[User / Browser]
    subgraph Frontend [Next.js App (Port 3000)]
        Pages[Pages]
        AuthContext[Auth Context]
        ApiClient[Axios Client]
    end
    subgraph Backend [Django API (Port 8000)]
        DjRestAuth[dj-rest-auth]
        AllAuth[django-allauth]
        MFA[MFA App]
        DB[(SQLite DB)]
    end

    User -->|Interacts| Pages
    Pages -->|Uses| AuthContext
    AuthContext -->|Requests| ApiClient
    ApiClient -->|HTTP Requests| DjRestAuth
    
    DjRestAuth -->|Auth Logic| AllAuth
    DjRestAuth -->|MFA Logic| MFA
    AllAuth -->|Persists| DB
    MFA -->|Persists| DB

    note1[Login Flow]
    User -.->|1. Credentials| Pages
    Pages -.->|2. Login| DjRestAuth
    DjRestAuth -.->|3. MFA Required + Ephemeral Token| Pages
    Pages -.->|4. Verify Code + Token| DjRestAuth
    DjRestAuth -.->|5. Auth Token / Session| User
```

## Running the Demo

The easiest way to run the demo is with Docker Compose:

```bash
cd demo
docker-compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
