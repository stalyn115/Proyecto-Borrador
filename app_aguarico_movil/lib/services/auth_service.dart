import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/usuario.dart';

class AuthService {
  /// Login contra POST /login
  /// El backend espera: { "usuario": "...", "clave": "..." }
  /// Usuarios válidos en aguarico_v6.db: admin, staly, aguarico, usuario1
  Future<AuthResult> login(String usuario, String clave) async {
    try {
      final response = await http
          .post(
            Uri.parse(ApiConfig.loginUrl),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'usuario': usuario, 'clave': clave}),
          )
          .timeout(const Duration(seconds: 10));

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && (data['success'] == true || data['token'] != null)) {
        return AuthResult.ok(Usuario.fromJson(data));
      } else {
        final msg = data['mensaje'] ?? data['message'] ?? 'Usuario o clave incorrectos';
        return AuthResult.error(msg.toString());
      }
    } on Exception catch (e) {
      return AuthResult.error('No se pudo conectar con el servidor.\n${e.toString()}');
    }
  }
}

class AuthResult {
  final bool success;
  final Usuario? usuario;
  final String? error;

  AuthResult._({required this.success, this.usuario, this.error});

  factory AuthResult.ok(Usuario u) => AuthResult._(success: true, usuario: u);
  factory AuthResult.error(String msg) => AuthResult._(success: false, error: msg);
}
