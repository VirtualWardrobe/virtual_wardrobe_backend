# Virtual Wardrobe – Revolutionizing Fashion Organization Through Modern Technology

**Virtual Wardrobe** is a full-stack, cloud-native application designed to help users efficiently manage their personal wardrobe, reduce overconsumption, and make sustainable fashion choices. Version 2.0 brings a modern, scalable architecture across both frontend and backend, ensuring a smoother, faster, and more immersive user experience.

---

## ✨ What's New in Version 2.0

| **Component**            | **Old Stack**         | **New Stack**                                      |
| ------------------------ | --------------------- | -------------------------------------------------- |
| **Frontend**             | HTML, CSS, JavaScript | Next.js (TypeScript) + Tailwind CSS                |
| **Backend Framework**    | Django (synchronous)  | FastAPI (asynchronous, OpenAPI support)            |
| **ORM**                  | Django ORM            | Prisma ORM (type-safe, auto-generated client)      |
| **Database**             | SQLite                | PostgreSQL via Neon Serverless PostgreSQL          |
| **Cloud Provider**       | AWS                   | Google Cloud Platform (VMs, Cloud Storage)         |
| **Authentication**       | Django Session-based  | JWT (stateless) + Google OAuth 2.0                 |
| **Architecture**         | Monolithic            | Microservices                                      |
| **Caching**              | Not implemented       | Redis (in-memory caching)                          |
| **Database Indexing**    | Not implemented       | Indexed key tables for optimized query performance |
| **Virtual Try-On**       | Not implemented       | CatVTON model via the fal.ai platform              |
| **Logging & Monitoring** | Not implemented       | Grafana Loki + Dashboards for log aggregation      |

---

## 🧑‍💻 Frontend Highlights – Built with Next.js & Tailwind CSS

The frontend was completely re-engineered in **Version 2.0** using **Next.js with TypeScript** and **Tailwind CSS**, offering a modern, responsive, and performant UI. Key improvements:

- **Server-side rendering** for faster initial load times and SEO benefits.
- **Tailwind CSS** for utility-first, maintainable styling.
- **Dynamic outfit filtering** and search for quick discovery.
- **Virtual Try-On** integration with the backend.
- **Mobile-first** design approach for an optimized user experience across devices.

This revamp replaces the basic HTML, CSS, and JS used in the first version.

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

### Virtual Try-On

- Powered by the **CatVTON model** via [fal.ai](https://fal.ai).
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
- **Faster page loads** and enhanced frontend responsiveness.
- **Better debugging** and monitoring with centralized logging.

---

## 🌱 Sustainability Mission

**Virtual Wardrobe** empowers users to:

- Track their fashion inventory.
- Make mindful decisions around purchases.
- Embrace a minimal, sustainable lifestyle through intelligent recommendations and outfit planning.

---

## 🔗 Connect & Contribute

If you're interested in exploring or contributing to the project:

- 📬 [Connect on LinkedIn](https://www.linkedin.com/in/anirudh248)
- 💻 View the full codebase on [GitHub](https://github.com/orgs/VirtualWardrobe/repositories)
