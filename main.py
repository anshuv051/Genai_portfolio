
import os
import io
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import pypdf
import docx
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Import from local modules
from generator import generate_portfolio
from database import PortfolioVectorDB
from models import init_db, User, Portfolio, Analytics, ContactSubmission
from auth import get_db, get_current_user, create_access_token, verify_password, get_password_hash

# Import additional utilities
import uuid
import logging

# Initialize
load_dotenv()
init_db()

# --- THEME CONFIGURATION ---
THEMES = {
    "midnight": {
        "name": "Midnight",
        "bg": "#0a0a0f",
        "text": "#e4e4e7",
        "text_dim": "#71717a",
        "primary": "#8b5cf6",
        "secondary": "#ec4899",
        "card_bg": "rgba(30, 30, 40, 0.8)",
        "border": "rgba(139, 92, 246, 0.2)"
    },
    "ocean": {
        "name": "Ocean",
        "bg": "#0c1929",
        "text": "#e0f2fe",
        "text_dim": "#7dd3fc",
        "primary": "#06b6d4",
        "secondary": "#3b82f6",
        "card_bg": "rgba(12, 25, 41, 0.9)",
        "border": "rgba(6, 182, 212, 0.3)"
    },
    "sunset": {
        "name": "Sunset",
        "bg": "#1a0a0a",
        "text": "#fef3c7",
        "text_dim": "#fbbf24",
        "primary": "#f59e0b",
        "secondary": "#ef4444",
        "card_bg": "rgba(40, 20, 20, 0.9)",
        "border": "rgba(245, 158, 11, 0.3)"
    },
    "forest": {
        "name": "Forest",
        "bg": "#0a1a0f",
        "text": "#dcfce7",
        "text_dim": "#86efac",
        "primary": "#22c55e",
        "secondary": "#14b8a6",
        "card_bg": "rgba(10, 26, 15, 0.9)",
        "border": "rgba(34, 197, 94, 0.3)"
    }
}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
db_vector = PortfolioVectorDB()

# --- FILE EXTRACTION HELPER ---
def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from PDF, DOCX, or TXT files"""
    ext = filename.lower().split('.')[-1]
    
    if ext == 'pdf':
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    elif ext == 'docx':
        doc = docx.Document(io.BytesIO(file_content))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    elif ext == 'txt':
        return file_content.decode('utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file format: {ext}")

# --- IMAGE EXTRACTION ---
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_images_from_pdf(file_content: bytes, user_id: int) -> str:
    """Extract images from PDF - Simplified version
    
    Returns a placeholder profile image since PDF image extraction is unreliable.
    """
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join("static", "uploads", str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a placeholder profile image with human silhouette
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple placeholder image with human silhouette
        img = Image.new('RGB', (200, 200), color=(70, 80, 100))
        draw = ImageDraw.Draw(img)
        
        # Draw a circle background
        draw.ellipse([20, 20, 180, 180], fill=(90, 100, 120), outline=(120, 130, 150), width=3)
        
        # Draw human head (circle)
        head_color = (200, 200, 200)
        draw.ellipse([75, 45, 125, 95], fill=head_color, outline=(150, 150, 150), width=2)
        
        # Draw human body (rounded rectangle/ellipse)
        draw.ellipse([55, 90, 145, 160], fill=head_color, outline=(150, 150, 150), width=2)
        
        img_uuid = str(uuid.uuid4())[:8]
        img_filename = f"profile_{img_uuid}.jpg"
        img_path = os.path.join(upload_dir, img_filename)
        
        img.save(img_path, "JPEG", quality=90)
        logger.info(f"Created placeholder profile image: {img_filename}")
        
        return f"/static/uploads/{user_id}/{img_filename}"
        
    except Exception as e:
        logger.error(f"Error creating placeholder image: {e}")
        return None


def extract_images_from_docx(file_content: bytes, user_id: int) -> str:
    """Extract images from DOCX - Simplified version
    
    Returns a placeholder profile image since DOCX image extraction is unreliable.
    """
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join("static", "uploads", str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a placeholder profile image with human silhouette
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple placeholder image with human silhouette
        img = Image.new('RGB', (200, 200), color=(70, 80, 100))
        draw = ImageDraw.Draw(img)
        
        # Draw a circle background
        draw.ellipse([20, 20, 180, 180], fill=(90, 100, 120), outline=(120, 130, 150), width=3)
        
        # Draw human head (circle)
        head_color = (200, 200, 200)
        draw.ellipse([75, 45, 125, 95], fill=head_color, outline=(150, 150, 150), width=2)
        
        # Draw human body (rounded rectangle/ellipse)
        draw.ellipse([55, 90, 145, 160], fill=head_color, outline=(150, 150, 150), width=2)
        
        img_uuid = str(uuid.uuid4())[:8]
        img_filename = f"profile_{img_uuid}.jpg"
        img_path = os.path.join(upload_dir, img_filename)
        
        img.save(img_path, "JPEG", quality=90)
        logger.info(f"Created placeholder profile image for DOCX: {img_filename}")
        
        return f"/static/uploads/{user_id}/{img_filename}"
        
    except Exception as e:
        logger.error(f"Error creating placeholder image: {e}")
        return None

# --- PUBLIC ROUTES ---
@app.get("/favicon.ico")
async def favicon():
    """Handle favicon.ico request to avoid 404 errors"""
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": {}, "error": "Invalid credentials"})
    
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite="lax")
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": {}, "error": "Username taken"})
    
    new_user = User(username=username, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
async def logout():
    """Logout endpoint - clears the authentication cookie"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

