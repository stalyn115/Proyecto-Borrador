import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // ── URL permanente en Render.com ─────────────────────────────────────────
  // Reemplaza con la URL exacta que te asigne Render si es diferente
  static const String baseUrl = 'https://aguarico-backend.onrender.com';
  // ────────────────────────────────────────────────────────────────────────

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
}
