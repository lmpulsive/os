import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

# --- Enums from Prisma Schema ---
class EntitlementSource(str, Enum):
    purchase = "purchase"
    promo = "promo"
    admin = "admin"
    default = "default"

class AdminRole(str, Enum):
    editor = "editor"
    publisher = "publisher"
    superadmin = "superadmin"

# --- Pydantic Models (JSON Schemas mapped to Python) ---

# User Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    createdAt: datetime.datetime
    updatedAt: datetime.datetime

# Song Models
class SongCreate(BaseModel):
    title: str
    artist: str
    bpm: int
    durationSeconds: int
    beatmapJson: Dict # Maps to Prisma's Json type
    audioPath: str
    coverPath: Optional[str] = None
    version: str = "1.0"
    isPublished: bool = False

class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    bpm: Optional[int] = None
    durationSeconds: Optional[int] = None
    beatmapJson: Optional[Dict] = None
    audioPath: Optional[str] = None
    coverPath: Optional[str] = None
    version: Optional[str] = None
    isPublished: Optional[bool] = None

class SongResponse(BaseModel):
    id: UUID
    title: str
    artist: str
    bpm: int
    durationSeconds: int
    beatmapJson: Dict
    audioPath: str
    coverPath: Optional[str] = None
    version: str
    isPublished: bool
    createdAt: datetime.datetime
    updatedAt: datetime.datetime

# UserEntitlement Models
class UserEntitlementCreate(BaseModel):
    userId: UUID
    songId: UUID
    source: EntitlementSource

class UserEntitlementResponse(BaseModel):
    userId: UUID
    songId: UUID
    source: EntitlementSource
    grantedAt: datetime.datetime

# PerformanceMetric Models (Forward Declaration for GameplaySessionResponse)
class PerformanceMetricResponse(BaseModel):
    sessionId: UUID
    score: int
    accuracy: float
    maxCombo: Optional[int] = None
    modifiers: Optional[Dict] = None # Maps to Prisma's Json type
    submittedAt: datetime.datetime
    replayHash: Optional[str] = None
    signature: Optional[str] = None

class PerformanceMetricCreate(BaseModel):
    score: int
    accuracy: float
    maxCombo: Optional[int] = None
    modifiers: Optional[Dict] = None
    replayHash: Optional[str] = None
    signature: Optional[str] = None

# GameplaySession Models
class GameplaySessionCreate(BaseModel):
    userId: UUID
    songId: UUID
    songVersion: str
    clientVersion: str
    endedAt: Optional[datetime.datetime] = None
    deviceInfo: Optional[str] = None
    isSynced: bool = False

class GameplaySessionUpdate(BaseModel):
    endedAt: Optional[datetime.datetime] = None
    deviceInfo: Optional[str] = None
    isSynced: Optional[bool] = None

class GameplaySessionResponse(BaseModel):
    id: UUID
    userId: UUID
    songId: UUID
    songVersion: str
    clientVersion: str
    startedAt: datetime.datetime
    endedAt: Optional[datetime.datetime] = None
    deviceInfo: Optional[str] = None
    isSynced: bool
    performance: Optional[PerformanceMetricResponse] = None # Nested relationship

# Purchase Models
class PurchaseCreate(BaseModel):
    userId: UUID
    songId: UUID
    priceCents: int
    currency: str = "USD"
    paymentProcessor: Optional[str] = None
    paymentReference: Optional[str] = None
    refunded: bool = False

class PurchaseUpdate(BaseModel):
    priceCents: Optional[int] = None
    currency: Optional[str] = None
    paymentProcessor: Optional[str] = None
    paymentReference: Optional[str] = None
    refunded: Optional[bool] = None

class PurchaseResponse(BaseModel):
    id: UUID
    userId: UUID
    songId: UUID
    priceCents: int
    currency: str
    paymentProcessor: Optional[str] = None
    paymentReference: Optional[str] = None
    purchasedAt: datetime.datetime
    refunded: bool

# Admin Models
class AdminCreate(BaseModel):
    userId: UUID
    role: AdminRole

class AdminUpdate(BaseModel):
    role: Optional[AdminRole] = None

class AdminResponse(BaseModel):
    id: UUID
    userId: UUID
    role: AdminRole
    grantedAt: datetime.datetime

# --- In-memory "Database" ---
# In a real app, this would be replaced with database queries via an ORM
users_db: Dict[UUID, UserResponse] = {}
songs_db: Dict[UUID, SongResponse] = {}
user_entitlements_db: Dict[str, UserEntitlementResponse] = {} # Key: f"{userId}-{songId}"
gameplay_sessions_db: Dict[UUID, GameplaySessionResponse] = {}
performance_metrics_db: Dict[UUID, PerformanceMetricResponse] = {} # Key: sessionId
purchases_db: Dict[UUID, PurchaseResponse] = {}
admins_db: Dict[UUID, AdminResponse] = {} # Key is Admin.id, not User.id

