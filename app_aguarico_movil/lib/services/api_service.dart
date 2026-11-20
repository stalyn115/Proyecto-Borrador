import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

/// Servicio de red con resolución automática de URL.
///
/// Lógica de prioridad:
///   1. Intenta la IP local configurada (misma red WiFi de la oficina) — más rápido
///   2. Si falla o tarda más de 3 s, usa Render.com (internet público)
///
/// Esto permite que el APK funcione desde CUALQUIER red sin recompilar.
class ApiService {
  // ── URLs ──────────────────────────────────────────────────────────────────
  /// Servidor Render (internet público — siempre disponible si está desplegado)
  static const String _urlRender = 'https://proyecto-borrador.onrender.com';

  /// IP local del servidor (misma red WiFi).
  /// Cámbiala aquí si la IP de tu PC cambia, o deja que el fallback lo maneje.
  static const String _urlLocal  = 'http://192.168.100.37:8000';

  /// URL activa — se resuelve en el primer uso y se cachea.
  static String? _baseUrlCache;

  // ── Resolución de URL ─────────────────────────────────────────────────────
  /// Devuelve la URL del servidor más rápida disponible.
  static Future<String> get baseUrl async {
    if (_baseUrlCache != null) return _baseUrlCache!;
    _baseUrlCache = await _resolverUrl();
    return _baseUrlCache!;
  }

  /// Fuerza re-detección en el próximo uso (útil si cambia la red).
  static void resetUrl() => _baseUrlCache = null;

  static Future<String> _resolverUrl() async {
    // Intenta la IP local con timeout corto
    try {
      final resp = await http
          .get(Uri.parse('$_urlLocal/'))
          .timeout(const Duration(seconds: 3));
      if (resp.statusCode < 500) return _urlLocal;
    } catch (_) {}
    // Fallback a Render
    return _urlRender;
  }

  // ── Headers comunes ───────────────────────────────────────────────────────
  static Map<String, String> _headers({String? token}) {
    final h = <String, String>{'Content-Type': 'application/json'};
    if (token != null && token.isNotEmpty) h['Authorization'] = 'Bearer $token';
    return h;
  }

  // ── POST / GET genéricos ──────────────────────────────────────────────────
  static Future<Map<String, dynamic>> post(
    String endpoint, {
    required Map<String, dynamic> body,
    String? token,
  }) async {
    final url = await baseUrl;
    final uri = Uri.parse('$url$endpoint');
    final response = await http
        .post(uri, headers: _headers(token: token), body: jsonEncode(body))
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<dynamic> get(String endpoint, {String? token}) async {
    final url = await baseUrl;
    final uri = Uri.parse('$url$endpoint');
    final response = await http
        .get(uri, headers: _headers(token: token))
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body);
  }

  // ── Login ─────────────────────────────────────────────────────────────────
  static Future<bool> login(String username, String password) async {
    final url = await baseUrl;
    try {
      final response = await http.post(
        Uri.parse('$url/login'),
        body: {'username': username, 'password': password},
      ).timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ── Módulo Taxi / GPS ─────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> conectarTurno({
    required String unidad,
    required String socioNombre,
    required String telefono,
    required double lat,
    required double lng,
  }) async {
    final url = await baseUrl;
    try {
      final response = await http.post(
        Uri.parse('$url/taxi/conectar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'unidad': unidad,
          'socio_nombre': socioNombre,
          'telefono': telefono,
          'latitud': lat,
          'longitud': lng,
        }),
      ).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) return jsonDecode(response.body);
    } catch (e) {
      // Si falla (cambio de red), resetear URL y reintentar con Render
      resetUrl();
      try {
        final response = await http.post(
          Uri.parse('$_urlRender/taxi/conectar'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'unidad': unidad,
            'socio_nombre': socioNombre,
            'telefono': telefono,
            'latitud': lat,
            'longitud': lng,
          }),
        ).timeout(const Duration(seconds: 10));
        if (response.statusCode == 200) {
          _baseUrlCache = _urlRender;
          return jsonDecode(response.body);
        }
      } catch (_) {}
    }
    return {'status': 'error'};
  }

  static Future<Map<String, dynamic>> enviarGPS({
    required String unidad,
    required double lat,
    required double lng,
  }) async {
    final url = await baseUrl;
    try {
      final response = await http.post(
        Uri.parse('$url/taxi/gps'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'unidad': unidad, 'latitud': lat, 'longitud': lng}),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) return jsonDecode(response.body);
    } catch (_) {
      resetUrl();   // Próxima llamada re-detecta la red
    }
    return {'status': 'error'};
  }

  static Future<bool> solicitarDesconexion(String unidad) async {
    final url = await baseUrl;
    try {
      final response = await http.post(
        Uri.parse('$url/taxi/solicitar-desconexion'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'unidad': unidad}),
      ).timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> dispararAlertaPanico({
    required String unidad,
    required String socioNombre,
    required double lat,
    required double lng,
  }) async {
    // La alerta SOS siempre intenta AMBAS URLs en paralelo para máxima fiabilidad
    final futures = [_urlLocal, _urlRender].map((base) async {
      try {
        final r = await http.post(
          Uri.parse('$base/taxi/alerta'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'unidad': unidad,
            'socio_nombre': socioNombre,
            'latitud': lat,
            'longitud': lng,
          }),
        ).timeout(const Duration(seconds: 6));
        return r.statusCode == 200;
      } catch (_) {
        return false;
      }
    }).toList();

    final results = await Future.wait(futures);
    return results.any((ok) => ok);
  }

  static Future<bool> cancelarAlertaPanico(String unidad) async {
    final url = await baseUrl;
    try {
      final response = await http.post(
        Uri.parse('$url/taxi/cancelar-alerta'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'unidad': unidad}),
      ).timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
