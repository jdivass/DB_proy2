from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional

class ProductCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    stock_actual: int = Field(..., ge=0)
    stock_minimo: int = Field(..., ge=0)
    precio: float = Field(..., gt=0)
    id_categoria: int

    @model_validator(mode="after")
    def validar_stock(self):
        if self.stock_minimo > self.stock_actual:
            raise ValueError("minimum stock cant be bigger than actual stock")
        return self

class ProductUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    stock_actual: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    precio: Optional[float] = Field(None, gt=0)
    id_categoria: Optional[int]

    @model_validator(mode="after")
    def validar_stock(self):
        if self.stock_actual is not None and self.stock_minimo is not None:
            if self.stock_minimo > self.stock_actual:
                raise ValueError("minimum stock cant be bigger than actual stock")
        return self

class ProductResponse(BaseModel):
    id_producto: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    stock_actual: int
    stock_minimo: int
    categoria: str
    estado_stock: str
class ClientBase(BaseModel):
    nombre: str = Field(..., min_length=1)
    apellido: str = Field(..., min_length=1)
    telefono: Optional[str] = None
    correo: Optional[str] = None
    nit: Optional[str] = None

    @field_validator("correo")
    def validar_correo(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid mail")
        return v

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    apellido: Optional[str] = Field(None, min_length=1)
    telefono: Optional[str] = None
    correo: Optional[str] = None
    nit: Optional[str] = None

    @field_validator("correo")
    def validar_correo(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid mail")
        return v

class ClientResponse(ClientBase):
    id_cliente: int

class SaleItem(BaseModel):
    id_producto: int
    cantidad: int = Field(..., gt=0)
    precio: float = Field(..., gt=0)


class SaleCreate(BaseModel):
    id_cliente: int
    id_empleado: int
    metodo_pago: str
    productos: List[SaleItem]

    @field_validator("metodo_pago")
    def validar_metodo_pago(cls, v):
        metodos_validos = ["efectivo", "tarjeta", "transferencia"]
        if v.lower() not in metodos_validos:
            raise ValueError(f"Invalid pay method. Use: {metodos_validos}")
        return v.lower()

    @field_validator("productos")
    def validar_productos(cls, v):
        if len(v) == 0:
            raise ValueError("Sale must have at least one product")
        return v

class SaleProductResponse(BaseModel):
    producto: str
    cantidad: int
    precio: float
    subtotal: float

class SaleResponse(BaseModel):
    id_venta: int
    fecha: str
    metodo_pago: str
    productos: List[SaleProductResponse]
    total: float