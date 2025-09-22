# ale_core.py (Versión con Depuración para Render)
import traceback # <-- Movido al principio por buena práctica

class ALE_Core:
    def __init__(self):
        self._skillsets = {}
        print("✅ Motor A.L.E. Core v1.0 (Arquitectura Original) inicializado.")

    def cargar_skillset(self, nombre, instancia_skillset):
        self._skillsets[nombre] = instancia_skillset
        print(f"    -> Skillset '{nombre}' cargado en el motor.")

    async def procesar_peticion(self, datos_peticion):
        # ===================================================================
        # ===                MICRÓFONOS DE DEPURACIÓN                   ===
        # ===================================================================
        print("\n--- [ALE_CORE_DEBUG] INICIO DE PETICIÓN ---") # Micrófono 1
        print(f"[ALE_CORE_DEBUG] Datos recibidos: {datos_peticion}") # Micrófono 2
        
        nombre_skillset = datos_peticion.get("skillset_target")
        skillset_seleccionado = self._skillsets.get(nombre_skillset)

        if not skillset_seleccionado:
            print(f"🚨 [ALE_CORE_DEBUG] Skillset '{nombre_skillset}' no encontrado.") # Micrófono 3
            return {"error": f"Skillset '{nombre_skillset}' no encontrado."}
        
        print(f"[ALE_CORE_DEBUG] Skillset '{nombre_skillset}' encontrado. Ejecutando...") # Micrófono 4
        
        try:
            # Simplemente llamamos a la función ejecutar de la instancia
            resultado = await skillset_seleccionado.ejecutar(datos_peticion)
            print("[ALE_CORE_DEBUG] Ejecución completada con éxito.") # Micrófono 5
            return resultado
        except Exception as e:
            # Tu bloque de traceback, que es perfecto, se mantiene.
            print(f"🚨 ERROR CRÍTICO en la ejecución del skillset '{nombre_skillset}':")
            traceback.print_exc() 
            return {"error": f"Error interno en el skillset '{nombre_skillset}': {str(e)}"}

