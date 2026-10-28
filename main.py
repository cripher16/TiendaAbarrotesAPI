import pyodbc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from conexion import conectar

app = FastAPI(title="API Tienda de Abarrotes")

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a TiendaAbarrotes"}

@app.get("/probar-conexion")
def probar_conexion():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT DB_NAME()")
        nombre = cursor.fetchone()[0]

        return {
            "mensaje": "Conexion exitosa",
            "base_datos": nombre
        }
    finally:
        conexion.close()

        
@app.get("/categorias")
def obtener_categorias():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT IdCategoria, Nombre, Descripcion FROM Categoria"
        )

        categorias = []

        for fila in cursor.fetchall():
            categorias.append({
                "IdCategoria": fila.IdCategoria,
                "Nombre": fila.Nombre,
                "Descripcion": fila.Descripcion
            })

        return categorias

    finally:
        conexion.close()


class CategoriaNueva(BaseModel):
    Nombre: str
    Descripcion: str | None = None


@app.post("/categorias", status_code=201)
def crear_categoria(categoria: CategoriaNueva):

    nombre = categoria.Nombre.strip()

    if not nombre or len(nombre) > 50:
        raise HTTPException(
            status_code=422,
            detail="El nombre debe tener entre 1 y 50 caracteres"
        )

    if categoria.Descripcion is not None and len(categoria.Descripcion) > 150:
        raise HTTPException(
            status_code=422,
            detail="La descripcion no puede superar 150 caracteres"
        )

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO Categoria (Nombre, Descripcion)
            OUTPUT INSERTED.IdCategoria
            VALUES (?, ?)
            """,
            (nombre, categoria.Descripcion)
        )

        id_categoria = cursor.fetchone()[0]
        cursor.nextset()
        conexion.commit()

        return {
            "mensaje": "Categoria registrada correctamente",
            "IdCategoria": id_categoria
        }

    except Exception as error:
        conexion.rollback()

        if isinstance(error, HTTPException):
            raise

        import pyodbc
        if isinstance(error, pyodbc.IntegrityError):
            raise HTTPException(
                status_code=409,
                detail="La categoria ya existe o incumple una restriccion"
            )

        raise HTTPException(
            status_code=500,
            detail="No se pudo registrar la categoria"
        )

    finally:
        conexion.close()


@app.get("/categorias/{id_categoria}")
def obtener_categoria(id_categoria: int):

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT IdCategoria, Nombre, Descripcion
            FROM Categoria
            WHERE IdCategoria = ?
            """,
            (id_categoria,)
        )

        fila = cursor.fetchone()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Categoria no encontrada"
            )

        return {
            "IdCategoria": fila.IdCategoria,
            "Nombre": fila.Nombre,
            "Descripcion": fila.Descripcion
        }

    finally:
        conexion.close()


