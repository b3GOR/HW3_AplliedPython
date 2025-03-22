from fastapi import APIRouter,Query
from functions import generate_short_link, post_db
router = APIRouter()


@router.get('/')
async def Hello():
    return {'Hello world'}


@router.post('/links/shorten')
async def links_shorten(link: str = Query(..., description="The long URL to shorten")):
    long,short=generate_short_link(link)
    post_db(long,short)
    return {"long_link": long, "short_link": short}  

@router.get('links/{short_code}')
async def post_short_code(short_code):
    pass

@router.delete('links/{short_code}')
async def delete_short_code(short_code):
    pass
@router.put('links/{short_code}')
async def put_short_code(short_code):
    pass
@router.get('/links/{short_code}/stats')
async def link_stats(short_code):
    pass
