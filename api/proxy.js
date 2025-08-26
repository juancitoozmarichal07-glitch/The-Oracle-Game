export default async function handler(request, response) {
  // 1. REGISTRAMOS QUE LA PETICIÓN LLEGÓ
  console.log("Proxy contactado. Iniciando proceso.");

  const { targetUrl, body } = await request.json();
  const hfToken = process.env.HF_TOKEN;

  // 2. VERIFICAMOS QUE TENEMOS LA CLAVE
  if (!hfToken) {
    console.error("¡ERROR CRÍTICO! La variable de entorno HF_TOKEN no está configurada en Vercel.");
    return response.status(500).json({ error: "Configuración del servidor incompleta: falta el token." });
  }
  console.log("Token encontrado. Procediendo a llamar a la API de Hugging Face.");

  try {
    const apiResponse = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${hfToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // 3. ANALIZAMOS LA RESPUESTA DE HUGGING FACE
    console.log(`Respuesta recibida de Hugging Face con estado: ${apiResponse.status}`);

    if (!apiResponse.ok) {
      const errorBody = await apiResponse.text();
      console.error("Hugging Face devolvió un error:", errorBody);
      return response.status(apiResponse.status).json({ error: `Error de la API externa: ${errorBody}` });
    }

    const data = await apiResponse.json();
    console.log("Respuesta de la IA procesada con éxito. Devolviendo al juego.");
    return response.status(200).json(data);

  } catch (error) {
    // 4. SI TODO LO DEMÁS FALLA, CAPTURAMOS EL ERROR DE RED
    console.error("¡FALLO CATASTRÓFICO! No se pudo conectar con Hugging Face.", error);
    return response.status(500).json({ 
        error: "Fallo en la conexión del servidor a la API externa.",
        details: error.message 
    });
  }
}