# --- PROTECTED ADMIN ROUTES ---
async def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token = token.split(" ")[1]
    return await get_current_user(token, db)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    # Get or create analytics
    analytics = db.query(Analytics).filter(Analytics.user_id == user.id).first()
    if not analytics:
        analytics = Analytics(user_id=user.id)
        db.add(analytics)
        db.commit()
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.post("/update-key")
async def update_key(
    key: str = Form(...),
    user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    user.openrouter_key = key
    db.commit()
    return {"status": "success", "message": "API key updated"}

@app.post("/update-profile-image")
async def update_profile_image(
    image_url: str = Form(...),
    user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Update user's profile image URL"""
    user.profile_image = image_url if image_url.strip() else None
    db.commit()
    return {"status": "success", "message": "Profile image updated"}

@app.post("/update-theme")
async def update_theme(
    theme: str = Form(...),
    user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    valid_themes = ["midnight", "ocean", "sunset", "forest"]
    if theme not in valid_themes:
        raise HTTPException(status_code=400, detail="Invalid theme")
    
    user.theme = theme
    db.commit()
    return {"status": "success", "message": f"Theme set to {theme}"}

@app.get("/themes")
async def get_themes():
    """Get all available themes"""
    return {"themes": THEMES}

@app.post("/generate")
async def process_resume(
    file: UploadFile = File(...), 
    user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        # 1. Extract Text (supports PDF, DOCX, TXT)
        content = await file.read()
        try:
            resume_text = extract_text_from_file(content, file.filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # 2. Extract images from PDF or DOCX
        profile_image_path = None
        try:
            if file.filename.lower().endswith('.pdf'):
                profile_image_path = extract_images_from_pdf(content, user.id)
            elif file.filename.lower().endswith('.docx'):
                profile_image_path = extract_images_from_docx(content, user.id)
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            profile_image_path = None
        
        # 3. AI Generation (using User's Key if available)
        # Check if API key is provided
        if not user.openrouter_key:
            raise HTTPException(
                status_code=400, 
                detail="OpenRouter API key not found. Please add your API key in the dashboard before generating a portfolio."
            )
        
        try:
            result = generate_portfolio(resume_text, api_key=user.openrouter_key)
        except Exception as e:
            logger.error(f"Error generating portfolio: {e}")
            error_msg = str(e)
            # Check if it's an API key related error
            if "401" in error_msg or "User not found" in error_msg:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid API key. Please check your OpenRouter API key in the dashboard."
                )
            raise HTTPException(status_code=500, detail=f"Failed to generate portfolio: {error_msg}")
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 4. RAG Indexing
        try:
            chunks = [resume_text[i:i+1000] for i in range(0, len(resume_text), 1000)]
            metadatas = [{"source": "resume"} for _ in chunks]
            db_vector.upsert_resume(user.id, "main_resume", chunks, metadatas)
        except Exception as e:
            logger.error(f"Error indexing resume: {e}")
            # Continue even if indexing fails
        
        # 5. Save profile image (prefer extracted image over AI-generated)
        try:
            if profile_image_path:
                user.profile_image = profile_image_path
            else:
                structured_data = result.get("structured_data", {})
                profile_image = structured_data.get("profile_image")
                if profile_image and isinstance(profile_image, str) and profile_image.startswith("http"):
                    user.profile_image = profile_image
            db.commit()
        except Exception as e:
            logger.error(f"Error saving profile image: {e}")
            db.rollback()
        
        # 6. Save to DB
        try:
            portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
            if portfolio:
                portfolio.content = result["portfolio_content"]
            else:
                portfolio = Portfolio(user_id=user.id, content=result["portfolio_content"])
                db.add(portfolio)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save portfolio: {str(e)}")
        
        return {"status": "success", "portfolio_id": portfolio.id, "message": "Portfolio generated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_resume: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- ANALYTICS & CONTACTS ---
@app.get("/analytics-data")
async def get_analytics_data(user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    """Get analytics data for dashboard"""
    analytics = db.query(Analytics).filter(Analytics.user_id == user.id).first()
    contacts_count = db.query(ContactSubmission).filter(ContactSubmission.user_id == user.id).count()
    
    return {
        "total_views": analytics.total_visits if analytics else 0,
        "total_chats": analytics.chat_interactions if analytics else 0,
        "total_contacts": contacts_count
    }

@app.get("/contacts-data")
async def get_contacts_data(user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    """Get contact submissions for dashboard"""
    contacts = db.query(ContactSubmission).filter(ContactSubmission.user_id == user.id).order_by(ContactSubmission.submitted_at.desc()).all()
    return [
        {
            "email": c.visitor_email,
            "message": c.message,
            "name": c.visitor_name,
            "created_at": c.submitted_at.isoformat() if c.submitted_at else ""
        }
        for c in contacts
    ]

# --- VISITOR / PUBLIC VIEW ---
@app.get("/p/{username}", response_class=HTMLResponse)
async def public_portfolio(request: Request, username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Refresh to get latest theme
    db.refresh(user)
    
    # Also extract contact info from structured_data if available
    structured_data = user.portfolios[0].content
    contact_info = structured_data.get('contact', {}) if structured_data else {}
    
    # Track visit
    analytics = db.query(Analytics).filter(Analytics.user_id == user.id).first()
    if analytics:
        analytics.total_visits += 1
        db.commit()
    
    portfolio_data = user.portfolios[0].content
    # Handle old theme values or None
    current_theme = user.theme
    if current_theme not in THEMES:
        current_theme = "midnight"
    user_theme = current_theme
    theme_config = THEMES.get(user_theme, THEMES["midnight"])
    
    return templates.TemplateResponse("portfolio_public.html", {
        "request": request,
        "p": portfolio_data,
        "username": username,
        "user_id": user.id,
        "theme": theme_config,
        "user_theme": user_theme,
        "profile_image": user.profile_image,
        "contact": contact_info
    })

@app.post("/chat/{user_id}")
async def public_chat(user_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        query = data.get("query")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Track chat interaction
        analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()
        if analytics:
            analytics.chat_interactions += 1
            db.commit()

        context_chunks = db_vector.query_resume(user_id, query)
        context = "\n".join(context_chunks)
    
        if not context:
            return {"response": "I don't have enough information from the resume to answer that question. The portfolio owner hasn't uploaded their resume yet."}
    
        sys_prompt = f"""
        ROLE: You are the professional Digital Representative for {user.username}.
        MISSION: Your mission is to answer questions about {user.username}'s professional background, skills, and experience only.

        STRICT BOUNDARIES:
        1. ONLY answer questions related to {user.username}'s career, projects, skills, education, and professional interests.
        2. DECLINE all off-topic, personal, political, or philosophical questions.
        3. If asked about something NOT in the Resume Context, say: "I'm sorry, I don't have that information. I am specifically trained to answer questions about {user.username}'s professional background."
        4. NEVER provide personal advice, life tips, or general trivia.
        5. Maintain a professional, helpful, and representative tone at all times.

        RESUME CONTEXT:
        {context}
        """
    
        # Dynamic LLM for Chat
        user_llm = ChatOpenAI(
            model="openai/gpt-oss-120b:free",
            openai_api_key=user.openrouter_key or os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
        )
    
        response = user_llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=query)
        ])
    
        return {"response": response.content}
    
    except Exception as e:
        import logging
        logging.error(f"Chat error: {str(e)}")
        return {"response": "Sorry, I'm having trouble responding right now. Please try again later."}

@app.post("/contact/{user_id}")
async def submit_contact(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Handle contact form submissions"""
    # Use request.form() to parse FormData from the frontend
    form_data = await request.form()
    name = form_data.get("name")
    email = form_data.get("email")
    message = form_data.get("message")
    
    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    contact = ContactSubmission(
        user_id=user_id,
        visitor_name=name,
        visitor_email=email,
        message=message
    )
    db.add(contact)
    db.commit()
    
    return {"status": "success", "message": "Message sent successfully!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
