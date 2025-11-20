import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import MenuItem, Testimonial, GalleryImage, ContactInquiry

app = FastAPI(title="Luxury Catering API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Luxury Catering API running"}

@app.get("/schema")
def get_schema():
    # Lightweight schema export for admin/viewer tools
    return {
        "menuitem": MenuItem.schema(),
        "testimonial": Testimonial.schema(),
        "galleryimage": GalleryImage.schema(),
        "contactinquiry": ContactInquiry.schema(),
    }

# Seed default content if collections are empty
@app.post("/seed")
def seed_content():
    try:
        # Seed only if empty
        if db is None:
            raise HTTPException(status_code=500, detail="Database not configured")

        if db["menuitem"].count_documents({}) == 0:
            defaults = [
                {
                    "title": "Black Truffle Arancini",
                    "description": "Crisp risotto pearls with aged Parmesan and shaved truffle.",
                    "category": "Canapés",
                    "tags": ["vegetarian", "signature"],
                    "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=1600&auto=format&fit=crop"
                },
                {
                    "title": "Butter-Poached Lobster",
                    "description": "Champagne velouté, fennel pollen, and gold leaf.",
                    "category": "Mains",
                    "tags": ["seafood"],
                    "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1600&auto=format&fit=crop"
                },
                {
                    "title": "Valrhona Chocolate Tart",
                    "description": "Sea salt ganache, vanilla crème, cacao nib praline.",
                    "category": "Desserts",
                    "tags": ["dessert"],
                    "image_url": "https://images.unsplash.com/photo-1551024709-8f23befc6cf7?q=80&w=1600&auto=format&fit=crop"
                },
            ]
            for item in defaults:
                create_document("menuitem", item)

        if db["testimonial"].count_documents({}) == 0:
            for t in [
                {"name": "Amelia R.", "title": "Luxury Wedding, Lake Como", "quote": "Impeccable from first tasting to the final toast. A flawless experience."},
                {"name": "Marcus L.", "title": "Global Summit Gala", "quote": "World-class service that impressed every executive in the room."},
                {"name": "Sofia N.", "title": "Private Chef’s Table", "quote": "Each course arrived like art. Understated, elegant, unforgettable."},
            ]:
                create_document("testimonial", t)

        if db["galleryimage"].count_documents({}) == 0:
            gallery = [
                {"url": "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?q=80&w=1600&auto=format&fit=crop", "alt": "Caviar canapés"},
                {"url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1600&auto=format&fit=crop", "alt": "Fine dining table"},
                {"url": "https://images.unsplash.com/photo-1542826438-5ec323d1cb97?q=80&w=1600&auto=format&fit=crop", "alt": "Elegant dessert"},
                {"url": "https://images.unsplash.com/photo-1529042410759-befb1204b468?q=80&w=1600&auto=format&fit=crop", "alt": "Champagne service"},
                {"url": "https://images.unsplash.com/photo-1541870730196-cd1efcbf5646?q=80&w=1600&auto=format&fit=crop", "alt": "Gourmet plating"},
                {"url": "https://images.unsplash.com/photo-1516683037151-9d56a6a58c89?q=80&w=1600&auto=format&fit=crop", "alt": "Chef in action"}
            ]
            for g in gallery:
                create_document("galleryimage", g)

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Public endpoints for frontend
@app.get("/menu", response_model=List[MenuItem])
def get_menu():
    docs = get_documents("menuitem")
    # Convert _id and timestamps out
    return [MenuItem(**{k: v for k, v in d.items() if k in MenuItem.model_fields}) for d in docs]

@app.get("/testimonials", response_model=List[Testimonial])
def get_testimonials():
    docs = get_documents("testimonial")
    return [Testimonial(**{k: v for k, v in d.items() if k in Testimonial.model_fields}) for d in docs]

@app.get("/gallery", response_model=List[GalleryImage])
def get_gallery():
    docs = get_documents("galleryimage")
    return [GalleryImage(**{k: v for k, v in d.items() if k in GalleryImage.model_fields}) for d in docs]

@app.post("/contact")
def post_contact(payload: ContactInquiry):
    try:
        create_document("contactinquiry", payload)
        return {"status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
