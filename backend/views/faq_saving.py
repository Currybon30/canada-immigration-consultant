from fastapi import APIRouter, Depends, Request, Body
from config.mypinecone import MyPinecone
from auth.admin_api_validation import validate_admin_api_key
from fastapi.responses import JSONResponse
from typing import List
from controllers.data_processing import convert_faq_to_langchain_docformat
from controllers.faq_kmeans import cluster_faqs_pipeline, get_total_unclustered_queries, delete_db

router = APIRouter(prefix="/api")

@router.post("/faqs/create-faq")
async def create_faq(request: Request, faq_docs: List[dict] = Body(...), mongo_db_faq_ids: List[str] = Body([]), index_name: str = Body('faqs'), x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        return JSONResponse({'error': 'Invalid API Key'}, status_code=401)
    token = request.cookies.get('access_token')
    if not token:
        return JSONResponse({'error': 'Invalid Token'}, status_code=401)
    try:
        langchain_faq_docs = convert_faq_to_langchain_docformat(faq_docs)
        pinecone = MyPinecone()
        response = pinecone.insert_data(index_name, langchain_faq_docs)
        if mongo_db_faq_ids:
            await delete_db(mongo_db_faq_ids)
        return response
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
    
@router.get("/faqs/total-number-unclustered-queries")
async def get_unclustered_faqs(request: Request, category: str = None, x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        return JSONResponse({'error': 'Invalid API Key'}, status_code=401)
    token = request.cookies.get('access_token')
    if not token:
        return JSONResponse({'error': 'Invalid Token'}, status_code=401)
    try:
        if not category:
            return JSONResponse({'error': 'Category is required'}, status_code=400)
        total_unclustered_queries = await get_total_unclustered_queries(category)
        return {"total_unclustered_queries": total_unclustered_queries}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
    
@router.get("/faqs/kmeans-cluster")
async def kmeans_cluster_faqs(request: Request, category: str = None, x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        return JSONResponse({'error': 'Invalid API Key'}, status_code=401)
    token = request.cookies.get('access_token')
    if not token:
        return JSONResponse({'error': 'Invalid Token'}, status_code=401)
    try:
        pending_new_faqs = await cluster_faqs_pipeline(category)
        if isinstance(pending_new_faqs, dict):
            pending_new_faqs = [pending_new_faqs]
            return JSONResponse({'pending_new_faqs': pending_new_faqs}, status_code=200)
        else:
            return JSONResponse({'error': 'No new FAQs found'}, status_code=404)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)