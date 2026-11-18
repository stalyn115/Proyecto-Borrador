import 'dart:async';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../services/api_service.dart';
import 'panic_screen.dart';
import 'camouflage_screen.dart';

class HomeScreen extends StatefulWidget {
  final String unidad;
  final String socioNombre;
  final String telefono;

  const HomeScreen({
    Key? key,
    required this.unidad,
    required this.socioNombre,
    required this.telefono,
  }) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _conectado = false;
  bool _esperandoDesconexion = false;
  double _lat = -0.22985;
  double _lng = -78.52495;
  Timer? _gpsTimer;
  bool _camuflajeActivo = false;

  @override
  void initState() {
    super.initState();
    _iniciarGPS();
  }

  void _iniciarGPS() async {
    try {
      LocationPermission perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.always || perm == LocationPermission.whileInUse) {
        Position pos = await Geolocator.getCurrentPosition();
        setState(() {
          _lat = pos.latitude;
          _lng = pos.longitude;
        });
      }
    } catch (_) {}

    // Enviar GPS periódico cada 6 segundos si está conectado
    _gpsTimer = Timer.periodic(const Duration(seconds: 6), (timer) async {
      if (_conectado) {
        try {
          Position pos = await Geolocator.getCurrentPosition();
          setState(() {
            _lat = pos.latitude;
            _lng = pos.longitude;
          });
        } catch (_) {}

        final resp = await ApiService.enviarGPS(
          unidad: widget.unidad,
          lat: _lat,
          lng: _lng,
        );

        // Si la matriz aprobó la desconexión desde la PC central:
        if (resp['desconexion_aprobada'] == true) {
          setState(() {
            _conectado = false;
            _esperandoDesconexion = false;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('La Matriz ha aprobado tu fin de turno. Desconectado.'),
              backgroundColor: Colors.blue,
            ),
          );
        }
      }
    });
  }

  void _conectarTurno() async {
    final resp = await ApiService.conectarTurno(
      unidad: widget.unidad,
      socioNombre: widget.socioNombre,
      telefono: widget.telefono,
      lat: _lat,
      lng: _lng,
    );

    if (resp['status'] == 'ok') {
      setState(() {
        _conectado = true;
        _esperandoDesconexion = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Turno conectado. GPS transmitiendo a la Matriz.'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  void _solicitarDesconexion() async {
    final ok = await ApiService.solicitarDesconexion(widget.unidad);
    if (ok) {
      setState(() {
        _esperandoDesconexion = true;
      });
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: const Color(0xFF162D50),
          title: const Text('Solicitud Enviada a la Matriz', style: TextStyle(color: Colors.white)),
          content: const Text(
            'Para tu seguridad, la aplicación requiere autorización de la Matriz para desconectarse.\n\nPor favor espera la confirmación del operador central.',
            style: TextStyle(color: Colors.white70),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Entendido', style: TextStyle(color: Colors.orange)),
            ),
          ],
        ),
      );
    }
  }

  void _activarPanico() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => PanicScreen(
          unidad: widget.unidad,
          socioNombre: widget.socioNombre,
          lat: _lat,
          lng: _lng,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _gpsTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_camuflajeActivo) {
      return CamouflageScreen(
        onTriggerSilentPanic: () {
          ApiService.dispararAlertaPanico(
            unidad: widget.unidad,
            socioNombre: widget.socioNombre,
            lat: _lat,
            lng: _lng,
          );
        },
        onExitCamouflage: () {
          setState(() {
            _camuflajeActivo = false;
          });
        },
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0F2746),
      appBar: AppBar(
        backgroundColor: const Color(0xFF162D50),
        title: Text('${widget.unidad} — ${widget.socioNombre}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.calculate_outlined),
            tooltip: 'Activar Modo Camuflaje',
            onPressed: () {
              setState(() {
                _camuflajeActivo = true;
              });
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Estado de Conexión
              Card(
                color: const Color(0xFF1E3A5F),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(18.0),
                  child: Row(
                    children: [
                      Icon(
                        _conectado ? Icons.wifi : Icons.wifi_off,
                        color: _conectado ? Colors.greenAccent : Colors.redAccent,
                        size: 38,
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _conectado
                                  ? (_esperandoDesconexion ? 'ESPERANDO AUTORIZACIÓN MATRIZ' : 'EN SERVICIO / CONECTADO')
                                  : 'FUERA DE TURNO (DESCONECTADO)',
                              style: TextStyle(
                                color: _conectado
                                    ? (_esperandoDesconexion ? Colors.orange : Colors.greenAccent)
                                    : Colors.redAccent,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'GPS: ${_lat.toStringAsFixed(5)}, ${_lng.toStringAsFixed(5)}',
                              style: const TextStyle(color: Colors.white70, fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Botones de Conectar / Desconectar
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _conectado ? null : _conectarTurno,
                      icon: const Icon(Icons.play_arrow),
                      label: const Text('CONECTAR'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green.shade700,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: !_conectado || _esperandoDesconexion ? null : _solicitarDesconexion,
                      icon: const Icon(Icons.stop),
                      label: Text(_esperandoDesconexion ? 'SOLICITADO...' : 'DESCONECTAR'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange.shade800,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                    ),
                  ),
                ],
              ),

              const Spacer(),

              // BOTÓN DE PÁNICO
              Center(
                child: GestureDetector(
                  onTap: _activarPanico,
                  child: Container(
                    width: 210,
                    height: 210,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const RadialGradient(
                        colors: [Color(0xFFFF1744), Color(0xFFB71C1C)],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.red.withOpacity(0.5),
                          blurRadius: 30,
                          spreadRadius: 8,
                        ),
                      ],
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: const [
                        Icon(Icons.warning_rounded, size: 72, color: Colors.white),
                        SizedBox(height: 8),
                        Text(
                          'PÁNICO',
                          style: TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            letterSpacing: 2,
                          ),
                        ),
                        Text(
                          'Toca en peligro',
                          style: TextStyle(color: Colors.white70, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const Spacer(),

              // Botón rápido modo oculto
              OutlinedButton.icon(
                onPressed: () {
                  setState(() {
                    _camuflajeActivo = true;
                  });
                },
                icon: const Icon(Icons.visibility_off_outlined, color: Colors.white70),
                label: const Text(
                  'ACTIVAR PANTALLA CAMUFLADA (CALCULADORA)',
                  style: TextStyle(color: Colors.white70),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Colors.white24),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }
}
