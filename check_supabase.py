import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL") 

key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
# key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


def check_tables():
    try:
        # Verificar torres
        res = supabase.table('torres').select("*").limit(10).execute()
        print(f"Torres: {len(res.data)} registros")
        
        # Verificar datos meteorologicos
        res = supabase.table('datos_meteorologicos').select("*").limit(10).execute()
        print(f"Datos meteorológicos: {len(res.data)} registros")
        for dato in res.data:
            print(f"Torre {dato['id_torre']} - Temp: {dato['temperatura']} - {dato['timestamp']}")
        
        # Verificar diagnosticos
        res = supabase.table('diagnostico_tecnico').select("*").limit(10).execute()
        print(f"Diagnósticos: {len(res.data)} registros")
        
    except Exception as e:
        print(f"Error verificando Supabase: {str(e)}")

if __name__ == "__main__":
    check_tables()