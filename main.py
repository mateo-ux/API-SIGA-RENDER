import os
from dotenv import load_dotenv
from api_siga import ApiSigaClient
from api_siga.services import SigaServices
from api_siga.utils import MoodleManager, combinar_reportes, comparar_documentos_y_generar_faltantes, extraer_columnas_reporte_1003, generar_csv_con_informacion, print_json_bonito, guardar_excel, procesar_archivo, verificar_usuarios_individualmente

def main():
    load_dotenv()

    BASE_URL = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRETO = os.getenv("SECRETO")
    USERNAME = os.getenv("USERNAME_PRUEBA")
    PASSWORD = os.getenv("PASSWORD_PRUEBA")

    cliente = ApiSigaClient(BASE_URL, CLIENT_ID, SECRETO)
    access_token = cliente.generar_token()

    if not access_token:
        print("❌ No se pudo obtener el token de acceso.")
        return

    # Autenticación (con MultipartEncoder ya funcionando)
    from requests_toolbelt.multipart.encoder import MultipartEncoder
    import requests

    url_autenticar = f"{BASE_URL}/talentotech2/autenticar"
    headers = {"auth_token": access_token}
    data = MultipartEncoder(fields={"username": USERNAME, "password": PASSWORD})
    headers["Content-Type"] = data.content_type

    try:
        response = requests.post(url_autenticar, headers=headers, data=data)
        response.raise_for_status()
        auth_response = response.json()
    except Exception as e:
        print("❌ Error al autenticar:", e)
        return

    if auth_response.get("RESPUESTA") != "1":
        print("❌ Error al autenticar:", auth_response)
        return

    token_autenticacion = auth_response.get("TOKEN")
    print("✅ Autenticación correcta.")

    services = SigaServices(cliente)

    # Menú
    while True:
        print("\n🔍 Reporte a consultar?")
        print("1. Reporte 622 - Información académica detallada")
        print("2. Reporte 1003 - Lista de estudiantes")
        print("3. Reporte 775 - Detalle matrícula")
        print("4. Reporte 997 - Inscripciones por año")
        print("5. Reporte 992 - Matriculados por periodo")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()

        if opcion == "0":
            break
        elif opcion == "1":
            resultado = services.consultar_reporte_622(access_token, token_autenticacion, periodo=2025011112)
            guardar_excel(resultado, "reporte_622")
        elif opcion == "2":
            # Solo cuando se selecciona la opción 2 se obtiene el reporte 1003 y los estudiantes de Moodle
            resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
            guardar_excel(resultado, "reporte_1003")
            
            # Generar CSV de los datos de Moodle
            generar_csv_con_informacion("output/reporte_1003.xlsx")

            #validacion interna 
            comparar_documentos_y_generar_faltantes()
            
            verificar_usuarios_individualmente()
            
            # Ejemplo de uso: pasar la ruta del archivo CSV
            procesar_archivo('output/usuarios_no_matriculados.csv', moodle_manager=None)


            moodle_manager = MoodleManager()
            moodle_manager.matricular_usuarios('output/resultado_lotes.csv')
        elif opcion == "3":
            resultado = services.consultar_reporte_775(access_token, token_autenticacion, periodo=2025011112)
            guardar_excel(resultado, "reporte_775")
        elif opcion == "4":
            resultado = services.consultar_reporte_997(access_token, token_autenticacion, ano_periodo=2025)
            guardar_excel(resultado, "reporte_997")
        elif opcion == "5":
            resultado = services.consultar_reporte_1003(access_token, token_autenticacion)
            guardar_excel(resultado, "reporte_1003")
            resultado = services.consultar_reporte_992(access_token, token_autenticacion, cod_periodo_academico=2025011112)
            guardar_excel(resultado, "reporte_992")
            extraer_columnas_reporte_1003()
            combinar_reportes()
        else:
            print("❌ Opción inválida.")

if __name__ == "__main__":
    main()
