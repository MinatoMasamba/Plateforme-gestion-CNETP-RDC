import 'package:flutter/foundation.dart';

/// Compteurs de la barre latérale ST (miroir des événements
/// `st-ged-counts` du web : ready / versions / anomalies), alimentés par
/// `CtcGedWorkspace` après chaque chargement de `/api/v1/st/ged/`.
final ValueNotifier<Map<String, int>> gedSidebarCounts =
    ValueNotifier<Map<String, int>>(const {});

void publishGedCounts(Map<String, dynamic>? kpis) {
  int cast(Object? value) => value is num ? value.toInt() : 0;
  gedSidebarCounts.value = kpis == null
      ? const {}
      : {
          'ready': cast(kpis['ready']),
          'versions': cast(kpis['versions_todo']),
          'anomalies': cast(kpis['anomalies']),
        };
}