app = FastAPI(
    title="Rhythm Game API",
    version="1.0.0",
    description="API for managing users, songs, gameplay sessions, purchases, and admin roles for a rhythm game."
)

# --- Dependency to simulate a database session (optional but good practice) ---
# In a real app, this would yield a database connection or Prisma client instance
def get_db():
    try:
        yield
    finally:
        # In a real app, you might close the connection here
        pass

# --- API Routes ---

@app.get("/")
async def root():
    return {"message": "Welcome to the Rhythm Game API!"}

# --- User Routes ---
@app.get("/users", response_model=List[UserResponse])
async def get_all_users():
    return list(users_db.values())

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    # Simulate unique email constraint
    if any(u.email == user_data.email for u in users_db.values()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    now = datetime.datetime.now(datetime.timezone.utc)
    new_user = UserResponse(
        id=uuid4(),
        createdAt=now,
        updatedAt=now,
        **user_data.model_dump() # .dict() for pydantic v1
    )
    users_db[new_user.id] = new_user
    return new_user

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: UUID):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, user_data: UserUpdate):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True) # .dict(exclude_unset=True) for pydantic v1
    for key, value in update_data.items():
        setattr(user, key, value)
    user.updatedAt = datetime.datetime.now(datetime.timezone.utc)
    users_db[user_id] = user # Update in DB
    return user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID):
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    del users_db[user_id]
    # In a real app, also delete related data (sessions, entitlements, purchases, admin)
    # or implement soft delete.

# --- Song Routes ---
@app.get("/songs", response_model=List[SongResponse])
async def get_all_songs():
    return list(songs_db.values())

@app.post("/songs", response_model=SongResponse, status_code=status.HTTP_201_CREATED)
async def create_song(song_data: SongCreate):
    now = datetime.datetime.now(datetime.timezone.utc)
    new_song = SongResponse(
        id=uuid4(),
        createdAt=now,
        updatedAt=now,
        **song_data.model_dump()
    )
    songs_db[new_song.id] = new_song
    return new_song

