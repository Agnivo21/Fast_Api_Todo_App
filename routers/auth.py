from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from typing import Annotated
from models import Users
from passlib.context import CryptContext
from database import SessionLocal
from sqlalchemy.orm import session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from datetime import timedelta,datetime,timezone
from starlette import status
from jose import jwt,JWTError
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth",
    tags=['auth']
)

bcrypt_context=CryptContext(schemes=['bcrypt'],deprecated='auto')


SECRET_KEY = "2d026f2dce31ee415b27107f2a9ee8f0bb3aa338f8c029b614fc35fc9745246a"
ALGORITHM='HS256'

oauth2_bearer=OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    email : str
    username : str
    first_name : str
    last_name : str
    password : str
    role : str
    phone_number:str

class Token(BaseModel):
    access_token:str
    token_type:str


def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[session,Depends(get_db)]

def authenticate_user(username,password,db):
    user = db.query(Users).filter(username==Users.username).first()
    if user is None:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

def create_access_token(username: str,user_id :int,role:str,expires_delta:timedelta):
    encode={'sub':username,'id':user_id,'role':role}
    expires=datetime.now(timezone.utc)+expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token:Annotated[str,Depends(oauth2_bearer)]):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str=payload.get('sub')
        user_id:int=payload.get('id')
        user_role:str=payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=
                                'could not validate user')
        return {'username':username,'id':user_id,'user_role':user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=
                                'could not validate user')




templates=Jinja2Templates(directory="project3todo/templates")

###templates####

@router.get("/login-page")
def render_login_page(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})

@router.get("/register-page")
def render_register_page(request:Request):
    return templates.TemplateResponse("register.html",{"request":request})

####endpoints#####
@router.post("/")
def create_user(db: db_dependency,createuserrequest:CreateUserRequest):
    create_user_model=Users(
        email = createuserrequest.email,
        username = createuserrequest.username,
        first_name = createuserrequest.first_name,
        last_name = createuserrequest.last_name,
        hashed_password = bcrypt_context.hash(createuserrequest.password),
        role = createuserrequest.role,
        is_active=True,
        phone_number=createuserrequest.phone_number
    )
    db.add(create_user_model)
    db.commit()

@router.post("/token",response_model=Token)
def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],
                           db:db_dependency):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Failed Authentication"
        )
    token= create_access_token(user.username,user.id,user.role,timedelta(minutes=20))
    return {'access_token':token,'token_type':'bearer'}