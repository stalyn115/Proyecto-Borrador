import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Cambia esta URL por la IP de tu PC o tu servidor Render
  static const String baseUrl = 'http://172.17.209.212:8000';

  static Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login'),
        body: {'username': username, 'password': password},
      ).timeout(const Duration(seconds: 5));
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
      ).timeout(const Duration(seconds: 5));
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
      ).timeout(const Duration(seconds: 4));
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
      ).timeout(const Duration(seconds: 5));
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
      ).timeout(const Duration(seconds: 5));
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
      ).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
