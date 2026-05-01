from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class StatusLead(enum.Enum):
    novo = "novo"
    em_atendimento = "em_atendimento"
    agendado = "agendado"
    convertido = "convertido"
    perdido = "perdido"


class Cliente(Base):
    """Clientes da agência (ex: Desentupidora do João)"""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    segmento = Column(String(100))        # ex: desentupidora, gasista
    cidade = Column(String(100))
    telefone = Column(String(20))
    email = Column(String(200))
    prompt_personalizado = Column(Text)   # personalidade do funcionário virtual
    criado_em = Column(DateTime, default=datetime.now)

    campanhas = relationship("Campanha", back_populates="cliente")
    leads = relationship("Lead", back_populates="cliente")


class Campanha(Base):
    """Campanhas Google Ads"""
    __tablename__ = "campanhas"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nome = Column(String(200))
    google_ads_id = Column(String(50))    # ID real no Google Ads
    orcamento_diario = Column(Float)
    status = Column(String(50))
    criado_em = Column(DateTime, default=datetime.now)

    cliente = relationship("Cliente", back_populates="campanhas")


class Lead(Base):
    """Leads recebidos nas landing pages"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nome = Column(String(200))
    telefone = Column(String(20))
    email = Column(String(200))
    mensagem = Column(Text)               # primeira mensagem do lead
    status = Column(Enum(StatusLead), default=StatusLead.novo)
    origem = Column(String(100))          # ex: google_ads, landing_page
    criado_em = Column(DateTime, default=datetime.now)

    cliente = relationship("Cliente", back_populates="leads")
    conversas = relationship("Conversa", back_populates="lead")


class Conversa(Base):
    """Histórico de conversa com cada lead"""
    __tablename__ = "conversas"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    remetente = Column(String(20))        # "lead" ou "agente"
    mensagem = Column(Text)
    criado_em = Column(DateTime, default=datetime.now)

    lead = relationship("Lead", back_populates="conversas")


def criar_tabelas():
    Base.metadata.create_all(engine)
    print("Banco de dados criado com sucesso.")


if __name__ == "__main__":
    criar_tabelas()
