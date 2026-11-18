import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/usuario.dart';
import '../services/auth_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _service = AuthService();

  Usuario? _usuario;
  bool _cargando = false;
  String? _error;

  Usuario? get usuario => _usuario;
  bool get cargando => _cargando;
  String? get error => _error;
  bool get autenticado => _usuario != null;
  String get token => _usuario?.token ?? '';

  Future<bool> login(String usuario, String clave) async {
    _cargando = true;
    _error = null;
    notifyListeners();

    final result = await _service.login(usuario, clave);

    _cargando = false;
    if (result.success) {
      _usuario = result.usuario;
      // Guardar token localmente
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('token', _usuario!.token);
      await prefs.setString('usuario', _usuario!.usuario);
    } else {
      _error = result.error;
    }
    notifyListeners();
    return result.success;
  }

  Future<void> logout() async {
    _usuario = null;
    _error = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('usuario');
    notifyListeners();
  }

  /// Intenta restaurar sesión desde SharedPreferences
  Future<void> restaurarSesion() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final user = prefs.getString('usuario');
    if (token != null && token.isNotEmpty && user != null) {
      _usuario = Usuario(id: 0, usuario: user, rol: 'usuario', token: token);
      notifyListeners();
    }
  }
}