@app.put("/categorias/{id_categoria}")
def actualizar_categoria(id_categoria: int, categoria: CategoriaNueva):

    nombre = categoria.Nombre.strip()

    if not nombre or len(nombre) > 50:
        raise HTTPException(
            status_code=422,
            detail="El nombre debe tener entre 1 y 50 caracteres"
        )

    if categoria.Descripcion is not None and len(categoria.Descripcion) > 150:
        raise HTTPException(
            status_code=422,
            detail="La descripcion no puede superar 150 caracteres"
        )

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            UPDATE Categoria
            SET Nombre = ?, Descripcion = ?
            WHERE IdCategoria = ?
            """,
            (nombre, categoria.Descripcion, id_categoria)
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            raise HTTPException(
                status_code=404,
                detail="Categoria no encontrada"
            )

        conexion.commit()

        return {
            "mensaje": "Categoria actualizada correctamente",
            "IdCategoria": id_categoria
        }

    except HTTPException:
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="El nombre de la categoria ya existe"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar la categoria"
        )

    finally:
        conexion.close()


@app.delete("/categorias/{id_categoria}")
def eliminar_categoria(id_categoria: int):

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        # Verificar si existe la categoria
        cursor.execute(
            "SELECT IdCategoria FROM Categoria WHERE IdCategoria = ?",
            (id_categoria,)
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Categoria no encontrada"
            )

        # Verificar si tiene productos relacionados
        cursor.execute(
            "SELECT COUNT(*) FROM Producto WHERE IdCategoria = ?",
            (id_categoria,)
        )

        cantidad = cursor.fetchone()[0]

        if cantidad > 0:
            raise HTTPException(
                status_code=409,
                detail="No se puede eliminar una categoria con productos"
            )

        # Eliminar la categoria
        cursor.execute(
            "DELETE FROM Categoria WHERE IdCategoria = ?",
            (id_categoria,)
        )

        conexion.commit()

        return {
            "mensaje": "Categoria eliminada correctamente",
            "IdCategoria": id_categoria
        }

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar por relaciones existentes"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar la categoria"
        )

    finally:
        conexion.close()


# MODELO PARA MARCAS
class MarcaNueva(BaseModel):
    Nombre: str


# CONSULTAR TODAS LAS MARCAS
@app.get("/marcas")
def obtener_marcas():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT IdMarca, Nombre FROM Marca")

        marcas = []

        for fila in cursor.fetchall():
            marcas.append({
                "IdMarca": fila.IdMarca,
                "Nombre": fila.Nombre
            })

        return marcas

    finally:
        conexion.close()


# CONSULTAR UNA MARCA POR ID
@app.get("/marcas/{id_marca}")
def obtener_marca(id_marca: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT IdMarca, Nombre FROM Marca WHERE IdMarca = ?",
            (id_marca,)
        )

        fila = cursor.fetchone()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Marca no encontrada"
            )

        return {
            "IdMarca": fila.IdMarca,
            "Nombre": fila.Nombre
        }

    finally:
        conexion.close()


# REGISTRAR UNA MARCA
@app.post("/marcas", status_code=201)
def crear_marca(marca: MarcaNueva):
    nombre = marca.Nombre.strip()

    if not nombre or len(nombre) > 50:
        raise HTTPException(
            status_code=422,
            detail="Nombre invalido"
        )

    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO Marca (Nombre) VALUES (?)",
            (nombre,)
        )

        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
        id_marca = cursor.fetchone()[0]

        conexion.commit()

        return {
            "mensaje": "Marca registrada correctamente",
            "IdMarca": id_marca
        }

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="La marca ya existe"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al registrar marca"
        )

    finally:
        conexion.close()


# ACTUALIZAR UNA MARCA
@app.put("/marcas/{id_marca}")
def actualizar_marca(id_marca: int, marca: MarcaNueva):
    nombre = marca.Nombre.strip()

    if not nombre or len(nombre) > 50:
        raise HTTPException(
            status_code=422,
            detail="Nombre invalido"
        )

    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE Marca SET Nombre = ? WHERE IdMarca = ?",
            (nombre, id_marca)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Marca no encontrada"
            )

        conexion.commit()

        return {"mensaje": "Marca actualizada correctamente"}

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="El nombre de la marca ya existe"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar marca"
        )

    finally:
        conexion.close()


# ELIMINAR UNA MARCA
@app.delete("/marcas/{id_marca}")
def eliminar_marca(id_marca: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM Producto WHERE IdMarca = ?",
            (id_marca,)
        )

        if cursor.fetchone()[0] > 0:
            raise HTTPException(
                status_code=409,
                detail="La marca tiene productos relacionados"
            )

        cursor.execute(
            "DELETE FROM Marca WHERE IdMarca = ?",
            (id_marca,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Marca no encontrada"
            )

        conexion.commit()

        return {"mensaje": "Marca eliminada correctamente"}

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="La marca tiene registros relacionados"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar marca"
        )

    finally:
        conexion.close()


# MODELO UNIDAD DE MEDIDA
class UnidadNueva(BaseModel):
    Nombre: str
    Abreviatura: str


# CONSULTAR TODAS LAS UNIDADES
@app.get("/unidades")
def obtener_unidades():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT IdUnidad, Nombre, Abreviatura FROM UnidadMedida"
        )

        unidades = []

        for fila in cursor.fetchall():
            unidades.append({
                "IdUnidad": fila.IdUnidad,
                "Nombre": fila.Nombre,
                "Abreviatura": fila.Abreviatura
            })

        return unidades

    finally:
        conexion.close()


# CONSULTAR UNA UNIDAD POR ID
@app.get("/unidades/{id_unidad}")
def obtener_unidad(id_unidad: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT IdUnidad, Nombre, Abreviatura
            FROM UnidadMedida
            WHERE IdUnidad = ?
            """,
            (id_unidad,)
        )

        fila = cursor.fetchone()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Unidad de medida no encontrada"
            )

        return {
            "IdUnidad": fila.IdUnidad,
            "Nombre": fila.Nombre,
            "Abreviatura": fila.Abreviatura
        }

    finally:
        conexion.close()


