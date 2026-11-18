/// Configuración de la API del servidor Aguarico
/// Cambia [baseUrl] para apuntar al servidor desplegado en Render.
class ApiConfig {
  // ── URL permanente en Render.com ─────────────────────────────────────────
  // Reemplaza con la URL exacta que te asigne Render si es diferente
    static const String baseUrl = 'https://proyecto-borrador.onrender.com';
  // ────────────────────────────────────────────────────────────────────────

  // Endpoints
  static String get loginUrl => '$baseUrl/login';
  static String get asistenciaQrUrl => '$baseUrl/asistencia/qr';
  static String get sociosUrl => '$baseUrl/socios';
  static String get asistenciasUrl => '$baseUrl/asistencias';
}
