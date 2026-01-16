from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DECIMAL, Text, LargeBinary, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class StatusIA(str, enum.Enum):
    validated = "validated"
    math_error = "math_error"
    pending = "pending"

class EstudioContable(Base):
    __tablename__ = "estudios_contables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_estudio = Column(String(255))
    uuid_estudio = Column(String(100), unique=True)

    clientes = relationship("Cliente", back_populates="estudio")

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    estudio_id = Column(Integer, ForeignKey("estudios_contables.id"), nullable=True)
    razon_social = Column(String(255))
    uuid_cliente = Column(String(100), unique=True)
    config_modulos = Column(JSON)

    estudio = relationship("EstudioContable", back_populates="clientes")
    conexion = relationship("ClienteConexion", back_populates="cliente", uselist=False)
    comprobantes = relationship("Comprobante", back_populates="cliente")

class ClienteConexion(Base):
    __tablename__ = "cliente_conexiones"

    cliente_id = Column(Integer, ForeignKey("clientes.id"), primary_key=True)
    azure_endpoint = Column(String(255))
    azure_key = Column(String(255))
    whatsapp_api_key = Column(String(255))
    consumo_mes_actual = Column(Integer, default=0)

    cliente = relationship("Cliente", back_populates="conexion")

class Comprobante(Base):
    __tablename__ = "comprobantes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clientes.id"))
    total_amount = Column(DECIMAL(15, 2))
    file_hash = Column(String(64), unique=True)
    status_ia = Column(SQLEnum(StatusIA))

    cliente = relationship("Cliente", back_populates="comprobantes")
    ivas = relationship("ComprobanteIVA", back_populates="comprobante")
    items = relationship("ComprobanteItem", back_populates="comprobante")

class ComprobanteIVA(Base):
    __tablename__ = "comprobantes_iva"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id"))
    tax_base = Column(DECIMAL(15, 2))
    tax_percentage = Column(DECIMAL(5, 2))
    tax_amount = Column(DECIMAL(15, 2))

    comprobante = relationship("Comprobante", back_populates="ivas")

class ComprobanteItem(Base):
    __tablename__ = "comprobante_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id"))
    description = Column(Text)
    unit_price = Column(DECIMAL(15, 2))
    embedding_vector = Column(LargeBinary)

    comprobante = relationship("Comprobante", back_populates="items")
