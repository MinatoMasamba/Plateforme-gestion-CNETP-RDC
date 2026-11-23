import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_controller.dart';

class ApplicationChoiceScreen extends ConsumerWidget {
  const ApplicationChoiceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(authControllerProvider).session;
    final name = session?.fullName ?? '';
    final canCoordinate = session?.canAccessCoordination == true;
    return Scaffold(
      backgroundColor: const Color(0xFFF3F7FA),
      appBar: AppBar(
        title: const Text('CNE-ITP'),
        actions: [
          TextButton.icon(
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
            label: const Text('Se déconnecter'),
          ),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 900),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image.asset('assets/img/logo-cnetp.png', height: 72),
                const SizedBox(height: 24),
                if (name.isNotEmpty) Text('Bienvenue, $name'),
                const SizedBox(height: 8),
                Text(
                  'Choisissez votre application',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 12),
                const Text(
                  'Sélectionnez l’espace dans lequel vous souhaitez travailler.',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final cards = [
                      _ApplicationCard(
                        icon: Icons.edit_document,
                        title: 'Application Expert',
                        description:
                            'Projets de normes, contributions, réunions et suivi personnel.',
                        button: 'Passer à l’application Expert',
                        onPressed: () => context.go('/expert'),
                      ),
                      if (canCoordinate)
                        _ApplicationCard(
                          icon: Icons.account_tree_outlined,
                          title: 'Coordination du Secrétariat technique',
                          description:
                              'Dossiers, coordination, rapports et activités du Secrétariat technique.',
                          button: 'Passer à la Coordination',
                          onPressed: () => context.go('/ctc'),
                        ),
                    ];
                    if (cards.length == 1) return cards.single;
                    if (constraints.maxWidth < 700) {
                      return Column(
                        children: [
                          cards[0],
                          const SizedBox(height: 16),
                          cards[1],
                        ],
                      );
                    }
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: cards[0]),
                        const SizedBox(width: 20),
                        Expanded(child: cards[1]),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ApplicationCard extends StatelessWidget {
  const _ApplicationCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.button,
    required this.onPressed,
  });

  final IconData icon;
  final String title;
  final String description;
  final String button;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: Icon(icon, size: 40, color: const Color(0xFF0095C9)),
          ),
          const SizedBox(height: 20),
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          Text(description),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: onPressed,
            child: Text(button, textAlign: TextAlign.center),
          ),
        ],
      ),
    ),
  );
}
