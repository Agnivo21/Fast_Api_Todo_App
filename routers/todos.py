from fastapi import APIRouter,Depends,HTTPException,status,Path,Request
from ..models import Todos
from ..database import SessionLocal
from typing import Annotated
from pydantic import BaseModel,Field
from sqlalchemy.orm import session
from .auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates=Jinja2Templates(directory="project3todo/templates")

router = APIRouter(
    prefix='/todos',
    tags=['todos']
)


class Todorequest(BaseModel):
    title: str=Field(min_length=3)
    description: str= Field(min_length=3,max_length=100)
    priority: int=Field(gt=0)
    complete:bool


def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[session,Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

def redirect_to_login():
    redirect_response=RedirectResponse(url="/auth/login-page",status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response


###pages###
@router.get("/todo-page")
async def render_todo_page(request:Request,db:db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()
        
        todos = db.query(Todos).filter(Todos.owner_id==user.get("id"))

        return templates.TemplateResponse("todo.html",{"request":request,"todos":todos,"user":user})
    except:
        return redirect_to_login()

@router.get("/add-todo-page")
async def render_todo_page(request:Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        
        return templates.TemplateResponse("add-todo.html",{"request":request,"user":user})
    except:
        return redirect_to_login()
    
@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        todo = db.query(Todos).filter(Todos.id == todo_id).first()

        return templates.TemplateResponse(
            "edit-todo.html",
            {"request": request, "todo": todo, "user": user}
        )

    except:
        return redirect_to_login()

#### endpoints ###
@router.get("/")
async def read_all(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=404,detail="authentication failed")
    return db.query(Todos).filter(user.get('id')==Todos.owner_id).all() 

@router.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def getbyid(user:user_dependency,db:db_dependency,todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=404,detail="authentication failed")
    todosmodel=db.query(Todos).filter(Todos.id==todo_id).filter(user.get("id")==Todos.owner_id).first()
    if todosmodel is not None:
        return todosmodel
    raise HTTPException(status_code=404,detail="no todo match")

@router.post('/todo',status_code=status.HTTP_201_CREATED)
async def createtodos(user:user_dependency,db:db_dependency,todo_request:Todorequest):
    if user is None:
        raise HTTPException(status_code=404,detail="authentication failed")
    todo_model=Todos(**todo_request.model_dump(),owner_id=user.get("id"))
    db.add(todo_model)
    db.commit()

@router.put('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_todos(
    user:user_dependency,
    db: db_dependency,
    todo_request: Todorequest,
    todo_id: int = Path(gt=0)
):
    '''💡 FastAPI Tip Even though todo_id is a Path parameter, Python still treats Path(gt=0) as a default value, so the same rule applies.'''
    if user is None:
        raise HTTPException(status_code=404,detail="authentication failed")
    
    todosmodel=db.query(Todos).filter(Todos.id==todo_id).filter(user.get("id")==Todos.owner_id).first()
    if todosmodel is None:
        raise HTTPException(status_code=404,detail="no todo found")
    
    todosmodel.title=todo_request.title
    todosmodel.description=todo_request.description
    todosmodel.priority=todo_request.priority
    todosmodel.complete=todo_request.complete

    db.add(todosmodel)
    db.commit()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency,db: db_dependency, todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=404,detail="authentication failed")
    
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(user.get("id")==Todos.owner_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')

    db.query(Todos).filter(Todos.id == todo_id).filter(user.get("id")==Todos.owner_id).delete()

    db.commit()





