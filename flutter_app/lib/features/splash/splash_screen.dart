import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          const Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: SizedBox(
              height: 4,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(child: ColoredBox(color: AppColors.rdcBlue)),
                  Expanded(child: ColoredBox(color: AppColors.rdcYellow)),
                  Expanded(child: ColoredBox(color: AppColors.rdcRed)),
                ],
              ),
            ),
          ),
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image.asset('assets/img/logo-cnetp.png', width: 64, height: 64),
                const SizedBox(height: 18),
                const SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(strokeWidth: 2.4, color: AppColors.rdcBlue),
                ),
                const SizedBox(height: 14),
                const Text('Chargement de votre espace…',
                    style: TextStyle(fontSize: 12, color: AppColors.muted)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
