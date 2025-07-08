# Virtual Wardrobe – Revolutionizing Fashion Organization Through Modern Technology

**Virtual Wardrobe** is a cloud-native application designed to help users efficiently manage their personal wardrobe, reduce overconsumption, and make sustainable fashion choices. With a complete revamp from a traditional tech stack to a modern, scalable architecture, the project now offers enhanced performance, new features, and a smoother user experience.

---

## 🚀 Key Improvements in Version 2.0

| **Component**            | **Old Stack**                        | **New Stack**                                                         |
|--------------------------|--------------------------------------|-----------------------------------------------------------------------|
| **Backend Framework**    | Django (synchronous)                 | FastAPI (asynchronous, OpenAPI support)                               |
| **ORM**                  | Django ORM                           | Prisma ORM (type-safe, auto-generated client)                         |
| **Database**             | SQLite                               | PostgreSQL via Neon Serverless PostgreSQL (scalable & cost-optimized) |
| **Cloud Provider**       | AWS                                  | Google Cloud Platform (VMs, Cloud Storage)                            |
| **Authentication**       | Django Built-in Auth (session-based) | JWT (stateless) + Google OAuth 2.0                                    |
| **Architecture**         | Monolithic                           | Microservices                                                         |
| **Caching**              | Not implemented                      | Redis (in-memory caching)                                             |
| **Database Indexing**    | Not implemented                      | Indexed key tables for optimized query performance                    |
| **Virtual Try-On**       | Not implemented                      | Implemented using the CatVTON model via the fal.ai platform           |
| **Logging & Monitoring** | Not implemented                      | Grafana Loki for real-time log aggregation                            |

---

## 🛠️ Technical Enhancements

### FastAPI over Django

- Transitioned to FastAPI for asynchronous processing and real-time interactions.
- Provides automatic OpenAPI documentation and faster response handling.

### Prisma ORM over Django ORM

- Type-safe queries and schema modeling.
- Easier management of wardrobe data, user collections, and outfit combinations.

### PostgreSQL + Neon Serverless

- Upgraded from SQLite to PostgreSQL for better concurrency and scalability.
- Used **Neon Serverless PostgreSQL** for dynamic auto-scaling and cost savings.

### Redis Caching

- Integrated Redis to reduce database load.
- Improved browsing speed through efficient caching.

### Cloud Infrastructure

- Moved deployment to **Google Cloud Platform**, utilizing:

  - Cloud VMs for scalable compute resources.
  - Cloud Storage for reliable image/media management.

### Scalable Authentication

- Migrated from Django's session-based auth to **JWT** for stateless security.
- Added **Google Authentication (OAuth 2.0)** for seamless login.

### Virtual Try-On

- Introduced visualization of outfits to boost user engagement.

### Database Indexing

- Indexed critical tables (user data, wardrobe items, virtual try-on results).
- Improved performance for searches, recommendations, and history tracking.

### Grafana Loki for Log Aggregation

- Integrated **Grafana Loki** for centralized and structured log aggregation across all microservices.
- Enabled **real-time log monitoring** to streamline debugging and system observability.
- Paired with **Grafana dashboards** to visualize logs, monitor system health, and set alerting rules.

---

## 💡 System Design & Architecture

- Refactored into **microservices**, enabling independent scaling of components.
- Structured for horizontal scalability and fault tolerance.

---

## 📈 Project Outcomes

- **40% faster API responses** with async processing and caching.
- **Improved database performance** with Prisma & PostgreSQL.
- **Highly scalable cloud architecture** with GCP + Neon.
- **Immersive user experience** through Virtual Try-On.
- **Secure, scalable authentication** using JWT & Google SSO.
- Improved observability and debugging through Grafana Loki log aggregation.

---

## 🌿 Sustainability Mission

Virtual Wardrobe empowers users to:

- Track and manage clothing items.
- Make informed fashion decisions.
- Embrace a minimal, sustainable lifestyle through technology.

---

## 🔗 Connect

If you're interested in exploring or contributing to the project, feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/anirudh248) or check out the codebase here on GitHub!