# REGISTRAR UNA UNIDAD
@app.post("/unidades", status_code=201)
def crear_unidad(unidad: UnidadNueva):
    nombre = unidad.Nombre.strip()
    abreviatura = unidad.Abreviatura.strip()

    if not nombre or len(nombre) > 50:
        raise HTTPException(
            status_code=422,
            detail="Nombre invalido"
        )

    if not abreviatura or len(abreviatura) > 10:
        raise HTTPException(
            status_code=422,
            detail="Abreviatura invalida"
        )

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO UnidadMedida (Nombre, Abreviatura)
            OUTPUT INSERTED.IdUnidad
            VALUES (?, ?)
            """,
            (nombre, abreviatura)
        )

        id_unidad = cursor.fetchone()[0]
        conexion.commit()

        return {
            "mensaje": "Unidad registrada correctamente",
            "IdUnidad": id_unidad
        }

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="La unidad ya existe"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al registrar unidad"
        )

    finally:
        conexion.close()


# ACTUALIZAR UNA UNIDAD
@app.put("/unidades/{id_unidad}")
def actualizar_unidad(id_unidad: int, unidad: UnidadNueva):
    nombre = unidad.Nombre.strip()
    abreviatura = unidad.Abreviatura.strip()

    if not nombre or len(nombre) > 50:
        raise HTTPException(
            status_code=422,
            detail="Nombre invalido"
        )

    if not abreviatura or len(abreviatura) > 10:
        raise HTTPException(
            status_code=422,
            detail="Abreviatura invalida"
        )

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            UPDATE UnidadMedida
            SET Nombre = ?, Abreviatura = ?
            WHERE IdUnidad = ?
            """,
            (nombre, abreviatura, id_unidad)
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            raise HTTPException(
                status_code=404,
                detail="Unidad no encontrada"
            )

        conexion.commit()

        return {"mensaje": "Unidad actualizada correctamente"}

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una unidad con ese nombre"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar unidad"
        )

    finally:
        conexion.close()


# ELIMINAR UNA UNIDAD
@app.delete("/unidades/{id_unidad}")
def eliminar_unidad(id_unidad: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM Producto WHERE IdUnidad = ?",
            (id_unidad,)
        )

        if cursor.fetchone()[0] > 0:
            raise HTTPException(
                status_code=409,
                detail="La unidad tiene productos relacionados"
            )

        cursor.execute(
            "DELETE FROM UnidadMedida WHERE IdUnidad = ?",
            (id_unidad,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Unidad no encontrada"
            )

        conexion.commit()

        return {"mensaje": "Unidad eliminada correctamente"}

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="La unidad tiene registros relacionados"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar unidad"
        )

    finally:
        conexion.close()


# MODELO PROVEEDOR
class ProveedorNuevo(BaseModel):
    Nombre: str
    Telefono: str | None = None
    Direccion: str | None = None


def validar_proveedor(proveedor):
    nombre = proveedor.Nombre.strip()

    if not nombre or len(nombre) > 100:
        raise HTTPException(
            status_code=422,
            detail="Nombre invalido"
        )

    if proveedor.Telefono is not None and len(proveedor.Telefono) > 15:
        raise HTTPException(
            status_code=422,
            detail="Telefono demasiado largo"
        )

    if proveedor.Direccion is not None and len(proveedor.Direccion) > 150:
        raise HTTPException(
            status_code=422,
            detail="Direccion demasiado larga"
        )

    return nombre


# CONSULTAR TODOS LOS PROVEEDORES
@app.get("/proveedores")
def obtener_proveedores():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT IdProveedor, Nombre, Telefono, Direccion
            FROM Proveedor
        """)

        return [
            {
                "IdProveedor": fila.IdProveedor,
                "Nombre": fila.Nombre,
                "Telefono": fila.Telefono,
                "Direccion": fila.Direccion
            }
            for fila in cursor.fetchall()
        ]

    finally:
        conexion.close()


# CONSULTAR PROVEEDOR POR ID
@app.get("/proveedores/{id_proveedor}")
def obtener_proveedor(id_proveedor: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT IdProveedor, Nombre, Telefono, Direccion
            FROM Proveedor
            WHERE IdProveedor = ?
        """, (id_proveedor,))

        fila = cursor.fetchone()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

        return {
            "IdProveedor": fila.IdProveedor,
            "Nombre": fila.Nombre,
            "Telefono": fila.Telefono,
            "Direccion": fila.Direccion
        }

    finally:
        conexion.close()


