from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.db.database import Base, engine
from app.routes import (
    auth_routes,
    admin_routes,
    package_routes,
    testimonial_routes,
    faq_routes,
    most_visited_routes,
    blog_routes,
    happy_moment_routes,
    site_settings_routes,
    upload_routes,
    enquiry_routes,
    about_routes,
    package_batch_routes,   
    policy_routes,
    hero_routes,
    seasoned_routes
)


# Development/simple deployment approach.
# In production, prefer Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Travel Website API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Images are served straight from Cloudinary's CDN (see upload_service.py),
# so there's no local static mount here.

app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(package_routes.router)
app.include_router(package_batch_routes.router)
app.include_router(testimonial_routes.router)
app.include_router(faq_routes.router)
app.include_router(most_visited_routes.router)
app.include_router(blog_routes.router)
app.include_router(happy_moment_routes.router)
app.include_router(site_settings_routes.router)
app.include_router(upload_routes.router)
app.include_router(enquiry_routes.router)
app.include_router(about_routes.router)
app.include_router(policy_routes.router)
app.include_router(hero_routes.router)
app.include_router(seasoned_routes.router)

@app.get("/health")
def health():
    return {"status": "ok"}
