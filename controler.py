from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from models.models import Base, Employer, Feria, Transferencia, Reforma, Suspenso, Falecido

# Configurar a conexão com o banco de dados

engine = create_engine('sqlite:///database/hospital.db', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar as tabelas do banco de dados se não existirem
def create_base():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def getEmployerByReparticao(reparticao):
    """Retorna a lista de empregados filtrados pela repartição"""
    with SessionLocal() as db:
        return db.query(Employer).filter_by(reparticao=reparticao).all()

def getEmployerBySector(sector):
    """Retorna a lista de empregados filtrados pelo setor"""
    with SessionLocal() as db:
        return db.query(Employer).filter_by(sector=sector).all()

def getById(id):
    """Retorna um empregado com base no ID"""
    with SessionLocal() as db:
        return db.query(Employer).filter_by(id=id).first()

def getLen():
    """Retorna o número de empregados em setores específicos"""
    setores = ["Maternidade", "Laboratório", "Psiquiatria", "Medicina 1"]
    contagem = {}
    with SessionLocal() as db:
        for setor in setores:
            contagem[setor] = db.query(Employer).filter_by(sector=setor).count()
    return contagem

STATUS_TRANSITIONS = {
    "ACTIVO": ["LICENCA", "TRANSFERIDO", "APOSENTADO", "SUSPENSO", "FALECIDO"],
    "LICENCA": ["ACTIVO", "FALECIDO", "TRANSFERIDO"],
    "TRANSFERIDO": ["ACTIVO"],
    "APOSENTADO": [],
    "SUSPENSO": ["ACTIVO"],
    "FALECIDO": [],
    "Removido":["ACTIVO"]

}

def is_valid_transition(current_status, new_status):
    """ Verifica se a transição de status é válida """
    return new_status in STATUS_TRANSITIONS.get(current_status, [])

def update_status(funcionario, new_status):
    """ Atualiza o status do funcionário se a transição for válida """
    if is_valid_transition(funcionario.status, new_status):
        funcionario.status = new_status
    else:
        raise ValueError(f"Transição de status inválida: {funcionario.status} -> {new_status}")

def addFerias(id, start=datetime.now(), end=datetime.now()):
    try:
        with SessionLocal() as db:
            nova_feria = Feria(
                funcionario_id=id,
                data_inicio_ferias=start,
                data_fim_ferias=end
            )
            funcionario = db.query(Employer).filter_by(id=id).first()
            update_status(funcionario, "LICENCA")
            db.add(nova_feria)
            db.commit()
            return nova_feria
    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"Database error occurred: {str(e)}")
        raise

def addTransferencia(id, start=datetime.now(), lugar=""):
    try:
        with SessionLocal() as db:
            transferencia = Transferencia(
                funcionario_id=id,
                data_transferido=start,
                lugar_transferido=lugar
            )
            funcionario = db.query(Employer).filter_by(id=id).first()
            update_status(funcionario, "TRANSFERIDO")
            db.add(transferencia)
            db.commit()
            return transferencia
    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"Database error occurred: {str(e)}")
        raise

def addReforma(id, data, idade):
    try:
        with SessionLocal() as db:
            reforma = Reforma(
                funcionario_id=id,
                data_reforma=data,
                idade_reforma=idade
            )
            funcionario = db.query(Employer).filter_by(id=id).first()
            update_status(funcionario, "APOSENTADO")
            db.add(reforma)
            db.commit()
            return reforma
    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"Database error occurred: {str(e)}")
        raise

def addSuspenso(id, data=datetime.now(), motivo=""):
    try:
        with SessionLocal() as db:
            suspenso = Suspenso(
                funcionario_id=id,
                data_suspenso=data,
                motivo=motivo
            )
            funcionario = db.query(Employer).filter_by(id=id).first()
            update_status(funcionario, "SUSPENSO")
            db.add(suspenso)
            db.commit()
            return suspenso
    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"Database error occurred: {str(e)}")
        raise

def addFalecido(id, data, idade):
    try:
        with SessionLocal() as db:
            falecido = Falecido(
                funcionario_id=id,
                data_falecimento=data,
                idade=idade
            )
            funcionario = db.query(Employer).filter_by(id=id).first()
            update_status(funcionario, "FALECIDO")
            db.add(falecido)
            db.commit()
            return falecido
    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        print(f"Database error occurred: {str(e)}")
        raise

def getTransferencia():
    with SessionLocal() as db:
        return db.query(Transferencia).join(Employer).all()

def getSuspenso():
    with SessionLocal() as db:
        return db.query(Suspenso).join(Employer).all()

def getReforma():
    with SessionLocal() as db:
        return db.query(Reforma).join(Employer).all()

def getFalecido():
    with SessionLocal() as db:
        return db.query(Falecido).join(Employer).all()