# CREAR PROVEEDOR
@app.post("/proveedores", status_code=201)
def crear_proveedor(proveedor: ProveedorNuevo):
    nombre = validar_proveedor(proveedor)
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO Proveedor (Nombre, Telefono, Direccion)
            OUTPUT INSERTED.IdProveedor
            VALUES (?, ?, ?)
        """, (nombre, proveedor.Telefono, proveedor.Direccion))

        id_proveedor = cursor.fetchone()[0]
        conexion.commit()

        return {
            "mensaje": "Proveedor registrado correctamente",
            "IdProveedor": id_proveedor
        }

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al registrar proveedor"
        )

    finally:
        conexion.close()


# ACTUALIZAR PROVEEDOR
@app.put("/proveedores/{id_proveedor}")
def actualizar_proveedor(id_proveedor: int, proveedor: ProveedorNuevo):
    nombre = validar_proveedor(proveedor)
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE Proveedor
            SET Nombre = ?, Telefono = ?, Direccion = ?
            WHERE IdProveedor = ?
        """, (nombre, proveedor.Telefono, proveedor.Direccion, id_proveedor))

        if cursor.rowcount == 0:
            conexion.rollback()
            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

        conexion.commit()

        return {"mensaje": "Proveedor actualizado correctamente"}

    except HTTPException:
        raise

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar proveedor"
        )

    finally:
        conexion.close()


# ELIMINAR PROVEEDOR
@app.delete("/proveedores/{id_proveedor}")
def eliminar_proveedor(id_proveedor: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM Compra
            WHERE IdProveedor = ?
        """, (id_proveedor,))

        if cursor.fetchone()[0] > 0:
            raise HTTPException(
                status_code=409,
                detail="El proveedor tiene compras relacionadas"
            )

        cursor.execute("""
            DELETE FROM Proveedor
            WHERE IdProveedor = ?
        """, (id_proveedor,))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

        conexion.commit()

        return {"mensaje": "Proveedor eliminado correctamente"}

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="El proveedor tiene registros relacionados"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar proveedor"
        )

    finally:
        conexion.close()


# MODELO CLIENTE
class ClienteNuevo(BaseModel):
    Nombre: str
    Telefono: str | None = None


def validar_cliente(cliente):
    nombre = cliente.Nombre.strip()

    if not nombre or len(nombre) > 100:
        raise HTTPException(
            status_code=422,
            detail="El nombre debe tener entre 1 y 100 caracteres"
        )

    if cliente.Telefono is not None and len(cliente.Telefono) > 15:
        raise HTTPException(
            status_code=422,
            detail="El telefono no puede superar 15 caracteres"
        )

    return nombre


# CONSULTAR TODOS LOS CLIENTES
@app.get("/clientes")
def obtener_clientes():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT IdCliente, Nombre, Telefono
            FROM Cliente
            ORDER BY IdCliente
        """)

        return [
            {
                "IdCliente": fila.IdCliente,
                "Nombre": fila.Nombre,
                "Telefono": fila.Telefono
            }
            for fila in cursor.fetchall()
        ]

    finally:
        conexion.close()


# CONSULTAR CLIENTE POR ID
@app.get("/clientes/{id_cliente}")
def obtener_cliente(id_cliente: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT IdCliente, Nombre, Telefono
            FROM Cliente
            WHERE IdCliente = ?
        """, (id_cliente,))

        fila = cursor.fetchone()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado"
            )

        return {
            "IdCliente": fila.IdCliente,
            "Nombre": fila.Nombre,
            "Telefono": fila.Telefono
        }

    finally:
        conexion.close()


# CREAR CLIENTE
@app.post("/clientes", status_code=201)
def crear_cliente(cliente: ClienteNuevo):
    nombre = validar_cliente(cliente)
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO Cliente (Nombre, Telefono)
            OUTPUT INSERTED.IdCliente
            VALUES (?, ?)
        """, (nombre, cliente.Telefono))

        id_cliente = cursor.fetchone()[0]
        conexion.commit()

        return {
            "mensaje": "Cliente registrado correctamente",
            "IdCliente": id_cliente
        }

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al registrar cliente"
        )

    finally:
        conexion.close()