@app.get("/songs/{song_id}", response_model=SongResponse)
async def get_song_by_id(song_id: UUID):
    song = songs_db.get(song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    return song

@app.put("/songs/{song_id}", response_model=SongResponse)
async def update_song(song_id: UUID, song_data: SongUpdate):
    song = songs_db.get(song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    update_data = song_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(song, key, value)
    song.updatedAt = datetime.datetime.now(datetime.timezone.utc)
    songs_db[song_id] = song
    return song

@app.delete("/songs/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_song(song_id: UUID):
    if song_id not in songs_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    del songs_db[song_id]
    # In a real app, also delete related data (sessions, entitlements, purchases)

# --- GameplaySession Routes ---
@app.post("/gameplaysessions", response_model=GameplaySessionResponse, status_code=status.HTTP_201_CREATED)
async def create_gameplay_session(session_data: GameplaySessionCreate):
    if session_data.userId not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if session_data.songId not in songs_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    now = datetime.datetime.now(datetime.timezone.utc)
    new_session = GameplaySessionResponse(
        id=uuid4(),
        startedAt=now,
        **session_data.model_dump()
    )
    gameplay_sessions_db[new_session.id] = new_session
    return new_session

@app.get("/gameplaysessions/{session_id}", response_model=GameplaySessionResponse)
async def get_gameplay_session_by_id(session_id: UUID):
    session = gameplay_sessions_db.get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gameplay session not found")
    
    # Attach performance if it exists (simulating join)
    session.performance = performance_metrics_db.get(session_id)
    return session

@app.put("/gameplaysessions/{session_id}", response_model=GameplaySessionResponse)
async def update_gameplay_session(session_id: UUID, session_data: GameplaySessionUpdate):
    session = gameplay_sessions_db.get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gameplay session not found")

    update_data = session_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    gameplay_sessions_db[session_id] = session
    return session

# --- PerformanceMetric Routes (nested under GameplaySession) ---
@app.post("/gameplaysessions/{session_id}/performance", response_model=PerformanceMetricResponse, status_code=status.HTTP_201_CREATED)
async def submit_performance_metrics(session_id: UUID, performance_data: PerformanceMetricCreate):
    if session_id not in gameplay_sessions_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gameplay session not found")
    if session_id in performance_metrics_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Performance metrics already exist for this session")

    now = datetime.datetime.now(datetime.timezone.utc)
    new_performance = PerformanceMetricResponse(
        sessionId=session_id,
        submittedAt=now,
        **performance_data.model_dump()
    )
    performance_metrics_db[session_id] = new_performance
    
    # Optionally update the session to mark it as ended or synced if needed
    # session = gameplay_sessions_db[session_id]
    # session.endedAt = now # Could set this here or via a separate PUT on session
    # session.isSynced = True # Could set this here
    # gameplay_sessions_db[session_id] = session

    return new_performance

@app.get("/gameplaysessions/{session_id}/performance", response_model=PerformanceMetricResponse)
async def get_performance_metrics(session_id: UUID):
    performance = performance_metrics_db.get(session_id)
    if not performance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance metrics not found for this session")
    return performance

# --- Purchase Routes ---
@app.get("/purchases", response_model=List[PurchaseResponse])
async def get_all_purchases():
    return list(purchases_db.values())

@app.post("/purchases", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def record_purchase(purchase_data: PurchaseCreate):
    if purchase_data.userId not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if purchase_data.songId not in songs_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    now = datetime.datetime.now(datetime.timezone.utc)
    new_purchase = PurchaseResponse(
        id=uuid4(),
        purchasedAt=now,
        **purchase_data.model_dump()
    )
    purchases_db[new_purchase.id] = new_purchase
    
    # Automatically grant entitlement upon purchase
    entitlement_key = f"{purchase_data.userId}-{purchase_data.songId}"
    if entitlement_key not in user_entitlements_db:
        new_entitlement = UserEntitlementResponse(
            userId=purchase_data.userId,
            songId=purchase_data.songId,
            source=EntitlementSource.purchase,
            grantedAt=now
        )
        user_entitlements_db[entitlement_key] = new_entitlement

    return new_purchase

@app.get("/purchases/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase_by_id(purchase_id: UUID):
    purchase = purchases_db.get(purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")
    return purchase

@app.put("/purchases/{purchase_id}", response_model=PurchaseResponse)
async def update_purchase(purchase_id: UUID, purchase_data: PurchaseUpdate):
    purchase = purchases_db.get(purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")

    update_data = purchase_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(purchase, key, value)
    purchases_db[purchase_id] = purchase
    return purchase

# --- Admin Routes ---
@app.get("/admins", response_model=List[AdminResponse])
async def get_all_admins():
    return list(admins_db.values())

@app.post("/admins", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(admin_data: AdminCreate):
    if admin_data.userId not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if user is already an admin
    if any(a.userId == admin_data.userId for a in admins_db.values()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has an admin role")

    now = datetime.datetime.now(datetime.timezone.utc)
    new_admin = AdminResponse(
        id=uuid4(), # Admin has its own ID separate from user_id
        grantedAt=now,
        **admin_data.model_dump()
    )
    admins_db[new_admin.id] = new_admin
    return new_admin

@app.get("/admins/{admin_id}", response_model=AdminResponse)
async def get_admin_by_id(admin_id: UUID):
    admin = admins_db.get(admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin entry not found")
    return admin

@app.put("/admins/{admin_id}", response_model=AdminResponse)
async def update_admin_role(admin_id: UUID, admin_data: AdminUpdate):
    admin = admins_db.get(admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin entry not found")
    
    if admin_data.role: # Only update if role is provided
        admin.role = admin_data.role
    admins_db[admin_id] = admin
    return admin

@app.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(admin_id: UUID):
    if admin_id not in admins_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin entry not found")
    del admins_db[admin_id]

# --- User Entitlement Routes (nested under User) ---
@app.get("/users/{user_id}/entitlements", response_model=List[UserEntitlementResponse])
async def get_user_entitlements(user_id: UUID):
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_entitlements = [
        ent for ent in user_entitlements_db.values() if ent.userId == user_id
    ]
    return user_entitlements

@app.post("/users/{user_id}/entitlements", response_model=UserEntitlementResponse, status_code=status.HTTP_201_CREATED)
async def grant_user_entitlement(user_id: UUID, entitlement_data: UserEntitlementCreate):
    if user_id != entitlement_data.userId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID in path does not match user ID in body")
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if entitlement_data.songId not in songs_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    entitlement_key = f"{user_id}-{entitlement_data.songId}"
    if entitlement_key in user_entitlements_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has this entitlement")

    now = datetime.datetime.now(datetime.timezone.utc)
    new_entitlement = UserEntitlementResponse(
        grantedAt=now,
        **entitlement_data.model_dump()
    )
    user_entitlements_db[entitlement_key] = new_entitlement
    return new_entitlement

# To run this file:
# 1. Save it as `app.py`.
# 2. Install FastAPI and Uvicorn: `pip install "fastapi[all]" uvicorn`
# 3. Run from your terminal: `uvicorn app:app --reload`
# 4. Access the API documentation at http://127.0.0.1:8000/docs
