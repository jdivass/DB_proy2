from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class ProductCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    stock_actual: int = Field(..., ge=0)
    stock_minimo: int = Field(..., ge=0)
    precio: float = Field(..., gt=0)
    id_categoria: int

    @field_validator("stock_minimo")
    def validar_stock(cls, v, values):
        stock_actual = values.data.get("stock_actual")
        if stock_actual is not None and v > stock_actual:
            raise ValueError("stock_minimo no puede ser mayor que stock_actual")
        return v


class ProductUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    stock_actual: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    precio: Optional[float] = Field(None, gt=0)
    id_categoria: Optional[int]


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
            raise ValueError(f"Metodo de pago inválido. Use: {metodos_validos}")
        return v.lower()