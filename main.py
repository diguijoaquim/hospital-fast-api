from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
import re
from models.models import * 
import uvicorn
from sqlalchemy.orm import sessionmaker
from controler import *
import os


from groq import Groq
# Inicializar a aplicação FastAPI
app = FastAPI()

# Configurações de segurança e criptografia
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1036800

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Validação de usuário
def authenticate_user(db, contact: str, password: str):
    user = db.query(User).filter(User.contact == contact).first()
    if not user or user.password != password:
        return False
    return user

def validate_contact(contact: str):
    if not re.match(r'^(87|86|84|85|82|83)\d{7}$', contact):
        raise HTTPException(status_code=400, detail="Número inválido. Deve começar com 87, 86, 84, 85, 82, ou 83 e ter 9 dígitos.")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Rota para login e geração de token
@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect contact or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.contact}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Dependência para obter o usuário atual a partir do token
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        contact: str = payload.get("sub")
        if contact is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.contact == contact).first()
    if user is None:
        raise credentials_exception
    return user

# Exemplo de rota protegida que requer autenticação
@app.get("/users/me", response_model=dict)
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.name, "contact": current_user.contact}

@app.post("/users/")
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    validate_contact(user.contact)
    new_user = User(
        name=user.name,
        contact=user.contact,
        password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Rota para adicionar um funcionário
@app.post("/employers/")
def add_employer(employer: EmployerCreate, db: Session = Depends(get_db)):
    new_employer = Employer(
        nome=employer.nome,
        apelido=employer.apelido,
        nascimento=employer.nascimento,
        bi=employer.bi,
        provincia=employer.provincia,
        naturalidade=employer.naturalidade,
        residencia=employer.residencia,
        sexo=employer.sexo,
        inicio_funcoes=employer.inicio_funcoes,
        sector=employer.sector,
        reparticao=employer.reparticao,
        especialidade=employer.especialidade,
        categoria=employer.categoria,
        nuit=employer.nuit,
        careira=employer.careira,
        faixa_etaria=employer.faixa_etaria
    )
    db.add(new_employer)
    db.commit()
    db.refresh(new_employer)
    return new_employer

# Rotas FastAPI
@app.post('/add_ferias')
def feria(feria: FeriaModel):
    try:
        f = addFerias(id=feria.funcionario_id, start=feria.data_inicio_ferias, end=feria.data_fim_ferias)
        return f
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Erro ao adicionar férias: {e.detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")


@app.post('/add_transferencia')
def trasferido(transferencia: TransferenciaModal):
    try:
        f = addTransferencia(id=transferencia.funcionario_id, start=transferencia.data_transferido, lugar=transferencia.lugar_transferido)
        return f
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Erro ao adicionar trasferencia: {e.detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

@app.post('/add_reforma')
def reforma(reforma: ReformaModal):
    try:
        r = addReforma(id=reforma.funcionario_id, data=reforma.data_reforma, idade=reforma.idade_reforma)
        return r
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Erro ao adicionar reforma: {e.detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

@app.post('/add_suspenso')
def suspenso(suspenso: SuspensoModal):
    try:
        s = addSuspenso(id=suspenso.funcionario_id, data=suspenso.data_suspenso, motivo=suspenso.motivo)
        return s
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Erro ao adicionar suspenso: {e.detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

@app.post('/add_falecido')
def falecido(falecido: FalecidoModal):
    try:
        return addFalecido(id=falecido.funcionario_id, data=falecido.data_falecimento, idade=falecido.idade)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Erro ao adicionar falecido: {e.detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

@app.get('/trasferido')
def get_trasferido():
    return getTransferencia()


@app.get('/suspenso')
def get_suspenso():
    return getSuspenso()

@app.get('/falecido')
def get_falecido():
    return getFalecido()

@app.get('/ferias/')
def get_ferias(search=""):
    return getFerias(search)


@app.get("/removido/")
def remov(search: str = None, db: Session = Depends(get_db)):
    return getEmployersRemovido()



@app.get("/emp/transferidos")
def tras(search: str = None, db: Session = Depends(get_db)):
    return getEmployersTransferido()

@app.get("/emp/licencas")
def lice(search: str = None, db: Session = Depends(get_db)):
    return getEmployersLICENCA(search)

@app.get("/emp/suspensos")
def susp(search: str = None, db: Session = Depends(get_db)):
    return getEmployersSuspensed()




@app.get("/emp/reformados")
def refo(search: str = None, db: Session = Depends(get_db)):
    return getEmployersReforma()

@app.get("/emp/falecidos")
def fal(search: str = None, db: Session = Depends(get_db)):
    return getEmployersDeath()

@app.get("/employers/")
def funcionarios(search: str = None, db: Session = Depends(get_db)):
    return getEmployers()

@app.get("/employers/passados")
def funcionarios_passados(search: str = None, db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(
    or_(
        
        Employer.status == "TRASFERIDO",
        Employer.status == "SUSPENSO",
        Employer.status == "FALECIDO",
        
    )
).all()
    return employers

@app.get("/employer/{id}")
def funcionarios(id:int, db: Session = Depends(get_db)):
    return getById(id)

#ROTAS PARA ESTATUS
@app.post("/users/")
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    validate_contact(user.contact)
    new_user = User(
        name=user.name,
        contact=user.contact,
        password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Rota para listar funcionários por setor
@app.get("/employers/sector/{sector}")
def read_employers_by_sector(sector: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.sector == sector).all()


@app.get('/getbysearch/')
def searcher(name:str,db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.nome.like(f'%{name}%')).all()

@app.get("/employers/sectors")
def read_employers_by_sectors():
    
    return getLen()



# Rota para listar funcionários por naturalidade
@app.get("/employers/naturality/{naturality}")
def read_employers_by_naturality(naturality: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.naturalidade == naturality).all()

# Rota para listar funcionários por província
@app.get("/employers/province/{province}")
def read_employers_by_province(province: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.provincia == province).all()

# Rota para listar funcionários por nome
@app.get("/employers/name/{name}")
def read_employers_by_name(name: str, surename: str = None, db: Session = Depends(get_db)):
    if surename:
        return db.query(Employer).filter_by(nome=name, apelido=surename).all()
    else:
        return db.query(Employer).filter_by(nome=name).all()

# Rota para listar funcionários por gênero
@app.get("/employers/genre/{genre}")
def read_employers_by_genre(genre: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.sexo == genre).all()

# Rota para listar funcionários por ano de início
@app.get("/employers/year/{year}")
def read_employers_by_year(year: int, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.ano_inicio == year).all()




@app.put("/employer/{employer_id}")
def update_employer(employer_id: int, employer_update: EmployerUpdate, db: Session = Depends(get_db)):
    # Recupera o empregador com base no ID
    employer = db.query(Employer).filter(Employer.id == employer_id).first()
    
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    # Atualiza os campos conforme fornecido no payload
    update_data = employer_update.dict(exclude_unset=True)  # Exclui campos que não foram fornecidos
    
    for key, value in update_data.items():
        setattr(employer, key, value)  # Define os novos valores
    
    db.commit()
    db.refresh(employer)  # Atualiza o objeto com os dados mais recentes do banco
    
    return employer




# Rota para deletar um funcionário
@app.delete("/employers/{id_employer}")
def delete_employer(id_employer: int, db: Session = Depends(get_db)):
    employer = db.query(Employer).filter(Employer.id == id_employer).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    employer.status = "Removido"
    employer.data_remocao = datetime.utcnow()
    db.commit()
    return {"message": "Employer status updated to 'Removido'"}

client = Groq(api_key=os.getenv("API_KEY"))

# Classe para a entrada de texto
class TextInput(BaseModel):
    text: str

def employer_to_dict(employer):
    # Converte o objeto Employer para um dicionário, excluindo atributos não serializáveis
    return {
        "id": employer.id,
        "nome": employer.nome,
        "apelido": employer.apelido,
        "nascimento": employer.nascimento.isoformat() if employer.nascimento else None,
        "bi": employer.bi,
        "provincia": employer.provincia,
        "naturalidade": employer.naturalidade,
        "residencia": employer.residencia,
        "sexo": employer.sexo,
        "inicio_funcoes": employer.inicio_funcoes.isoformat() if employer.inicio_funcoes else None,
        "ano_inicio": employer.ano_inicio,
        "careira": employer.careira,
        "sector": employer.sector,
        "reparticao": employer.reparticao,
        "categoria": employer.categoria,
        "especialidade":employer.especialidade,
        "nuit":employer.nuit,
        "faixa_etaria":employer.faixa_etaria,
        "status":employer.status

    }

message_history = []

@app.post('/dina')
def dina(text_input: TextInput, db: Session = Depends(get_db)):
    users = db.query(Employer).all()
    text = text_input.text
    
    # Converte os objetos Employer para um formato serializável
    treino_dina = f"""
    Ola eu sou assistente IA criado e integrado no sistema de gestao de recursos humanos do hospital de lichinga, fui criada pela a BlueSpark
    
    {treino_ai}
    
    Dados do hospital:
    {[employer_to_dict(user) for user in users]}


    """

    # Adiciona a mensagem do sistema ao histórico, se for a primeira interação
    if not message_history:
        message_history.append({"role": "system", "content": treino_dina})

    # Adiciona a mensagem do usuário ao histórico
    message_history.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        messages=message_history,
        model="llama3-70b-8192",
    )
    return response.choices[0].message.content






# Rodar o servidor com Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.62", port=8000)
