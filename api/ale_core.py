# ale_core.py (Construido desde Cero)
class ALE_Core:
    def __init__(self):
        self._skillsets = {}
        print("✅ Motor A.L.E. Core v1.0 (Arquitectura Original) inicializado.")

    def cargar_skillset(self, nombre, instancia_skillset):
        self._skillsets[nombre] = instancia_skillset
        print(f"    -> Skillset '{nombre}' cargado en el motor.")

    async def procesar_peticion(self, datos_peticion):
        nombre_skillset = datos_peticion.get("skillset_target")
        skillset_seleccionado = self._skillsets.get(nombre_skillset)

        if not skillset_seleccionado:
            return {"error": f"Skillset '{nombre_skillset}' no encontrado."}
        
        try:
            # Simplemente llamamos a la función ejecutar de la instancia
            resultado = await skillset_seleccionado.ejecutar(datos_peticion)
            return resultado
        except Exception as e:
            import traceback
            print(f"🚨 ERROR CRÍTICO en la ejecución del skillset '{nombre_skillset}':")
            traceback.print_exc() # Imprime el error completo para un mejor diagnóstico
            return {"error": f"Error interno en el skillset '{nombre_skillset}': {str(e)}"}
