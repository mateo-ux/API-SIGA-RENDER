import os
import requests
import pandas as pd
from dotenv import load_dotenv
import json
import time

# Cargar las variables del archivo .env
load_dotenv()

def print_json_bonito(data):
    """Imprime un JSON con formato legible por consola"""
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))


def guardar_json(data, nombre_reporte):
    """Guarda la respuesta JSON como archivo .json en carpeta output/"""
    if not data or not isinstance(data, list):
        print("⚠️ No hay datos válidos para exportar.")
        return

    # Crear carpeta de salida si no existe
    os.makedirs("output", exist_ok=True)

    # Generar nombre del archivo
    filename = f"output/{nombre_reporte}.json"

    # Eliminar el archivo si ya existe
    if os.path.exists(filename):
        os.remove(filename)  # Eliminar el archivo existente

    try:
        # Guardar el archivo JSON con formato legible
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Archivo guardado: {filename}")
    except Exception as e:
        print(f"❌ Error al guardar JSON: {e}")

import os
import json
import pandas as pd

def generar_csv_con_informacionj(reporte_excel):
    """
    Nueva versión JSON-first:
    - Entrada: ruta a .xlsx (actual) o .json con las mismas columnas.
    - Salida: output/<base>_modificado.json con la estructura para Moodle.
    - Retorna: (ruta_json_salida, rows_en_memoria)

    Estructura de salida (list[dict]):
      idnumber, username, password, firstname, lastname, phone1, email,
      profile_field_departamento, profile_field_municipio, profile_field_modalidad,
      group1, course1, role1
    """
    try:
        if not isinstance(reporte_excel, str) or not os.path.exists(reporte_excel):
            print("⚠️ La ruta del reporte no existe o no es válida.")
            return None, []

        # Cargar origen en DataFrame
        if reporte_excel.lower().endswith(".xlsx"):
            df = pd.read_excel(reporte_excel)
        elif reporte_excel.lower().endswith(".json"):
            with open(reporte_excel, "r", encoding="utf-8") as f:
                data = json.load(f)
            # data puede ser list[dict] o dict con 'data'/'items'
            if isinstance(data, dict):
                data = data.get("data") or data.get("items") or data.get("rows") or []
            df = pd.DataFrame(data)
        else:
            print("⚠️ Formato no soportado. Usa .xlsx o .json como entrada.")
            return None, []

        # Verificar columnas requeridas
        required_columns = [
            'documento_numero', 'nombres', 'apellidos', 'telefono_celular',
            'correo_electronico', 'departamento', 'municipio',
            'modalidad_formacion', 'programa_interes', 'inscripcion_aprobada'
        ]
        if not all(col in df.columns for col in required_columns):
            print("⚠️ Algunas columnas necesarias están ausentes en el archivo de entrada.")
            return None, []

        # Filtrar aprobados
        df_aprobados = df[df['inscripcion_aprobada'] == 'APROBADO'].copy()
        if df_aprobados.empty:
            print("⚠️ No hay registros aprobados para exportar.")
            # Aun así creamos un JSON vacío para mantener flujo estable
            out_dir = "output"
            os.makedirs(out_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(reporte_excel))[0]
            out_path = os.path.join(out_dir, f"{base}_modificado.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return out_path, []

        # Mapeo de programa_interes
        mapa_programa = {
            'INTELIGENCIA ARTIFICIAL': 'Inteligencia Artificial',
            'ANÁLISIS DE DATOS': 'Analisis_datos',
            'PROGRAMACIÓN': 'Programacion',
            'CIBERSEGURIDAD': 'Ciberseguridad1',
            'ARQUITECTURA EN LA NUBE': 'Arquitectura_Nube',
            'BLOCKCHAIN': 'Blockchain'
        }

        # Construir estructura de salida
        df_nuevo = pd.DataFrame({
            'idnumber': df_aprobados['documento_numero'].astype(str),
            'username': df_aprobados['documento_numero'].astype(str),
            'password': df_aprobados['documento_numero'].astype(str),
            'firstname': df_aprobados['nombres'],
            'lastname': df_aprobados['apellidos'],
            'phone1': df_aprobados['telefono_celular'],
            'email': df_aprobados['correo_electronico'],
            'profile_field_departamento': df_aprobados['departamento'],
            'profile_field_municipio': df_aprobados['municipio'],
            'profile_field_modalidad': df_aprobados['modalidad_formacion'],
            'group1': df_aprobados['programa_interes'].astype(str).str.upper().map(mapa_programa).fillna(df_aprobados['programa_interes']),
            'course1': 'Prueba de Inicio Talento Tech',
            'role1': 5
        })

        # Guardar como JSON
        out_dir = "output"
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(reporte_excel))[0]
        out_path = os.path.join(out_dir, f"{base}_modificado.json")

        rows = df_nuevo.to_dict(orient="records")
        # Sobrescribir si existe (idempotente)
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except Exception:
                pass

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

        print(f"✅ Archivo JSON generado correctamente: {out_path}")
        return out_path, rows

    except Exception as e:
        print(f"❌ Error al generar el JSON: {e}")
        return None, []



import os
import json

