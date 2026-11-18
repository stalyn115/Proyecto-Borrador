import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/asistencia.dart';

class AsistenciaService {
  /// Registra asistencia por QR.
  /// POST /asistencia/qr  →  { "codigo": "XXX", "tipo": "entrada" }
  Future<AsistenciaQrResponse> registrarQr({
    required String codigo,
    required String tipo, // 'entrada' o 'salida'
    String? token,
  }) async {
    try {
      final headers = <String, String>{'Content-Type': 'application/json'};
      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }

      final body = AsistenciaQrRequest(codigo: codigo, tipo: tipo).toJson();

      final response = await http
          .post(
            Uri.parse(ApiConfig.asistenciaQrUrl),
            headers: headers,
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 10));

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 || response.statusCode == 201) {
        return AsistenciaQrResponse.fromJson(data);
      } else {
        final msg = data['mensaje'] ?? data['message'] ?? 'Error al registrar asistencia';
        return AsistenciaQrResponse(success: false, mensaje: msg.toString());
      }
    } on Exception catch (e) {
      return AsistenciaQrResponse(
        success: false,
        mensaje: 'Error de conexión: ${e.toString()}',
      );
    }
  }
}
