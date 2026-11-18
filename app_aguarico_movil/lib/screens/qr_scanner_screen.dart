import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/asistencia_service.dart';

class QrScannerScreen extends StatefulWidget {
  const QrScannerScreen({super.key});

  @override
  State<QrScannerScreen> createState() => _QrScannerScreenState();
}

class _QrScannerScreenState extends State<QrScannerScreen> {
  final MobileScannerController _camCtrl = MobileScannerController();
  final AsistenciaService _service = AsistenciaService();

  bool _procesando = false;
  bool _linterna = false;
  String _tipoAsistencia = 'entrada'; // 'entrada' | 'salida'
  String? _ultimoMensaje;
  bool? _ultimoExito;

  @override
  void dispose() {
    _camCtrl.dispose();
    super.dispose();
  }

  Future<void> _toggleLinterna() async {
    await _camCtrl.toggleTorch();
    setState(() => _linterna = !_linterna);
  }

  Future<void> _procesarQr(String codigo) async {
    if (_procesando) return;
    setState(() {
      _procesando = true;
      _ultimoMensaje = null;
    });

    final token = context.read<AuthProvider>().token;
    final resp = await _service.registrarQr(
      codigo: codigo,
      tipo: _tipoAsistencia,
      token: token,
    );

    if (!mounted) return;
    setState(() {
      _procesando = false;
      _ultimoMensaje = resp.nombreSocio != null
          ? '${resp.nombreSocio} — ${resp.mensaje}'
          : resp.mensaje;
      _ultimoExito = resp.success;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_ultimoMensaje!),
        backgroundColor: resp.success ? Colors.green[700] : Colors.red[700],
        duration: const Duration(seconds: 2),
      ),
    );

    await Future.delayed(const Duration(seconds: 2));
    if (mounted) setState(() => _ultimoMensaje = null);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Escanear QR'),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: Icon(_linterna ? Icons.flash_on : Icons.flash_off),
            tooltip: 'Linterna',
            onPressed: _toggleLinterna,
          ),
        ],
      ),
      body: Column(
        children: [
          // Selector entrada / salida
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                const Text('Tipo: ', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Entrada'),
                  selected: _tipoAsistencia == 'entrada',
                  selectedColor: const Color(0xFF1B5E20),
                  labelStyle: TextStyle(
                    color: _tipoAsistencia == 'entrada' ? Colors.white : Colors.black,
                  ),
                  onSelected: (_) => setState(() => _tipoAsistencia = 'entrada'),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Salida'),
                  selected: _tipoAsistencia == 'salida',
                  selectedColor: Colors.orange[700],
                  labelStyle: TextStyle(
                    color: _tipoAsistencia == 'salida' ? Colors.white : Colors.black,
                  ),
                  onSelected: (_) => setState(() => _tipoAsistencia = 'salida'),
                ),
              ],
            ),
          ),

          // Cámara QR
          Expanded(
            child: Stack(
              alignment: Alignment.center,
              children: [
                MobileScanner(
                  controller: _camCtrl,
                  onDetect: (capture) {
                    final barcode = capture.barcodes.firstOrNull;
                    final raw = barcode?.rawValue;
                    if (raw != null && raw.isNotEmpty && !_procesando) {
                      _procesarQr(raw);
                    }
                  },
                ),

                // Marco de escaneo
                Container(
                  width: 240,
                  height: 240,
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.white, width: 2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),

                // Indicador procesando
                if (_procesando)
                  Container(
                    color: Colors.black45,
                    child: const Center(
                      child: CircularProgressIndicator(color: Colors.white),
                    ),
                  ),

                // Resultado
                if (_ultimoMensaje != null)
                  Positioned(
                    bottom: 20,
                    left: 16,
                    right: 16,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: _ultimoExito == true
                            ? Colors.green[700]
                            : Colors.red[700],
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        _ultimoMensaje!,
                        style: const TextStyle(color: Colors.white, fontSize: 15),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
