import 'package:cnetp_app/core/routing/app_router.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('La bêta bloque les destinations CTC et Pilotage', () {
    for (final space in [
      'ctc',
      'pilotage',
      'pilotage_atf',
      'pilotage_directoire',
      'pilotage_conseillers',
    ]) {
      expect(spacePath(space), '/acces-restreint');
    }
    expect(spacePath('expert'), '/expert');
  });
}
