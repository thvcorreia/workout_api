from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi_pagination import Page, pagination_params
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate
from typing import List, Optional, Annotated
from workout_api.categorias.schemas import CategoriaIn
from workout_api.centro_treinamento.schemas import CentroTreinamentoAtleta
from workout_api.contrib.schemas import BaseSchema, OutMixin
from workout_api.database import get_db
from workout_api.models import Atleta  # Supondo que você tenha um modelo Atleta

app = FastAPI()

class Atleta(BaseSchema):
    nome: Annotated[str, Field(description='Nome do atleta', example='Joao', max_length=50)]
    cpf: Annotated[str, Field(description='CPF do atleta', example='12345678900', max_length=11)]
    idade: Annotated[int, Field(description='Idade do atleta', example=25)]
    peso: Annotated[PositiveFloat, Field(description='Peso do atleta', example=75.5)]
    altura: Annotated[PositiveFloat, Field(description='Altura do atleta', example=1.70)]
    sexo: Annotated[str, Field(description='Sexo do atleta', example='M', max_length=1)]
    categoria: Annotated[CategoriaIn, Field(description='Categoria do atleta')]
    centro_treinamento: Annotated[CentroTreinamentoAtleta, Field(description='Centro de treinamento do atleta')]

class AtletaIn(Atleta):
    pass

class AtletaOut(Atleta, OutMixin):
    pass

class AtletaUpdate(BaseSchema):
    nome: Annotated[Optional[str], Field(None, description='Nome do atleta', example='Joao', max_length=50)]
    idade: Annotated[Optional[int], Field(None, description='Idade do atleta', example=25)]

@app.exception_handler(IntegrityError)
def integrity_error_handler(request, exc):
    detail = f"Já existe um atleta cadastrado com o cpf: {exc.params['cpf']}"
    raise HTTPException(status_code=303, detail=detail)

@app.get("/atletas/", response_model=Page[AtletaOut], dependencies=[Depends(pagination_params)])
def get_atletas(db: Session = Depends(get_db), nome: Optional[str] = Query(None), cpf: Optional[str] = Query(None)):
    query = db.query(Atleta)
    
    if nome:
        query = query.filter(Atleta.nome.ilike(f"%{nome}%"))
    
    if cpf:
        query = query.filter(Atleta.cpf == cpf)
    
    return sqlalchemy_paginate(query)

# Exemplo de função para criar um novo atleta
@app.post("/atletas/", response_model=AtletaOut)
def create_atleta(atleta: AtletaIn, db: Session = Depends(get_db)):
    db_atleta = Atleta(**atleta.dict())
    try:
        db.add(db_atleta)
        db.commit()
        db.refresh(db_atleta)
    except IntegrityError as e:
        raise integrity_error_handler(None, e)
    return db_atleta
