import 'dart:async';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
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
  Timer? _countdownTimer;
  Timer? _gpsTimer;
  int _cancelPressCount = 0;
  bool _alertaConfirmada = false;

  // GPS en tiempo real durante la alerta
  double _lat = 0;
  double _lng = 0;

  @override
  void initState() {
    super.initState();
    _lat = widget.lat;
    _lng = widget.lng;
    _startCountdown();
    _iniciarGPSTiempoReal();
  }

  // ── GPS en tiempo real ────────────────────────────────────────────────
  void _iniciarGPSTiempoReal() {
    // Actualizar posición cada 4 segundos mientras la alerta esté activa
    _gpsTimer = Timer.periodic(const Duration(seconds: 4), (_) async {
      try {
        final pos = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
        );
        if (mounted) {
          setState(() {
            _lat = pos.latitude;
            _lng = pos.longitude;
          });
        }
        // Si la alerta ya fue confirmada, seguir enviando posición actualizada
        if (_alertaConfirmada) {
          await ApiService.dispararAlertaPanico(
            unidad: widget.unidad,
            socioNombre: widget.socioNombre,
            lat: _lat,
            lng: _lng,
          );
        }
      } catch (_) {}
    });
  }

  // ── Cuenta regresiva ──────────────────────────────────────────────────
  void _startCountdown() {
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsLeft > 1) {
        setState(() => _secondsLeft--);
      } else {
        _countdownTimer?.cancel();
        _confirmarAlertaEmergencia();
      }
    });
  }

  void _cancelarAlerta() async {
    setState(() => _cancelPressCount++);

    if (_cancelPressCount >= 2) {
      _countdownTimer?.cancel();
      _gpsTimer?.cancel();
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
    setState(() => _alertaConfirmada = true);

    await ApiService.dispararAlertaPanico(
      unidad: widget.unidad,
      socioNombre: widget.socioNombre,
      lat: _lat,
      lng: _lng,
    );

    // Llamar al 911
    final uri911 = Uri.parse('tel:911');
    if (await canLaunchUrl(uri911)) {
      await launchUrl(uri911);
    }
  }

  // ── Abrir mapa con ubicación actual ──────────────────────────────────
  Future<void> _abrirMiUbicacion() async {
    // Intentar obtener posición más reciente antes de abrir
    try {
      final pos = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      ).timeout(const Duration(seconds: 3));
      _lat = pos.latitude;
      _lng = pos.longitude;
    } catch (_) {}

    final uri = Uri.parse(
      'https://www.google.com/maps/search/?api=1&query=$_lat,$_lng',
    );
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _compartirUbicacion() async {
    final uri = Uri.parse(
      'https://www.google.com/maps/search/?api=1&query=$_lat,$_lng',
    );
    // Compartir por WhatsApp con el link de ubicación
    final msg = Uri.encodeComponent(
      '🚨 ALERTA SOS — ${widget.unidad} — ${widget.socioNombre}\n'
      'Ubicación: https://www.google.com/maps/search/?api=1&query=$_lat,$_lng',
    );
    final wa = Uri.parse('whatsapp://send?text=$msg');
    if (await canLaunchUrl(wa)) {
      await launchUrl(wa, mode: LaunchMode.externalApplication);
    } else if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _gpsTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async => false,
      child: Scaffold(
        backgroundColor: _alertaConfirmada ? Colors.black : const Color(0xFFB71C1C),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.warning_amber_rounded,
                  size: 90,
                  color: Colors.white,
                ),
                const SizedBox(height: 12),
                Text(
                  _alertaConfirmada ? '¡ALERTA TRANSMITIDA!' : 'ALERTA DE EMERGENCIA',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  _alertaConfirmada
                      ? 'La Matriz recibe tu GPS en tiempo real.'
                      : 'Transmitiendo a la Matriz en $_secondsLeft segundos...',
                  style: const TextStyle(fontSize: 15, color: Colors.white70),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 14),

                // ── Tarjeta de ubicación GPS ──────────────────────────
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.black26,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.location_on, color: Colors.greenAccent, size: 18),
                          const SizedBox(width: 6),
                          Text(
                            'GPS: ${_lat.toStringAsFixed(5)}, ${_lng.toStringAsFixed(5)}',
                            style: const TextStyle(
                                color: Colors.greenAccent,
                                fontSize: 13,
                                fontFamily: 'monospace'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: _abrirMiUbicacion,
                              icon: const Icon(Icons.map, size: 18),
                              label: const Text('Ver en mapa', style: TextStyle(fontSize: 13)),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.blue.shade800,
                                padding: const EdgeInsets.symmetric(vertical: 10),
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: _compartirUbicacion,
                              icon: const Icon(Icons.share, size: 18),
                              label: const Text('Compartir', style: TextStyle(fontSize: 13)),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green.shade800,
                                padding: const EdgeInsets.symmetric(vertical: 10),
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // ── Cuenta regresiva o confirmación ───────────────────
                if (!_alertaConfirmada) ...[
                  Text(
                    '$_secondsLeft',
                    style: const TextStyle(
                      fontSize: 76,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _cancelarAlerta,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.red.shade900,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 28, vertical: 16),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30)),
                    ),
                    child: Text(
                      _cancelPressCount == 0
                          ? 'CANCELAR (Toca 2 veces)'
                          : '¡TOCA OTRA VEZ!',
                      style: const TextStyle(
                          fontSize: 17, fontWeight: FontWeight.bold),
                    ),
                  ),
                ] else ...[
                  const Text(
                    'Enviando ubicación cada 4 segundos a la Matriz.',
                    style: TextStyle(color: Colors.white60, fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.check),
                    label: const Text('Volver al Panel'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 24, vertical: 14),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
