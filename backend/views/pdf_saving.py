import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.getcwd(), 'immigration-consultant-capstone'))


from fastapi import File, UploadFile, Form, APIRouter, Depends, Body, Request
from config.mypinecone import MyPinecone
from fastapi.responses import JSONResponse
from typing import List
from controllers.data_processing import data_preprocessing, convert_to_langchain_docformat
from auth.admin_api_validation import validate_admin_api_key
import dotenv
dotenv.load_dotenv()

router = APIRouter(prefix="/api")
admin_api_key = os.getenv('ADMIN_API_KEY')


# Function to receive PDF file
# Function to return the processed text to check before saving

@router.post("/upload-pdf")
async def upload_pdf(request: Request, pdf_file: UploadFile = File(...), skip_tags: List[str] = Form([]), category: List[str] = Form([]), txt_removed: List[str] = Form([]), update_pdf_id: str = Form(None), x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        return JSONResponse({'error': 'Invalid API Key'}, status_code=401)

    token = request.cookies.get('access_token')
    if not token:
        return JSONResponse({'error': 'Invalid Token'}, status_code=401)
    
    else:
        file_name = pdf_file.filename
        
        if update_pdf_id is not None:
            update_pdf_id = update_pdf_id.strip()
            pinecone = MyPinecone()
            pinecone.delete_data_by_ofc_doc_id('studypermit-pgwp-visa', update_pdf_id)
            
        
        temp_pdf_path = f'{file_name}.pdf'
        with open(temp_pdf_path, 'wb') as f:
            f.write(await pdf_file.read())
            
        docs = data_preprocessing(temp_pdf_path, skip_tags=skip_tags, category=category, txt_removed=txt_removed)
        
        os.remove(temp_pdf_path)
        
        return JSONResponse({'message': f'File {file_name} uploaded successfully', 'docs': docs}, status_code=201)  
    
    
@router.post("/save-pdf-to-pinecone")
def save_pdf_to_pinecone(request: Request, docs: List[dict] = Body(...), ofc_doc_id: str = Body(...), x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        return JSONResponse({'error': 'Invalid API Key'}, status_code=401)
    token = request.cookies.get('access_token')
    if not token:
        return JSONResponse({'error': 'Invalid Token'}, status_code=401)
    else:
        try:
            final_docs = convert_to_langchain_docformat(docs, ofc_doc_id)
            pinecone = MyPinecone()
            index_name = 'studypermit-pgwp-visa'
            pinecone.insert_data(index_name, final_docs)
            return JSONResponse({'message': f'{ofc_doc_id} saved successfully'}, status_code=201)
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)