def comparar_documentos_y_generar_faltantesj(
    usuarios_path: str = "output/reporte_1003_modificado.json",
    nivelacion_path: str = "input/Prueba de nivelacion Padre.json",
    salida_path: str = "output/usuarios_faltantes_nivelacion.json"
):
    """
    Compara usuarios (1003_modificado) vs el maestro de nivelación y genera un JSON con los faltantes.
    Entradas:
      - usuarios_path: JSON con campos al menos 'idnumber'
      - nivelacion_path: JSON maestro con campo 'username'
    Salida:
      - salida_path: JSON con las filas de usuarios que faltan en nivelación
    """
    try:
        # ---- Cargar usuarios (1003_modificado) ----
        if not os.path.exists(usuarios_path):
            print(f"❌ Error: No existe {usuarios_path}")
            return None

        with open(usuarios_path, "r", encoding="utf-8") as f:
            usuarios_data = json.load(f)

        # Normalizar a list[dict]
        if isinstance(usuarios_data, dict):
            usuarios_rows = usuarios_data.get("rows") or usuarios_data.get("data") or usuarios_data.get("items") or []
        else:
            usuarios_rows = usuarios_data

        if not isinstance(usuarios_rows, list) or (usuarios_rows and not isinstance(usuarios_rows[0], dict)):
            print("❌ Formato inválido en usuarios (se esperaba list[dict]).")
            return None

        if not usuarios_rows:
            print("⚠️ El archivo de usuarios está vacío.")
            # Creamos salida vacía para mantener flujo
            os.makedirs(os.path.dirname(salida_path), exist_ok=True)
            with open(salida_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return salida_path

        # Validar columna requerida
        if "idnumber" not in usuarios_rows[0]:
            print("❌ El JSON de usuarios no contiene la clave 'idnumber'.")
            return None

        # ---- Cargar nivelación (maestro) ----
        if not os.path.exists(nivelacion_path):
            print(f"❌ Error: No existe {nivelacion_path}")
            return None

        with open(nivelacion_path, "r", encoding="utf-8") as f:
            nivelacion_data = json.load(f)

        if isinstance(nivelacion_data, dict):
            nivelacion_rows = nivelacion_data.get("rows") or nivelacion_data.get("data") or nivelacion_data.get("items") or []
        else:
            nivelacion_rows = nivelacion_data

        if not isinstance(nivelacion_rows, list) or (nivelacion_rows and not isinstance(nivelacion_rows[0], dict)):
            print("❌ Formato inválido en nivelación (se esperaba list[dict]).")
            return None

        if not nivelacion_rows:
            print("⚠️ El maestro de nivelación está vacío; todos los usuarios serán faltantes.")

        # Validar columna requerida
        if nivelacion_rows and "username" not in nivelacion_rows[0]:
            print("❌ El JSON de nivelación no contiene la clave 'username'.")
            return None

        # ---- Calcular faltantes ----
        documentos_usuarios = {str(u.get("idnumber", "")).strip() for u in usuarios_rows if u.get("idnumber") not in (None, "")}
        documentos_nivelacion = {str(n.get("username", "")).strip() for n in nivelacion_rows if n.get("username") not in (None, "")}

        documentos_faltantes = documentos_usuarios - documentos_nivelacion

        if not documentos_faltantes:
            print("✅ Todos los usuarios están en el maestro de nivelación.")
            # Generamos igualmente un JSON vacío
            os.makedirs(os.path.dirname(salida_path), exist_ok=True)
            with open(salida_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return salida_path

        faltantes_rows = [u for u in usuarios_rows if str(u.get("idnumber", "")).strip() in documentos_faltantes]

        if not faltantes_rows:
            print("⚠️ No se encontraron registros faltantes (posible inconsistencia de datos).")
            os.makedirs(os.path.dirname(salida_path), exist_ok=True)
            with open(salida_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return salida_path

        # ---- Guardar salida JSON ----
        os.makedirs(os.path.dirname(salida_path), exist_ok=True)
        # Sobrescribir si ya existe
        try:
            if os.path.exists(salida_path):
                os.remove(salida_path)
        except Exception:
            pass

        with open(salida_path, "w", encoding="utf-8") as f:
            json.dump(faltantes_rows, f, ensure_ascii=False, indent=2)

        print(f"✅ Archivo generado con usuarios faltantes: {salida_path}")
        print(f"📝 Total de usuarios faltantes: {len(faltantes_rows)}")
        return salida_path

    except FileNotFoundError as e:
        print(f"❌ Error: Archivo no encontrado - {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

def verificar_usuarios_individualmentej(
    faltantes_path: str = "output/usuarios_faltantes_nivelacion.json",
    resultados_path: str = "output/verificacion_individual_moodle.json",
    no_matriculados_path: str = "output/usuarios_no_matriculados.json",
    maestro_path: str = "input/Prueba de nivelacion Padre.json"
):
    """
    Verifica usuarios faltantes en Moodle uno por uno y genera:
      - output/verificacion_individual_moodle.json (reporte completo)
      - output/usuarios_no_matriculados.json (subset)
      - Actualiza Prueba de nivelacion Padre.json agregando 'username' de los matriculados.
    Entradas:
      - faltantes_path: JSON con al menos la clave 'idnumber' por registro.
    """
    try:
        # 1) Cargar usuarios faltantes (JSON)
        if not os.path.exists(faltantes_path):
            print(f"❌ No existe {faltantes_path}")
            return

        with open(faltantes_path, "r", encoding="utf-8") as f:
            faltantes_data = json.load(f)

        if isinstance(faltantes_data, dict):
            faltantes_rows = faltantes_data.get("rows") or faltantes_data.get("data") or faltantes_data.get("items") or []
        else:
            faltantes_rows = faltantes_data

        if not isinstance(faltantes_rows, list):
            print("❌ Formato inválido en faltantes (se esperaba list[dict]).")
            return

        df_faltantes = pd.DataFrame(faltantes_rows)
        if df_faltantes.empty or "idnumber" not in df_faltantes.columns:
            print("⚠️ 'faltantes' vacío o sin columna 'idnumber'.")
            # Aun así dejar archivos consistentes
            os.makedirs(os.path.dirname(resultados_path), exist_ok=True)
            with open(resultados_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            with open(no_matriculados_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return

        # 2) Configuración Moodle
        load_dotenv()
        MOODLE_URL = os.getenv("MOODLE_URL")  # En tu .env ya apunta a .../webservice/rest/server.php
        MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
        COURSE_ID = os.getenv("PRUEBA_INICIO_COURSE_ID", "5")  # por defecto 5

        if not MOODLE_URL or not MOODLE_TOKEN:
            print("❌ Faltan MOODLE_URL/MOODLE_TOKEN en el .env")
            return

        session = requests.Session()

        def usuario_en_moodle(documento: str) -> bool:
            params = {
                'wstoken': MOODLE_TOKEN,
                'wsfunction': 'core_user_get_users_by_field',
                'field': 'username',
                'values[0]': documento,
                'moodlewsrestformat': 'json'
            }
            try:
                r = session.get(MOODLE_URL, params=params, timeout=15)
                users = r.json()
                return isinstance(users, list) and len(users) > 0
            except Exception:
                return False

        # 3) Verificar cada usuario
        total_usuarios = len(df_faltantes)
        print(f"\n🔍 Verificando {total_usuarios} usuarios individualmente...")

        resultados = []
        for i, row in df_faltantes.iterrows():
            documento = str(row['idnumber'])
            en_moodle = usuario_en_moodle(documento)
            resultados.append({
                "idnumber": documento,
                "en_moodle": bool(en_moodle),
                "fecha_verificacion": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            if (i + 1) % 10 == 0 or (i + 1) == total_usuarios:
                print(f"Progreso: {i+1}/{total_usuarios} | Último documento: {documento}")

        df_resultados = pd.DataFrame(resultados)

        # 4) Separar matriculados / no matriculados
        df_matriculados = df_faltantes[
            df_faltantes['idnumber'].isin(
                df_resultados[df_resultados['en_moodle'] == True]['idnumber']
            )
        ]
        df_no_matriculados = df_faltantes[
            df_faltantes['idnumber'].isin(
                df_resultados[df_resultados['en_moodle'] == False]['idnumber']
            )
        ]

        # 5) Guardar salidas como JSON
        os.makedirs(os.path.dirname(resultados_path), exist_ok=True)

        with open(resultados_path, "w", encoding="utf-8") as f:
            json.dump(df_resultados.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        print(f"📊 Reporte completo guardado en {resultados_path}")

        with open(no_matriculados_path, "w", encoding="utf-8") as f:
            json.dump(df_no_matriculados.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        print(f"✅ {len(df_no_matriculados)} usuarios NO matriculados guardados en {no_matriculados_path}")

        # 6) Actualizar maestro de nivelación (JSON) con los matriculados
        if not df_matriculados.empty:
            # Cargar maestro actual
            if os.path.exists(maestro_path):
                with open(maestro_path, "r", encoding="utf-8") as f:
                    maestro_data = json.load(f)
                if isinstance(maestro_data, dict):
                    maestro_rows = maestro_data.get("rows") or maestro_data.get("data") or maestro_data.get("items") or []
                else:
                    maestro_rows = maestro_data
            else:
                maestro_rows = []

            # Normalizar maestro a lista de dicts con 'username'
            if not isinstance(maestro_rows, list):
                maestro_rows = []
            # Conjunto existente
            existentes = {str(r.get("username", "")).strip() for r in maestro_rows if isinstance(r, dict)}

            nuevos = []
            for doc in df_matriculados['idnumber'].astype(str):
                u = doc.strip()
                if u and u not in existentes:
                    nuevos.append({"username": u})

            if nuevos:
                maestro_rows.extend(nuevos)
                # Guardar maestro actualizado
                with open(maestro_path, "w", encoding="utf-8") as f:
                    json.dump(maestro_rows, f, ensure_ascii=False, indent=2)
                print(f"📁 {len(nuevos)} usuarios agregados a {maestro_path}")
            else:
                print("ℹ️ No había usuarios nuevos para agregar al maestro.")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
import os
import json
import pandas as pd
# Si quieres normalizar acentos en departamento/modalidad, descomenta:
# import unicodedata

def _load_json_rows(path: str):
    """Carga JSON tolerante a BOM y devuelve list[dict].
       Acepta: list[dict] o dict con claves 'rows'/'data'/'items'/'result'."""
    with open(path, "r", encoding="utf-8-sig") as f:  # <- clave contra BOM
        data = json.load(f)

    if isinstance(data, dict):
        for key in ("rows", "data", "items", "result"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # Si es dict pero no trae lista, intenta convertir a lista de un solo elemento
        return [data] if data else []
    elif isinstance(data, list):
        return data
    else:
        return []

def asignar_lote(df: pd.DataFrame):
    """
    Valida registros y asigna lotes (Lote 1 / Lote 2) balanceados.
    Requisitos:
      - Columnas: 'profile_field_modalidad', 'profile_field_departamento'
      - Modalidad permitida: 'VIRTUAL' o 'PRESENCIAL'
      - Departamento permitido: ANTIOQUIA, CALDAS, CHOCÓ, QUINDÍO, RISARALDA

    Retorna:
      df_valid (con 'profile_field_lote')
      df_invalid (con 'motivo_rechazo')
    """
    required_cols = {'profile_field_modalidad', 'profile_field_departamento'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(sorted(missing))}")

    work = df.copy()

    # Normalizaciones
    work['profile_field_modalidad'] = work['profile_field_modalidad'].apply(
        lambda x: str(x).strip().upper() if pd.notna(x) else ''
    )
    work['profile_field_departamento'] = work['profile_field_departamento'].apply(
        lambda x: str(x).strip().upper() if pd.notna(x) else ''
    )

    # Si quieres quitar acentos para comparar (útil si la fuente a veces viene sin acentos):
    # def _norm_up(s):
    #     s = '' if pd.isna(s) else str(s)
    #     s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    #     return s.strip().upper()
    # work['profile_field_departamento'] = work['profile_field_departamento'].map(_norm_up)
    # work['profile_field_modalidad']   = work['profile_field_modalidad'].map(_norm_up)

    modalidades_validas = {'VIRTUAL', 'PRESENCIAL'}
    departamentos_validos = {'ANTIOQUIA', 'CALDAS', 'CHOCÓ', 'QUINDÍO', 'RISARALDA'}

    motivos = []
    invalid_mask = pd.Series(False, index=work.index)

    mask_modalidad = ~work['profile_field_modalidad'].isin(modalidades_validas)
    invalid_mask = invalid_mask | mask_modalidad

    mask_departamento = ~work['profile_field_departamento'].isin(departamentos_validos)
    invalid_mask = invalid_mask | mask_departamento

    for i, row in work.iterrows():
        m = []
        if mask_modalidad.loc[i]:
            m.append(f"Modalidad inválida: {row.get('profile_field_modalidad', '')}")
        if mask_departamento.loc[i]:
            m.append(f"Departamento no permitido: {row.get('profile_field_departamento', '')}")
        motivos.append(" | ".join(m) if m else "")

    work['motivo_rechazo'] = motivos

    df_invalid = work[invalid_mask].copy()
    df_valid = work[~invalid_mask].copy()

    # Asignación de lote (round-robin)
    df_valid = df_valid.reset_index(drop=True)
    if not df_valid.empty:
        lotes = ['Lote 1' if (i % 2 == 0) else 'Lote 2' for i in range(len(df_valid))]
        df_valid['profile_field_lote'] = lotes
    else:
        df_valid['profile_field_lote'] = pd.Series(dtype=object)

    if 'profile_field_lote' not in df_invalid.columns:
        df_invalid['profile_field_lote'] = ""

    new_cols = []
    for c in ['profile_field_lote']:
        if c not in df.columns:
            new_cols.append(c)

    df_valid = df_valid[[*df.columns, *[c for c in new_cols if c in df_valid.columns]]]
    df_invalid = df_invalid[[*df.columns, 'motivo_rechazo', *(['profile_field_lote'] if 'profile_field_lote' in df_invalid.columns else [])]]

    return df_valid, df_invalid

def procesar_archivoj(
    ruta_archivo: str,
    moodle_manager=None,
    salida_valid: str = "output/resultado_lotes.json",
    salida_invalid: str = "output/resultado_lotes_descartados.json",
):
    """
    Lee un JSON (list[dict] o dict con rows/data/items) tolerante a BOM,
    valida columnas mínimas y asigna lotes. Genera:
      - output/resultado_lotes.json
      - output/resultado_lotes_descartados.json
    """
    try:
        if not isinstance(ruta_archivo, str) or not os.path.exists(ruta_archivo):
            print("❌ La ruta del archivo no existe o no es válida.")
            return None, None

        # --- AQUÍ EL CAMBIO CLAVE: loader tolerante a BOM ---
        rows = _load_json_rows(ruta_archivo)

        if not isinstance(rows, list) or (rows and not isinstance(rows[0], dict)):
            print("❌ Formato inválido: se esperaba una lista de objetos (list[dict]).")
            return None, None

        df = pd.DataFrame(rows)
        print("Columnas del archivo cargado:")
        print(list(df.columns))

        required = {'profile_field_modalidad', 'profile_field_departamento'}
        if not required.issubset(set(df.columns)):
            print("❌ El archivo no contiene las columnas requeridas: "
                  "'profile_field_modalidad' y 'profile_field_departamento'.")
            return None, None

        df_valid, df_invalid = asignar_lote(df)

        output_dir = os.path.dirname(salida_valid) or "output"
        os.makedirs(output_dir, exist_ok=True)

        def _dump_json(path, payload):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

        valid_rows = df_valid.to_dict(orient="records") if not df_valid.empty else []
        _dump_json(salida_valid, valid_rows)
        print(f"✅ Archivo de filas válidas guardado como '{salida_valid}'.")

        invalid_rows = df_invalid.to_dict(orient="records") if not df_invalid.empty else []
        if invalid_rows:
            _dump_json(salida_invalid, invalid_rows)
            print(f"⚠️ Archivo de filas inválidas guardado como '{salida_invalid}'.")
            if moodle_manager:
                print("\nRegistrando usuarios rechazados en Matriculados Fallidos...")
                for row in invalid_rows:
                    modalidad = (row.get('profile_field_modalidad') or '').strip().upper()
                    departamento = (row.get('profile_field_departamento') or '').strip().upper()

                    motivo = "Rechazado - "
                    if modalidad not in ['VIRTUAL', 'PRESENCIAL']:
                        motivo += f"Modalidad inválida: {row.get('profile_field_modalidad', '')}"
                    elif departamento not in ['ANTIOQUIA', 'CALDAS', 'CHOCÓ', 'QUINDÍO', 'RISARALDA']:
                        motivo += f"Departamento no permitido: {row.get('profile_field_departamento', '')}"
                    else:
                        motivo += "Razón desconocida"

                    user_data = {
                        'username': row.get('username', ''),
                        'firstname': row.get('firstname', ''),
                        'lastname': row.get('lastname', ''),
                        'email': row.get('email', ''),
                        'phone1': row.get('phone1', ''),
                        'idnumber': row.get('idnumber', ''),
                        'group1': row.get('group1', ''),
                        'password': 'No aplica'
                    }
                    moodle_manager.registrar_resultado(
                        row=user_data,
                        tipo="fallido",
                        motivo=motivo,
                        grupo=row.get('group1', '')
                    )
        else:
            _dump_json(salida_invalid, [])
            print("ℹ️ No hubo filas inválidas. Se creó un JSON vacío de descartados.")

        return salida_valid, salida_invalid

    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")
        return None, None


# Ejemplo de uso
#ruta_archivo = 'output/usuarios_no_matriculados.csv'
import os
import json
import time
import csv  # <- lo dejo por compatibilidad si en otro lado lo usas, pero no se usa aquí para IO
import requests
from datetime import datetime
from urllib.parse import urljoin
from dotenv import load_dotenv

class MoodleManager:
    def __init__(self):
        load_dotenv()
        self.MOODLE_URL = os.getenv('MOODLE_URL').rstrip('/') + '/'
        self.MOODLE_TOKEN = os.getenv('MOODLE_TOKEN')
        self.session = requests.Session()
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        # Configuración de Google Sheets via Apps Script
        self.APPS_SCRIPT_URL = os.getenv('APPS_SCRIPT_WEBAPP_URL')
        self.SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
        self.MAX_RETRIES = 3  # Número máximo de reintentos

        # ARCHIVO DE EXITOSOS -> JSON (antes: CSV)
        self.ARCHIVO_EXITOSOS = 'input/Prueba de nivelacion Padre.json'
        
        if not all([self.MOODLE_URL, self.MOODLE_TOKEN, self.APPS_SCRIPT_URL, self.SHEET_ID]):
            raise ValueError("Faltan configuraciones en el archivo .env")

    def _leer_json_lista(self, path):
        """Lee un archivo JSON que contiene una lista (tolerante a UTF-8 con BOM)."""
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        # Permitimos tanto list como dict con clave 'rows'/'data'/'items'
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ('rows', 'data', 'items'):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

    def _escribir_json_lista(self, path, lista):
        """Escribe una lista en JSON (crea carpetas si faltan)."""
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)

    def matricular_usuarios(self, json_file_path):
        """
        Lee usuarios desde un JSON (list[dict]) y ejecuta el flujo de creación/matriculación.
        (Antes recibía CSV; ahora JSON).
        """
        try:
            usuarios = self._leer_json_lista(json_file_path)
            print(f"\nTotal de usuarios a procesar: {len(usuarios)}")
            
            # Inicializar archivo de exitosos si no existe (formato JSON: list de objetos {'username': ...})
            if not os.path.exists(self.ARCHIVO_EXITOSOS):
                self._escribir_json_lista(self.ARCHIVO_EXITOSOS, [])

            for i, row in enumerate(usuarios, 1):
                try:
                    username = row.get('username', '').strip()
                    print(f"\n[{i}/{len(usuarios)}] Procesando usuario: {username}")
                    
                    # Verificar si el usuario ya existe
                    if self.usuario_existe(username):
                        print("⏩ Usuario ya existe, omitiendo...")
                        self.registrar_resultado(row, "fallido", "Usuario ya existente")
                        continue
                        
                    # Crear nuevo usuario
                    try:
                        user_id = self.crear_usuario(row)
                        if not user_id:
                            continue  # El error ya se registró en crear_usuario
                            
                        # Matricular en curso principal (ID=5)
                        if not self.matricular_en_curso(user_id, 5, 5):
                            self.registrar_resultado(row, "fallido", "Error en matriculación")
                            continue
                            
                        # Asignar a grupo/subgrupo si está especificado
                        grupo = row.get('group1', '').strip()
                        if grupo and not self.asignar_a_grupo(user_id, 5, grupo):
                            self.registrar_resultado(row, "fallido", "Error al asignar grupo")
                            continue
                        
                        # Registrar éxito en Google Sheets
                        if not self.registrar_resultado(row, "exitoso", "Matriculación exitosa", grupo):
                            print("⚠️ No se pudo registrar el éxito en Google Sheets, pero el usuario fue creado")
                        
                        # Registrar username en archivo JSON de exitosos
                        self.registrar_exitoso_csv(username)  # mantiene el nombre, ahora escribe JSON
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"⚠️ Error al crear usuario: {error_msg}")
                        self.registrar_resultado(row, "fallido", error_msg)
                        continue
                
                except Exception as e:
                    error_msg = f"Error inesperado: {str(e)}"
                    print(f"⚠️ {error_msg}")
                    self.registrar_resultado(row, "fallido", error_msg)
                    continue
        
        except Exception as e:
            print(f"🚨 Error crítico: {str(e)}")
            raise
        finally:
            print("\n✅ Proceso completado. Revisa los registros en Google Sheets y en el archivo JSON de exitosos")

    def registrar_exitoso_csv(self, username):
        """
        Registrar username en archivo de exitosos **JSON** (antes CSV).
        Se mantiene el nombre del método para no romper llamadas existentes.
        Estructura del JSON: list de objetos {'username': '<valor>'}
        """
        try:
            existentes = self._leer_json_lista(self.ARCHIVO_EXITOSOS)
            # normalizar a lista de dicts con clave 'username'
            norm = []
            for item in existentes:
                if isinstance(item, dict) and 'username' in item:
                    norm.append(item)
                elif isinstance(item, str):
                    norm.append({'username': item})
            existentes = norm

            if any(item.get('username') == username for item in existentes):
                print(f"⏩ Usuario {username} ya registrado en archivo JSON")
                return True
            
            existentes.append({'username': username})
            self._escribir_json_lista(self.ARCHIVO_EXITOSOS, existentes)
            print(f"📝 Registrado {username} en archivo JSON de exitosos")
            return True
        except Exception as e:
            print(f"⚠️ Error al registrar en archivo JSON: {str(e)}")
            return False

    def registrar_resultado(self, row, tipo, motivo, grupo=""):
        """Registrar resultado en Google Sheets con las columnas especificadas (sin cambios)."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        datos = {
            "sheet_id": self.SHEET_ID,
            "tipo": tipo,
            "datos": {
                "Cédula": row.get('username', ''),
                "Nombre Completo": f"{row.get('firstname', '')} {row.get('lastname', '')}",
                "Email": row.get('email', ''),
                "Examen": grupo or row.get('group1', ''),
                "Celular": row.get('phone1', ''),
                "Fecha": fecha,
                "Observaciones": motivo
            }
        }
        
        print(f"Enviando datos a Google Sheets: {json.dumps(datos, indent=2)}")  # Debug
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    self.APPS_SCRIPT_URL,
                    json=datos,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                print(f"Respuesta de Google Apps Script: {response.status_code} - {response.text}")  # Debug
                
                if response.status_code == 200:
                    print(f"📝 Registrado en hoja de {tipo} (Intento {attempt + 1})")
                    return True
                else:
                    print(f"⚠️ Error al registrar (Intento {attempt + 1}): {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Error de conexión (Intento {attempt + 1}): {str(e)}")
            
            if attempt < self.MAX_RETRIES - 1:
                time.sleep(2)
        
        print(f"❌ No se pudo registrar después de {self.MAX_RETRIES} intentos")
        return False

    # --- Resto de métodos SIN CAMBIOS ---
    def usuario_existe(self, username):
        params = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_user_get_users_by_field',
            'field': 'username',
            'values[0]': username,
            'moodlewsrestformat': 'json'
        }
        response = self.session.get(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            params=params,
            headers=self.headers
        )
        users = response.json()
        return isinstance(users, list) and len(users) > 0

    def crear_usuario(self, row):
        campos_personalizados = {
            'profile_field_departamento': 'departamento',
            'profile_field_municipio': 'municipio', 
            'profile_field_modalidad': 'modalidad',
            'profile_field_lote': 'lote'
        }
        campos_requeridos = ['username', 'password', 'firstname', 'lastname', 'email', 'idnumber', 'phone1']
        for campo in campos_requeridos:
            if not row.get(campo, '').strip():
                error_msg = f"Campo requerido faltante: {campo}"
                raise Exception(error_msg)
        
        user_data = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_user_create_users',
            'users[0][username]': row['username'].strip(),
            'users[0][password]': row['password'].strip(),
            'users[0][firstname]': row['firstname'].strip(),
            'users[0][lastname]': row['lastname'].strip(),
            'users[0][email]': row['email'].strip(),
            'users[0][auth]': 'manual',
            'users[0][idnumber]': row['idnumber'].strip(),
            'users[0][phone1]': row['phone1'].strip(),
            'moodlewsrestformat': 'json'
        }
        for i, (csv_field, field_type) in enumerate(campos_personalizados.items()):
            value = row.get(csv_field, '').strip()
            if value:
                user_data[f'users[0][customfields][{i}][type]'] = field_type
                user_data[f'users[0][customfields][{i}][value]'] = value
        
        print("Creando usuario...")
        response = self.session.post(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            data=user_data,
            headers=self.headers
        )
        result = response.json()
        if isinstance(result, list) and result and 'id' in result[0]:
            print(f"✅ Usuario creado con ID: {result[0]['id']}")
            return result[0]['id']
        error_msg = self.extraer_error_moodle(result)
        if "invalid_parameter_exception" in error_msg.lower():
            error_details = self.obtener_detalles_error_parametro(result)
            error_msg = f"Error en parámetros: {error_details}"
        raise Exception(error_msg)
    
    def obtener_detalles_error_parametro(self, response):
        try:
            if isinstance(response, dict):
                debuginfo = response.get('debuginfo', '')
                if debuginfo:
                    import re
                    match = re.search(r'Invalid parameter value detected:(.*?)Key:', debuginfo)
                    if match:
                        return match.group(1).strip()
                return response.get('message', 'Parámetro no válido no especificado')
            return str(response)
        except:
            return "No se pudieron extraer detalles del error de parámetro"
        
    def extraer_error_moodle(self, response):
        if not response:
            return "Respuesta vacía de Moodle"
        if isinstance(response, dict):
            if 'exception' in response:
                error_msg = f"{response.get('exception', '')}: {response.get('message', '')}"
                if 'debuginfo' in response:
                    error_msg += f" (Detalles: {response['debuginfo']})"
                return error_msg
            if 'error' in response:
                return response['error']
        if isinstance(response, list):
            if len(response) > 0 and isinstance(response[0], dict):
                if 'warnings' in response[0]:
                    warnings = response[0]['warnings']
                    if warnings and len(warnings) > 0:
                        return warnings[0].get('message', 'Error desconocido en warnings')
        try:
            return json.dumps(response, indent=2)
        except:
            return str(response)

    def matricular_en_curso(self, user_id, course_id, role_id):
        enrol_data = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'enrol_manual_enrol_users',
            'enrolments[0][roleid]': role_id,
            'enrolments[0][userid]': user_id,
            'enrolments[0][courseid]': course_id,
            'enrolments[0][suspend]': 0,
            'moodlewsrestformat': 'json'
        }
        print(f"Matriculando en curso {course_id}...")
        response = self.session.post(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            data=enrol_data,
            headers=self.headers
        )
        result = response.json()
        if result is None:
            print(f"✅ Matriculado en curso {course_id} con rol {role_id}")
            return True
        print(f"❌ Error en matriculación:", json.dumps(result, indent=2))
        return False

    def asignar_a_grupo(self, user_id, course_id, group_name):
        group_id = self.obtener_id_grupo(course_id, group_name)
        if not group_id:
            print(f"⚠️ Grupo '{group_name}' no encontrado")
            return False
        group_data = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_group_add_group_members',
            'members[0][userid]': user_id,
            'members[0][groupid]': group_id,
            'moodlewsrestformat': 'json'
        }
        print(f"Asignando al grupo '{group_name}'...")
        response = self.session.post(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            data=group_data,
            headers=self.headers
        )
        result = response.json()
        if result is None:
            print(f"✅ Asignado al grupo '{group_name}' (ID: {group_id})")
            return True
        print(f"❌ Error al asignar al grupo:", json.dumps(result, indent=2))
        return False

    def obtener_id_grupo(self, course_id, group_name):
        params = {
            'wstoken': self.MOODLE_TOKEN,
            'wsfunction': 'core_group_get_course_groups',
            'courseid': course_id,
            'moodlewsrestformat': 'json'
        }
        response = self.session.get(
            urljoin(self.MOODLE_URL, 'webservice/rest/server.php'),
            params=params,
            headers=self.headers
        )
        groups = response.json()
        if isinstance(groups, list):
            for group in groups:
                if group['name'] == group_name:
                    return group['id']
        return None


#if __name__ == "__main__":
     #moodle_manager = MoodleManager()
     #moodle_manager.matricular_usuarios('output/resultado_lotes.json')

import os
import json
import pandas as pd

def _leer_json_lista(path):
    """Lee un JSON que contiene una lista de objetos (tolerante a BOM)."""
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("rows", "data", "items"):
            if k in data and isinstance(data[k], list):
                return data[k]
    return []

def _escribir_json_lista(path, rows):
    """Escribe una lista de objetos a JSON (crea carpeta si no existe)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def extraer_columnas_reporte_1003():
    # Leer desde JSON
    src = "output/reporte_1003.json"
    try:
        rows = _leer_json_lista(src)
        df = pd.DataFrame(rows)
    except FileNotFoundError:
        print("❌ No se encontró el archivo 'output/reporte_1003.json'.")
        return
    except Exception as e:
        print(f"❌ Error al leer JSON: {e}")
        return

    # Verificar que las columnas existan
    columnas_necesarias = ["documento_numero", "inscripcion_aprobada"]
    for col in columnas_necesarias:
        if col not in df.columns:
            print(f"⚠️ No se encontró la columna '{col}' en el archivo.")
            return

    # Filtrar solo las columnas necesarias
    df_filtrado = df[columnas_necesarias].copy()

    # Guardar a JSON
    dst = "output/reporte_1003_filtrado.json"
    _escribir_json_lista(dst, df_filtrado.to_dict(orient="records"))
    print("✅ Archivo 'output/reporte_1003_filtrado.json' creado correctamente.")


import json
import pandas as pd

def _norm_doc(x):
    if pd.isna(x):
        return None
    s = str(x).strip().replace(",", "")
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _fmt_grupo(v):
    if pd.isna(v):
        return "Activar"
    s = str(v).strip()
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return str(int(round(f)))
    except:
        return s or "Activar"

def combinar_reportes():
    try:
        # Leer archivos desde JSON
        rows_1003 = _leer_json_lista("output/reporte_1003.json")
        rows_992  = _leer_json_lista("output/reporte_992.json")

        df_1003 = pd.DataFrame(rows_1003)
        df_992  = pd.DataFrame(rows_992)

        # Validar columnas
        columnas_1003 = ["documento_numero", "inscripcion_aprobada"]
        columnas_992  = ["documento_estudiante", "estado_en_ciclo", "grupo"]
        for col in columnas_1003:
            if col not in df_1003.columns:
                print(f"⚠️ Falta columna '{col}' en reporte_1003")
                return
        for col in columnas_992:
            if col not in df_992.columns:
                print(f"⚠️ Falta columna '{col}' en reporte_992")
                return

        # Normalizar claves
        df_1003 = df_1003[columnas_1003].copy()
        df_1003["doc_key"] = df_1003["documento_numero"].apply(_norm_doc)

        df_992 = df_992[columnas_992].copy()
        df_992["doc_key"] = df_992["documento_estudiante"].apply(_norm_doc)

        # Merge tipo BUSCARV
        df_final = pd.merge(
            df_1003,
            df_992[["doc_key", "estado_en_ciclo", "grupo"]],
            on="doc_key",
            how="left"
        ).drop(columns=["doc_key"])

        # Rellenos y formato
        df_final["estado_en_ciclo"] = df_final["estado_en_ciclo"].fillna("Activar")
        df_final["grupo"] = df_final["grupo"].apply(_fmt_grupo)

        # Guardar resultado en JSON
        dst = "output/reporte_1003_combinado.json"
        _escribir_json_lista(dst, df_final.to_dict(orient="records"))
        print("✅ Archivo 'output/reporte_1003_combinado.json' creado correctamente.")

    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")



# ========= ALIASES DE RETRO-COMPATIBILIDAD =========
# Permiten que código viejo que importaba nombres sin la 'j'
# siga funcionando con las nuevas funciones basadas en JSON.

try:
    comparar_documentos_y_generar_faltantes
except NameError:
    def comparar_documentos_y_generar_faltantes(*args, **kwargs):
        # Versión JSON
        return comparar_documentos_y_generar_faltantesj(*args, **kwargs)

try:
    generar_csv_con_informacion
except NameError:
    def generar_csv_con_informacion(*args, **kwargs):
        return generar_csv_con_informacionj(*args, **kwargs)

try:
    verificar_usuarios_individualmente
except NameError:
    def verificar_usuarios_individualmente(*args, **kwargs):
        return verificar_usuarios_individualmentej(*args, **kwargs)

try:
    procesar_archivo
except NameError:
    def procesar_archivo(*args, **kwargs):
        return procesar_archivoj(*args, **kwargs)

try:
    combinar_reportes
except NameError:
    def combinar_reportes(*args, **kwargs):
        return combinar_reportesj(*args, **kwargs)

try:
    extraer_columnas_reporte_1003
except NameError:
    def extraer_columnas_reporte_1003(*args, **kwargs):
        return extraer_columnas_reporte_1003j(*args, **kwargs)



# --- Alias de compatibilidad para código antiguo que esperaba Excel/CSV ---

# Si guardar_excel no existe, lo mapeamos a guardar_json
try:
    guardar_excel
except NameError:
    def guardar_excel(data, nombre_reporte):
        # Conserva la firma original pero guarda en JSON para el nuevo flujo
        # Ej: guardar_excel(resultado, "reporte_1003") -> crea output/reporte_1003.json
        return guardar_json(data, nombre_reporte)

# (Opcional) Si en algún punto se importó json_file_to_excel, lo dejamos como no-op seguro
try:
    json_file_to_excel
except NameError:
    def json_file_to_excel(json_path, output_excel_path):
        # No generamos Excel en Render; solo informamos.
        print(f"ℹ️ json_file_to_excel omitido. Ahora trabajamos solo con JSON. Origen: {json_path}")
        return None
