# Virtual Wardrobe – Revolutionizing Fashion Organization Through Modern Technology

**Virtual Wardrobe** is a cloud-native application designed to help users efficiently manage their personal wardrobe, reduce overconsumption, and make sustainable fashion choices. With a complete revamp from a traditional tech stack to a modern, scalable architecture, the project now offers enhanced performance, real-time features, and a smoother user experience.

---

## 🚀 Key Improvements in Version 2.0

| **Component**         | **Old Stack**                        | **New Stack**                                                       |
| --------------------- | ------------------------------------ | ------------------------------------------------------------------- |
| **Backend Framework** | Django (synchronous)                 | FastAPI (asynchronous, OpenAPI support)                             |
| **ORM**               | Django ORM                           | Prisma ORM (type-safe, auto-generated client)                       |
| **Database**          | SQLite                               | PostgreSQL + Neon Serverless PostgreSQL (scalable & cost-optimized) |
| **Cloud Provider**    | AWS                                  | Google Cloud Platform (VMs, Cloud Storage)                          |
| **Authentication**    | Django Built-in Auth (session-based) | JWT (stateless) + Google OAuth 2.0                                  |
| **Caching**           | None                                 | Redis (in-memory caching)                                           |
| **Architecture**      | Monolithic                           | Microservices + Containerization (Docker)                           |
| **Virtual Try-On**    | Static views                         | Real-time virtual try-on technology                                 |
| **Database Indexing** | Not implemented                      | Indexed key tables for optimized query performance                  |

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
- Added **Neon Serverless PostgreSQL** for dynamic auto-scaling and cost savings.

### Redis Caching

- Integrated Redis to reduce database load and enhance outfit browsing speed.

### Cloud Infrastructure

- Moved deployment to **Google Cloud Platform**, utilizing:

  - Cloud VMs for scalable compute resources.
  - Cloud Storage for reliable image/media management.

### Scalable Authentication

- Migrated from Django's session-based auth to **JWT** for stateless security.
- Added **Google Authentication (OAuth 2.0)** for seamless login.

### Virtual Try-On

- Introduced real-time visualization of outfits to boost user engagement.

### Database Indexing

- Indexed critical tables (user data, outfits, clothing categories).
- Improved performance for searches, recommendations, and history tracking.

---

## 💡 System Design & Architecture

- Refactored into **microservices**, enabling independent scaling of components.
- **Containerized** using Docker for simplified deployment and maintenance.
- Structured for horizontal scalability and fault tolerance.

---

## 📈 Project Outcomes

- **40% faster API responses** with async processing and caching.
- **Improved database performance** with Prisma & PostgreSQL.
- **Highly scalable cloud architecture** with GCP + Neon.
- **Immersive user experience** through Virtual Try-On.
- **Secure, scalable authentication** using JWT & Google SSO.

---

## 🌿 Sustainability Mission

Virtual Wardrobe empowers users to:

- Track and manage clothing items.
- Make informed fashion decisions.
- Embrace a minimal, sustainable lifestyle through technology.

---

## 🔗 Connect

If you're interested in exploring or contributing to the project, feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/anirudh248) or check out the codebase here on GitHub!
