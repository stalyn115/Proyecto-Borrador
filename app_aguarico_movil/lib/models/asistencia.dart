class AsistenciaQrRequest {
  final String codigo;
  final String tipo; // 'entrada' | 'salida'

  AsistenciaQrRequest({required this.codigo, required this.tipo});

  Map<String, dynamic> toJson() => {
        'codigo': codigo,
        'tipo': tipo,
      };
}

class AsistenciaQrResponse {
  final bool success;
  final String mensaje;
  final String? nombreSocio;
  final String? hora;

  AsistenciaQrResponse({
    required this.success,
    required this.mensaje,
    this.nombreSocio,
    this.hora,
  });

  factory AsistenciaQrResponse.fromJson(Map<String, dynamic> json) {
    return AsistenciaQrResponse(
      success: json['success'] ?? false,
      mensaje: json['mensaje'] ?? json['message'] ?? '',
      nombreSocio: json['nombre_socio'],
      hora: json['hora'],
    );
  }
}
