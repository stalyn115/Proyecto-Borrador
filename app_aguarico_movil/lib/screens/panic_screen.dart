import 'dart:async';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';

class PanicScreen extends StatefulWidget {
  final String unidad;
  final String socioNombre;
  final double lat;
  final double lng;

  const PanicScreen({
    Key? key,
    required this.unidad,
    required this.socioNombre,
    required this.lat,
    required this.lng,
  }) : super(key: key);

  @override
  _PanicScreenState createState() => _PanicScreenState();
}

class _PanicScreenState extends State<PanicScreen> {
  int _secondsLeft = 10;
  Timer? _timer;
  int _cancelPressCount = 0;
  bool _alertaConfirmada = false;

  @override
  void initState() {
    super.initState();
    _startCountdown();
  }

  void _startCountdown() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsLeft > 1) {
        setState(() {
          _secondsLeft--;
        });
      } else {
        _timer?.cancel();
        _confirmarAlertaEmergencia();
      }
    });
  }

  void _cancelarAlerta() async {
    setState(() {
      _cancelPressCount++;
    });

    if (_cancelPressCount >= 2) {
      _timer?.cancel();
      await ApiService.cancelarAlertaPanico(widget.unidad);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Alerta cancelada (Falsa Alarma registrada)'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Presiona 1 vez más para cancelar'),
          duration: Duration(seconds: 1),
        ),
      );
    }
  }

  void _confirmarAlertaEmergencia() async {
    setState(() {
      _alertaConfirmada = true;
    });

    await ApiService.dispararAlertaPanico(
      unidad: widget.unidad,
      socioNombre: widget.socioNombre,
      lat: widget.lat,
      lng: widget.lng,
    );

    // Llamar al 911 o abrir auxilio
    final uri911 = Uri.parse('tel:911');
    if (await canLaunchUrl(uri911)) {
      await launchUrl(uri911);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async => false, // Bloquear salida accidental
      child: Scaffold(
        backgroundColor: _alertaConfirmada ? Colors.black : const Color(0xFFB71C1C),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.warning_amber_rounded,
                  size: 110,
                  color: Colors.white,
                ),
                const SizedBox(height: 16),
                Text(
                  _alertaConfirmada ? '¡ALERTA TRANSMITIDA!' : 'ALERTA DE EMERGENCIA',
                  style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                Text(
                  _alertaConfirmada
                      ? 'La Matriz y grupos de auxilio han recibido tu ubicación GPS en tiempo real.'
                      : 'Transmitiendo auxilio a la Matriz en $_secondsLeft segundos...',
                  style: const TextStyle(fontSize: 16, color: Colors.white70),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 36),
                if (!_alertaConfirmada) ...[
                  Text(
                    '$_secondsLeft',
                    style: const TextStyle(
                      fontSize: 84,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 40),
                  ElevatedButton(
                    onPressed: _cancelarAlerta,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.red.shade900,
                      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(30),
                      ),
                    ),
                    child: Text(
                      _cancelPressCount == 0
                          ? 'CANCELAR (Toca 2 veces)'
                          : '¡TOCA OTRA VEZ!',
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                  ),
                ] else ...[
                  ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                    },
                    icon: const Icon(Icons.check),
                    label: const Text('Volver al Panel'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                    ),
                  )
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
