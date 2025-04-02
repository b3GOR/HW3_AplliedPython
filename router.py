from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
from fastapi import Depends, HTTPException,status, Query, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

import psycopg2
from sqlalchemy import select
from sqlalchemy.orm import Session



from db import LinkDB, LinkStatsDB, UserDB
from functions import authenticate_user, delete_cache_link, update_access_count, cache_link,get_cached_link, create_access_token, generate_short_link,   get_current_active_user, get_db, get_password_hash 
from config import DOMAIN
from validation import LinkRequest, LinkResponse, LinkStats, LinkUpdate, Token, User, UserCreate
 

router = APIRouter()



@router.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user_email = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user_username = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = UserDB(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: UserDB = Depends(get_current_active_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user

@router.post('/links/shorten', response_model=LinkResponse)
async def links_shorten(
    link_data: LinkRequest, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        if link_data.alias:
            existing_link = db.query(LinkDB).filter(LinkDB.short_code == link_data.alias).first()
            if existing_link:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom alias already exists"
                )
        
        # Создаем новую ссылку
        if link_data.alias is None:
            long_link, short_code = generate_short_link(link_data.long_link)
        else:
            long_link, short_code = link_data.long_link, link_data.alias
        
        # Создаем новую запись в БД
        new_link = LinkDB(
            short_code=short_code,
            original_url=long_link,
            expires_at=link_data.expires_at.astimezone(timezone.utc) if link_data.expires_at is not None else None,
            user_id=current_user.id if current_user else None
        )
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        
        # Создаем статистику для новой ссылки
        stats = LinkStatsDB(short_link=short_code)
        db.add(stats)
        db.commit()

        cache_link(short_code,long_link,0)

 
        

        

        return {"long_link": long_link, "short_link": f'https://{DOMAIN}/{short_code}'}
        
    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/links/{short_code}')
async def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    cached = get_cached_link(short_code)
    if cached:
        stats = db.query(LinkStatsDB).filter(LinkStatsDB.short_link == short_code).first()
        if stats:
            stats.access_count += 1
            stats.last_access = datetime.now(timezone.utc)
            db.commit()
            update_access_count(short_code)
        return RedirectResponse(url=cached)
    else:
        link = db.query(LinkDB).filter(LinkDB.short_code == short_code).first()
        if not link:
            raise HTTPException(status_code=404, detail="Short link not found")
    
        if link.expires_at and link.expires_at < datetime.now(timezone.utc):
            db.delete(link)
            raise HTTPException(status_code=404, detail="Link has expired")
        
        stats = db.query(LinkStatsDB).filter(LinkStatsDB.short_link == short_code).first()
        if stats:
            stats.access_count += 1
            stats.last_access = datetime.now(timezone.utc)
            db.commit()
            update_access_count(short_code)
        
        return RedirectResponse(url=link.original_url)

        

@router.delete('/links/{short_code}')
async def delete_link(
    short_code: str, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to delete links"
        )
    
    link = db.query(LinkDB).filter(LinkDB.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    if link.user_id and link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this link"
        )
    

    
    db.delete(link)
    db.commit()
    delete_cache_link(short_code)
    
    return {"message": "Link successfully deleted"}

@router.put('/links/{old_short_code}')
async def update_short_code(
    old_short_code: str,
    link_data: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        link = db.query(LinkDB).filter(LinkDB.short_code == old_short_code).first()
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        if link.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        if db.query(LinkDB).filter(LinkDB.short_code == link_data.new_short_code).first():
            raise HTTPException(status_code=400, detail="Short code already exists")

        stats = db.query(LinkStatsDB).filter(LinkStatsDB.short_link == old_short_code).first()
        

        if stats:
            db.delete(stats)
            db.flush()  

        link.short_code = link_data.new_short_code
        db.add(link)
        
        if stats:
            new_stats = LinkStatsDB(
                short_link=link_data.new_short_code,
                access_count=stats.access_count,
                last_access=stats.last_access
            )
            db.add(new_stats)
        
        db.commit()

        delete_cache_link(old_short_code)
        cache_link(link_data.new_short_code, link.original_url)

        return {
            "message": "Short code updated successfully",
            'old_short_url': f"https://{DOMAIN}/{old_short_code}",
            "new_short_url": f"https://{DOMAIN}/{link_data.new_short_code}"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
@router.get('/links/{short_code}/stats', response_model=LinkStats)
async def get_link_stats(short_code: str, db: Session = Depends(get_db)):

    link = db.query(LinkDB).filter(LinkDB.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    stats = db.query(LinkStatsDB).filter(LinkStatsDB.short_link == short_code).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Statistics not found for this link")
    
    result = {
        "original_url": link.original_url,
        "created_at": link.created_at,
        "access_count": stats.access_count,
        "last_access": stats.last_access,
        "expires_at": link.expires_at
    }
    
    
    return result

# @router.get('/links/search')
# async def search_by_original_url(
#     original_url: str = Query(..., description="Original URL to search for"),
#     db: Session = Depends(get_db)
# ):
#     query = db.execute(select(LinkDB).filter_by(original_url==original_url))
#     result=query.all()
#     return {'message': result}
