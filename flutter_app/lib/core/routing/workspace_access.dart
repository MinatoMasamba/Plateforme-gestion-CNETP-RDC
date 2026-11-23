import '../auth/session.dart';

String spacePath(String space) =>
    space == 'expert' ? '/expert' : '/choisir-application';

/// Filtre d'interface ; les API restent responsables des autorisations métier.
String? coordinationAccessRedirect(Session? session, String location) {
  if (session?.canAccessCoordination == true) return null;
  if (location == '/ctc' || location.startsWith('/ctc/')) {
    return spacePath(session?.space ?? 'public');
  }
  if ((location == '/choisir-application' || location == '/acces-restreint') &&
      session?.space == 'expert') {
    return '/expert';
  }
  return null;
}
