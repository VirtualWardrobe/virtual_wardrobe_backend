# Virtual Wardrobe – Backend (v2.0)

The **Virtual Wardrobe Backend** is a high-performance, scalable API built with **FastAPI**, **Prisma**, **Redis**, and deployed on **Google Cloud Platform**. It supports outfit management, virtual try-on, authentication, and more through a microservices-based architecture.

---

## ✨ What's New in Backend (v2.0)

| Component            | Old Stack       | New Stack                                          |
| -------------------- | --------------- | -------------------------------------------------- |
| Backend Framework    | Django (sync)   | FastAPI (async, OpenAPI support)                   |
| ORM                  | Django ORM      | Prisma ORM (type-safe, auto-generated client)      |
| Database             | SQLite          | PostgreSQL via Neon Serverless                     |
| Authentication       | Django Sessions | JWT (stateless) + Google OAuth 2.0                 |
| Architecture         | Monolithic      | Microservices                                      |
| Caching              | Not Implemented | Redis (in-memory caching)                          |
| Database Indexing    | Not Implemented | Indexed tables for optimized query performance     |
| Virtual Try-on       | Not Implemented | Virtual Try-on API (Vertex AI)                     |
| Logging & Monitoring | Not Implemented | Grafana Loki + Dashboards for real-time monitoring |

---

## ⚙️ Backend Enhancements – Powered by FastAPI, Prisma, and GCP

### FastAPI

- Asynchronous, high-performance API framework.
- Auto-generates OpenAPI (Swagger) docs.
- Fast response times and better scalability.

### Prisma ORM

- Type-safe and auto-generated client.
- Simple schema definitions and DB migrations.
- Clean data modeling for users, items, and outfit combinations.

### PostgreSQL + Neon Serverless

- Replaces SQLite with serverless PostgreSQL for scalability.
- Auto-scaling capabilities to handle fluctuating traffic.

### Redis Caching

- Speeds up browsing and reduces backend load.
- Cached filters, outfits, and frequently queried data.

### Cloud Infrastructure on GCP

- Cloud VMs for compute.
- Cloud Storage for static/media assets.
- Enables CI/CD and scalable deployments.

### Authentication System

- Stateless JWT-based authentication.
- Integrated Google OAuth 2.0 for SSO.
- Scalable and secure.

### Virtual Try-on

- Powered by the virtual try-on API provided by Vertex AI.
- Users can visualize outfits directly in the app.

### Observability with Grafana Loki

- Real-time logs and system health monitoring.
- Debug and analyze across microservices.

---

## 🧱 System Architecture

- Microservices-based design for modularity and scalability.
- Stateless services with dedicated caching, logging, and storage layers.
- Cloud-optimized deployment with environment-based configurations.

---

## 📊 Performance Gains

- **40% faster API responses** via async FastAPI and Redis caching.
- **Improved data management** with Prisma and PostgreSQL.
- **Seamless authentication** and smoother login flows.
- **Better debugging** and monitoring with centralized logging.

---

## 🔗 Connect & Contribute

If you're interested in exploring or contributing to the project:

- 📬 [Connect on LinkedIn](https://www.linkedin.com/in/anirudh248)
- 💻 View the full codebase on [GitHub](https://github.com/orgs/VirtualWardrobe/repositories)
