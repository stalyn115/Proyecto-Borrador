import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // ── URL permanente en Render.com / Local ────────────────────────────────────
  static const String baseUrl = 'https://aguarico-backend.onrender.com';
  // ────────────────────────────────────────────────────────────────────────────

  /// Headers comunes para todas las peticiones
  static Map<String, String> _headers({String? token}) {
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  /// POST genérico — retorna el body decodificado o lanza excepción
  static Future<Map<String, dynamic>> post(
    String endpoint, {
    required Map<String, dynamic> body,
    String? token,
  }) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final response = await http
        .post(uri, headers: _headers(token: token), body: jsonEncode(body))
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  /// GET genérico
  static Future<dynamic> get(String endpoint, {String? token}) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final response = await http
        .get(uri, headers: _headers(token: token))
        .timeout(const Duration(seconds: 15));
    return jsonDecode(response.body);
  }

  // ── Métodos para módulo de Taxi y Botón de Pánico ──────────────────────────

  static Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login'),
        body: {'username': username, 'password': password},
      ).timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<Map<String, dynamic>> conectarTurno({
    required String unidad,
    required String socioNombre,
    required String telefono,
    required double lat,
    required double lng,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/taxi/conectar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'unidad': unidad,
          'socio_nombre': socioNombre,
          'telefono': telefono,
          'latitud': lat,
          'longitud': lng,
        }),
      ).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Error conectarTurno: $e');
    }
    return {'status': 'error'};
  }

  static Future<Map<String, dynamic>> enviarGPS({
    required String unidad,
    required double lat,
    required double lng,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/taxi/gps'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'unidad': unidad,
          'latitud': lat,
          'longitud': lng,
        }),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (_) {}
    return {'status': 'error'};
  }

  static Future<bool> solicitarDesconexion(String unidad) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/taxi/solicitar-desconexion'),
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
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/taxi/alerta'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'unidad': unidad,
          'socio_nombre': socioNombre,
          'latitud': lat,
          'longitud': lng,
        }),
      ).timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> cancelarAlertaPanico(String unidad) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/taxi/cancelar-alerta'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'unidad': unidad}),
      ).timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
