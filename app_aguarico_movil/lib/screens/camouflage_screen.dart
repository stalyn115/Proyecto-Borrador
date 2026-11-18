import 'package:flutter/material.dart';

class CamouflageScreen extends StatefulWidget {
  final Function onTriggerSilentPanic;
  final Function onExitCamouflage;

  const CamouflageScreen({
    Key? key,
    required this.onTriggerSilentPanic,
    required this.onExitCamouflage,
  }) : super(key: key);

  @override
  _CamouflageScreenState createState() => _CamouflageScreenState();
}

class _CamouflageScreenState extends State<CamouflageScreen> {
  String _display = '0';
  String _currentInput = '';

  void _onBtnPress(String val) {
    setState(() {
      if (val == 'C') {
        _display = '0';
        _currentInput = '';
      } else if (val == '=') {
        // Código secreto para salir de camuflaje
        if (_currentInput == '1234') {
          widget.onExitCamouflage();
          return;
        }
        // Código secreto para disparar alerta de pánico silenciosa
        if (_currentInput == '911' || _currentInput == '9999') {
          widget.onTriggerSilentPanic();
          _display = 'Error';
          _currentInput = '';
          return;
        }

        try {
          // Evaluación matemática simple
          _display = 'Resultado';
        } catch (_) {
          _display = '0';
        }
        _currentInput = '';
      } else {
        if (_display == '0' || _display == 'Error' || _display == 'Resultado') {
          _display = val;
        } else {
          _display += val;
        }
        _currentInput += val;
      }
    });
  }

  Widget _buildCalcBtn(String text, {Color? bg, Color? fg}) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.all(6.0),
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: bg ?? Colors.grey.shade900,
            foregroundColor: fg ?? Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 20),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          ),
          onPressed: () => _onBtnPress(text),
          child: Text(text, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async => false, // No permite salir con botón atrás
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          backgroundColor: Colors.black,
          elevation: 0,
          title: const Text('Calculadora', style: TextStyle(color: Colors.white70, fontSize: 16)),
          automaticallyImplyLeading: false,
        ),
        body: Column(
          children: [
            Expanded(
              child: Container(
                alignment: Alignment.bottomRight,
                padding: const EdgeInsets.all(24),
                child: Text(
                  _display,
                  style: const TextStyle(color: Colors.white, fontSize: 52, fontWeight: FontWeight.w300),
                ),
              ),
            ),
            Row(
              children: [
                _buildCalcBtn('C', bg: Colors.grey.shade800, fg: Colors.orange),
                _buildCalcBtn('+/-', bg: Colors.grey.shade800),
                _buildCalcBtn('%', bg: Colors.grey.shade800),
                _buildCalcBtn('÷', bg: Colors.orange),
              ],
            ),
            Row(
              children: [
                _buildCalcBtn('7'),
                _buildCalcBtn('8'),
                _buildCalcBtn('9'),
                _buildCalcBtn('×', bg: Colors.orange),
              ],
            ),
            Row(
              children: [
                _buildCalcBtn('4'),
                _buildCalcBtn('5'),
                _buildCalcBtn('6'),
                _buildCalcBtn('-', bg: Colors.orange),
              ],
            ),
            Row(
              children: [
                _buildCalcBtn('1'),
                _buildCalcBtn('2'),
                _buildCalcBtn('3'),
                _buildCalcBtn('+', bg: Colors.orange),
              ],
            ),
            Row(
              children: [
                _buildCalcBtn('0'),
                _buildCalcBtn('.'),
                _buildCalcBtn('=', bg: Colors.orange),
              ],
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}
