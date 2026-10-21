import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/auth_controller.dart';
import '../../theme/app_colors.dart';

class SpacePlaceholder extends ConsumerWidget {
  const SpacePlaceholder({super.key, required this.title});

  final String title;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: AppColors.page,
      appBar: AppBar(
        backgroundColor: Colors.white,
        title: Text(title),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ref.read(authControllerProvider.notifier).logout();
            },
          ),
        ],
      ),
      body: Center(
        child: Text(
          '$title\n\n(en construction)',
          textAlign: TextAlign.center,
          style: const TextStyle(color: AppColors.muted, fontSize: 16),
        ),
      ),
    );
  }
}