def getFerias(search=None):
    with SessionLocal() as db:
        ferias=[]
        if search!=None:
            f=db.query(Feria).filter(Feria.data_inicio_ferias.like(f'%{search}%'))
        else:
            f=db.query(Feria).all()
        
        for feria in f:
            funcionario=db.query(Employer).filter_by(id=feria.funcionario_id).first()
            ferias.append({"nome":funcionario.nome+" "+funcionario.apelido,'data_inicio_ferias':feria.data_inicio_ferias,"data_fim_ferias":feria.data_fim_ferias})
        return ferias

def getEmployersRemovido():
    try:
        with SessionLocal() as db:
            employers = db.query(Employer).outerjoin(Feria).outerjoin(Transferencia).filter(
                Employer.status == "Removido"
            ).options(
                joinedload(Employer.ferias),
                joinedload(Employer.transferencias)  # Carregar dados de transferência
            ).all()
            return employers
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def getEmployersDeath():
    try:
        with SessionLocal() as db:
            employers = db.query(Employer).outerjoin(Falecido).filter(
                Employer.status == "FALECIDO"
            ).options(joinedload(Employer.ferias)).all()
            return employers
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def getEmployersLICENCA(seaarch=None):
    try:
        with SessionLocal() as db:
            if seaarch ==None:

                employers = db.query(Employer).outerjoin(Feria).outerjoin(Transferencia).filter(
                    Employer.status == "LICENCA"
                ).options(joinedload(Employer.ferias)).all()
            else:
                employers = db.query(Employer).outerjoin(Feria).outerjoin(Transferencia).filter(
                    Employer.status == "LICENCA"
                ).options(joinedload(Employer.ferias)).filter(Employer.nome.like(f"%{seaarch}%")).all()
            return employers
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def getEmployersTransferido():
    try:
        with SessionLocal() as db:
            employers = db.query(Employer).outerjoin(Transferencia).filter(
                Employer.status == "TRANSFERIDO"
            ).options(
                joinedload(Employer.ferias),
                joinedload(Employer.transferencias)  # Carregar dados de transferência
            ).all()
            return employers
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def getEmployersReforma():
    try:
        with SessionLocal() as db:
            employers = db.query(Employer).outerjoin(Reforma).filter(
                Employer.status == "APOSENTADO"
            ).options(joinedload(Employer.ferias)).all()
            return employers
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def getEmployersSuspensed():
    try:
        with SessionLocal() as db:
            employers = db.query(Employer).outerjoin(Suspenso).filter(
                Employer.status == "SUSPENSO"
            ).options(joinedload(Employer.ferias)).all()
            return employers
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def getEmployers():
    try:
        with SessionLocal() as db:
            employers = db.query(Employer).outerjoin(Feria).outerjoin(Transferencia).filter(
                or_(
                    Employer.status == "ACTIVO",
                    Employer.status == "DISPENSA",
                    Employer.status == "LICENCA"
                )
            ).options(joinedload(Employer.ferias)).all()
            return employers
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error occurred: {str(e)}")
        raise






def getEmployerssearche():
    try:
        with SessionLocal() as db:
            employers = db.query(Employer).outerjoin(Feria).outerjoin(Transferencia).filter(
                or_(
                    
                    Employer.status == "LICENCA"
                )
            ).options(joinedload(Employer.ferias)).all()
            return employers
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error occurred: {str(e)}")
        raise







def treino_ai():
    text='''

    ao mencionar dados nao posso retornar em json nao , deve ser dados claros, sempre ignorar o id do funcionario nao pode ser retornado

    Criado pela Electro Gulamo , 
    os principais programadores, Diqui Joaquim, Jorge Sebastiao , Zelote francisco e Alvarinho Luis, esses pertencen na equipe BlueSpark da ElectroGulamo
    
    Hospital de lichinga:

    Hospital Provincial de Lichinga: Informação Atualizada (8 de Julho de 2024)
    O Hospital Provincial de Lichinga, na província de Niassa, Moçambique, foi recentemente inaugurado após extensas obras de reabilitação, ampliação e requalificação.
    Serviços Disponíveis:
    Serviços de Urgência: Atendimento médico imediato para casos graves.
    Maternidade: Cuidados de saúde pré, durante e pós-parto para mães e recém-nascidos.
    Bloco Operatório: Realização de cirurgias de diversas especialidades.
    Consulta Externa: Consultas médicas em diversas áreas da medicina.
    Fisioterapia: Reabilitação física para pacientes com diversos tipos de lesões.
    Pediatria: Cuidados de saúde para crianças.
    Tomografia TAC: Exames de imagem avançados para diagnóstico de doenças.
    Produção e Canalização de Oxigénio: Garantia de oxigénio para pacientes que necessitem.
    Outras Informações:

    Localização: Lichinga, Niassa, Moçambique.

'''
    return text
