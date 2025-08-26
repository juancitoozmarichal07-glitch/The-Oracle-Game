export default async function handler(request, response) {
  // El mensajero coge la petición de tu juego
  const { targetUrl, body } = await request.json();
  
  // Y coge la clave secreta de la "caja fuerte" de Vercel
  const hfToken = process.env.HF_TOKEN;

  try {
    // Luego, va a Hugging Face con la clave secreta
    const apiResponse = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${hfToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // Recoge la respuesta de la IA
    const data = await apiResponse.json();
    
    // Y te la devuelve a tu juego
    return response.status(200).json(data);

  } catch (error) {
    // Si algo sale mal, nos avisa
    return response.status(500).json({ error: error.message });
  }
}
