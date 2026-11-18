import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const TaxiSeguroApp());
}

class TaxiSeguroApp extends StatelessWidget {
  const TaxiSeguroApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Taxi Seguro Aguarico',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF0F2746),
        fontFamily: 'Segoe UI',
      ),
      home: const LoginScreen(),
    );
  }
}