# ACTUALIZAR CLIENTE
@app.put("/clientes/{id_cliente}")
def actualizar_cliente(id_cliente: int, cliente: ClienteNuevo):
    nombre = validar_cliente(cliente)
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE Cliente
            SET Nombre = ?, Telefono = ?
            WHERE IdCliente = ?
        """, (nombre, cliente.Telefono, id_cliente))

        if cursor.rowcount == 0:
            conexion.rollback()
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado"
            )

        conexion.commit()

        return {
            "mensaje": "Cliente actualizado correctamente"
        }

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar cliente"
        )

    finally:
        conexion.close()


# ELIMINAR CLIENTE
@app.delete("/clientes/{id_cliente}")
def eliminar_cliente(id_cliente: int):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        # Verificar ventas relacionadas
        cursor.execute("""
            SELECT COUNT(*)
            FROM Venta
            WHERE IdCliente = ?
        """, (id_cliente,))

        if cursor.fetchone()[0] > 0:
            raise HTTPException(
                status_code=409,
                detail="El cliente tiene ventas relacionadas"
            )

        cursor.execute("""
            DELETE FROM Cliente
            WHERE IdCliente = ?
        """, (id_cliente,))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado"
            )

        conexion.commit()

        return {
            "mensaje": "Cliente eliminado correctamente"
        }

    except HTTPException:
        conexion.rollback()
        raise

    except pyodbc.IntegrityError:
        conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar por registros relacionados"
        )

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar cliente"
        )

    finally:
        conexion.close()


from decimal import Decimal
from pydantic import Field

# MODELO PARA REGISTRAR COMPRAS
class CompraNueva(BaseModel):
    IdProveedor: int = Field(gt=0)
    IdProducto: int = Field(gt=0)
    Cantidad: int = Field(gt=0)
    PrecioCompra: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


@app.post("/compras", status_code=201)
def registrar_compra(compra: CompraNueva):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            EXEC RegistrarCompra
                @IdProveedor = ?,
                @IdProducto = ?,
                @Cantidad = ?,
                @PrecioCompra = ?
            """,
            (
                compra.IdProveedor,
                compra.IdProducto,
                compra.Cantidad,
                compra.PrecioCompra
            )
        )

        conexion.commit()

        return {
            "mensaje": "Compra procesada correctamente"
        }

    except pyodbc.Error:
        conexion.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo registrar la compra. Verifica los datos."
        )

    finally:
        conexion.close()



# MODELO PARA REGISTRAR VENTAS
class VentaNueva(BaseModel):
    IdCliente: int = Field(gt=0)
    IdProducto: int = Field(gt=0)
    Cantidad: int = Field(gt=0)


# ENDPOINT PARA REGISTRAR VENTAS
@app.post("/ventas", status_code=201)
def registrar_venta(venta: VentaNueva):

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            EXEC RegistrarVenta
                @IdCliente = ?,
                @IdProducto = ?,
                @Cantidad = ?
            """,
            (
                venta.IdCliente,
                venta.IdProducto,
                venta.Cantidad
            )
        )

       
        # Avanzar hasta encontrar el resultado SELECT
        while cursor.description is None:
            if not cursor.nextset():
                raise HTTPException(
                    status_code=500,
                    detail="El procedimiento no devolvio resultados"
                )

        resultado = cursor.fetchone()

        if resultado is None:
            raise HTTPException(
                status_code=500,
                detail="El procedimiento no devolvio resultados"
            )

        respuesta = {
            "mensaje": resultado[0],
            "IdVenta": resultado[1],
            "Total": float(resultado[2])
        }


        if resultado is None:
            raise HTTPException(
                status_code=500,
                detail="El procedimiento no devolvio resultados"
            )

        respuesta = {
            "mensaje": resultado[0],
            "IdVenta": resultado[1],
            "Total": float(resultado[2])
        }

        conexion.commit()

        return respuesta

    except pyodbc.Error as error:
        conexion.rollback()

        print("ERROR SQL SERVER:", repr(error))

        raise HTTPException(
            status_code=400,
            detail="Error al ejecutar RegistrarVenta"
        )

    finally:
        conexion.close()

    
# REPORTE DE VENTAS POR CLIENTE
@app.get("/reportes/ventas-clientes")
def reporte_ventas_clientes():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("EXEC ReporteVentasCliente")

        while cursor.description is None:
            if not cursor.nextset():
                raise HTTPException(
                    status_code=500,
                    detail="El reporte no devolvio resultados"
                )

        reportes = []

        for fila in cursor.fetchall():
            reportes.append({
                "Cliente": fila.Cliente,
                "CantidadVentas": fila.CantidadVentas,
                "TotalGastado": float(fila.TotalGastado)
            })

        return reportes

    finally:
        conexion.close()


# REPORTE DE INVENTARIO POR CATEGORIA
@app.get("/reportes/inventario-categorias")
def reporte_inventario_categorias():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("EXEC ReporteInventarioCategoria")

        while cursor.description is None:
            if not cursor.nextset():
                raise HTTPException(
                    status_code=500,
                    detail="El reporte no devolvio resultados"
                )

        reportes = []

        for fila in cursor.fetchall():
            reportes.append({
                "Categoria": fila.Categoria,
                "CantidadProductos": fila.CantidadProductos,
                "TotalExistencias": fila.TotalExistencias
            })

        return reportes

    finally:
        conexion.close()

