class Usuario {
  final int id;
  final String usuario;
  final String rol;
  final String token;

  Usuario({
    required this.id,
    required this.usuario,
    required this.rol,
    required this.token,
  });

  factory Usuario.fromJson(Map<String, dynamic> json) {
    return Usuario(
      id: json['id'] ?? 0,
      usuario: json['usuario'] ?? '',
      rol: json['rol'] ?? 'usuario',
      token: json['token'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'usuario': usuario,
        'rol': rol,
        'token': token,
      };
}
