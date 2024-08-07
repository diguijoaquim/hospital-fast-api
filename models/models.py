from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Instância Base para os modelos
Base = declarative_base()

# Modelo para usuário (login através de telefone e senha)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    contact = Column(String(30))
    password = Column(String(64))

# Modelo para férias usando Pydantic
class FeriaModel(BaseModel):
    funcionario_id: str
    data_inicio_ferias: datetime
    data_fim_ferias: datetime

class TransferenciaModal(BaseModel):
    funcionario_id: str
    data_transferido: datetime
    lugar_transferido: str

class ReformaModal(BaseModel):
    funcionario_id: str
    data_reforma: datetime
    idade_reforma: int


class FalecidoModal(BaseModel):
    funcionario_id: str
    data_falecimento: datetime
    idade: int

class SuspensoModal(BaseModel):
    funcionario_id: str
    data_suspenso: datetime
    motivo:str



# Modelo para Férias
class Feria(Base):
    __tablename__ = "ferias"
    id = Column(Integer, primary_key=True)
    funcionario_id = Column(Integer, ForeignKey('employers.id'), nullable=False)
    data_inicio_ferias = Column(DateTime, nullable=True)
    data_fim_ferias = Column(DateTime, nullable=True)
    employer = relationship("Employer", back_populates="ferias")

# Modelo para Transferência
class Transferencia(Base):
    __tablename__ = "transferencias"
    id = Column(Integer, primary_key=True)
    funcionario_id = Column(Integer, ForeignKey('employers.id'), nullable=False)
    data_transferido = Column(DateTime, nullable=True)
    lugar_transferido = Column(String(40), nullable=True)
    employer = relationship("Employer", back_populates="transferencias")

# Modelo para Reforma
class Reforma(Base):
    __tablename__ = "reformas"
    id = Column(Integer, primary_key=True)
    funcionario_id = Column(Integer, ForeignKey('employers.id'), nullable=False)
    data_reforma = Column(DateTime, nullable=True)
    idade_reforma = Column(Integer)
    employer = relationship("Employer", back_populates="reformas")

# Modelo para Falecido
class Falecido(Base):
    __tablename__ = "falecimentos"
    id = Column(Integer, primary_key=True)
    funcionario_id = Column(Integer, ForeignKey('employers.id'), nullable=False)
    data_falecimento = Column(DateTime, nullable=True)
    idade = Column(Integer)
    employer = relationship("Employer", back_populates="falecimentos")

# Modelo para Suspenso
class Suspenso(Base):
    __tablename__ = "suspensos"
    id = Column(Integer, primary_key=True)
    funcionario_id = Column(Integer, ForeignKey('employers.id'), nullable=False)
    data_suspenso = Column(DateTime, nullable=True)
    motivo = Column(String(50))
    employer = relationship("Employer", back_populates="suspensos")

# Modelo para Empregador
class Employer(Base):
    __tablename__ = "employers"
    id = Column(Integer, primary_key=True)
    nome = Column(String(50))
    apelido = Column(String(50))
    nascimento = Column(DateTime)
    bi = Column(String(50))
    provincia = Column(String(50))
    naturalidade = Column(String(50))
    residencia = Column(String(50))
    sexo = Column(String(50))
    inicio_funcoes = Column(DateTime)
    ano_inicio = Column(Integer, default=2020)
    sector = Column(String(200))
    reparticao = Column(String(100))
    especialidade = Column(String(100))
    categoria = Column(String(100))
    nuit = Column(String(50))
    status = Column(String(50), default="ACTIVO")
    careira = Column(String(200))
    faixa_etaria = Column(String(50)) 

    ferias = relationship("Feria", back_populates="employer")
    transferencias = relationship("Transferencia", back_populates="employer")
    reformas = relationship("Reforma", back_populates="employer")
    falecimentos = relationship("Falecido", back_populates="employer")
    suspensos = relationship("Suspenso", back_populates="employer")
    def em_ferias(self):
        if self.data_inicio_ferias and self.data_fim_ferias:
            return self.data_inicio_ferias <= datetime.utcnow() <= self.data_fim_ferias
        return False

    def calculate_days(self, status: str):
        if status == "APOSENTADO" and self.data_aposentadoria:
            return (datetime.utcnow() - self.data_aposentadoria).days
        elif status == "LICENCA" and self.data_licenca:
            return (datetime.utcnow() - self.data_licenca).days
        elif status == "DISPENSA" and self.data_dispensa:
            return (datetime.utcnow() - self.data_dispensa).days
        return 0

class EmployerCreate(BaseModel):
    nome: str
    apelido: str
    nascimento: datetime
    bi: str
    provincia: str
    naturalidade: str
    residencia: str
    sexo: str
    inicio_funcoes: datetime
    sector: str
    reparticao: str
    especialidade: str
    categoria: str
    nuit: str
    careira:str
    faixa_etaria:str

# Modelo Pydantic para atualização de empregador
class EmployerUpdate(BaseModel):
    nome: Optional[str]
    apelido: Optional[str]
    bi: Optional[str]
    provincia: Optional[str]
    naturalidade: Optional[str]
    residencia: Optional[str]
    sexo: Optional[str]
    sector: Optional[str]
    reparticao: Optional[str]
    especialidade: Optional[str]
    categoria: Optional[str]
    nuit: Optional[str]
    novo_local: Optional[str]  # Para Transferido
    data_transferencia: Optional[datetime]
    motivo_suspensao: Optional[str]  # Para Suspenso
    data_aposentadoria: Optional[datetime]  # Para Aposentado
    data_falecimento: Optional[datetime]  # Para Falecido
    faixa_etaria:Optional[str]

class EmployerUpdateStatus(BaseModel):
    status: str  # Novo status do funcionário, por exemplo, "Transferido", "Despedido", "Falecido"
    data_remocao: Optional[datetime] = None  # Data da remoção, pode ser opcional
    razao_remocao: Optional[str] = None  # Razão da remoção, pode ser opcional
    nova_localizacao: Optional[str] = None  # Nova localização se o funcionário for transferido, pode ser opcional

# Modelo Pydantic para criação de usuário
class UserCreate(BaseModel):
    name: str
    contact: str
    password: str