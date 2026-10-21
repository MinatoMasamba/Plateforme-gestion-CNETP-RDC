import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';
import 'session.dart';

enum AuthStatus { unknown, authenticated, unauthenticated, failure }

class AuthState {
  const AuthState({
    this.status = AuthStatus.unknown,
    this.session,
    this.error,
    this.loading = false,
  });

  final AuthStatus status;
  final Session? session;
  final String? error;
  final bool loading;

  AuthState copyWith({
    AuthStatus? status,
    Session? session,
    String? error,
    bool? loading,
    bool clearError = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      session: session ?? this.session,
      error: clearError ? null : (error ?? this.error),
      loading: loading ?? this.loading,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController({AuthState? initialState}) : super(initialState ?? const AuthState()) {
    final s = state.session;
    if (state.status == AuthStatus.authenticated && s != null) {
      ApiClient.accessToken = s.access;
      unawaited(_validateInBackground(s));
    }
  }

  static const _prefsKey = 'cnetp_session';

  /// Charge la session depuis le stockage AVANT le premier rendu (main()).
  /// Élimine la course « unknown → /login » au démarrage.
  static Future<AuthState> loadInitialState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_prefsKey);
      if (raw == null || raw.isEmpty) {
        return const AuthState(status: AuthStatus.unauthenticated);
      }
      final session = Session.fromJson(jsonDecode(raw) as Map<String, dynamic>);
      return AuthState(status: AuthStatus.authenticated, session: session);
    } catch (_) {
      return const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  /// Restaure la session depuis le stockage local et vérifie le bootstrap.
  Future<void> restore() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_prefsKey);
    if (raw == null || raw.isEmpty) {
      state = const AuthState(status: AuthStatus.unauthenticated);
      return;
    }
    Session session;
    try {
      session = Session.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      state = const AuthState(status: AuthStatus.unauthenticated);
      return;
    }
    ApiClient.accessToken = session.access;
    // Optimiste : on route immédiatement à partir de la session stockée,
    // puis on valide/rafraîchit en arrière-plan (évite un blocage sur /splash).
    state = AuthState(status: AuthStatus.authenticated, session: session);
    unawaited(_validateInBackground(session));
  }

  Future<void> _validateInBackground(Session session) async {
    try {
      final boot = await _fetchBootstrap();
      final refreshed = _merge(session, boot);
      await _persist(refreshed);
      if (state.status == AuthStatus.authenticated) {
        state = AuthState(status: AuthStatus.authenticated, session: refreshed);
      }
    } catch (e) {
      // Seules les erreurs d'authentification déclenchent un refresh/logout.
      final isAuthError = e is DioException &&
          (e.response?.statusCode == 401 || e.response?.statusCode == 403);
      if (!isAuthError) return;
      final ok = await _tryRefresh(session);
      if (!ok && state.status == AuthStatus.authenticated) {
        await logout();
      }
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final resp = await ApiClient.dio.post('/api/v1/mobile/auth/login/', data: {
        'email': email,
        'password': password,
        'device_id': 'flutter-web',
        'device_type': 'web',
      });

      final data = resp.data as Map<String, dynamic>;
      if (data['error_code'] == 'EMAIL_NOT_CONFIRMED') {
        throw Exception(data['message'] ?? 'Email non confirmé.');
      }

      final user = (data['user'] as Map<String, dynamic>?) ?? const {};
      final session = Session(
        access: data['access'] as String? ?? '',
        refresh: data['refresh'] as String? ?? '',
        userId: user['id'] as int? ?? 0,
        email: user['email'] as String? ?? '',
        fullName: user['full_name'] as String? ?? '',
        userType: user['user_type'] as String? ?? 'public',
        space: 'public',
      );

      ApiClient.accessToken = session.access;
      final boot = await _fetchBootstrap();
      final merged = _merge(session, boot);
      await _persist(merged);
      state = AuthState(status: AuthStatus.authenticated, session: merged);
    } on DioException catch (e) {
      state = state.copyWith(
        status: AuthStatus.failure,
        error: _readError(e),
        loading: false,
      );
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.failure,
        error: e.toString().replaceFirst('Exception: ', ''),
        loading: false,
      );
    }
  }

  Future<void> logout() async {
    final session = state.session;
    try {
      if (session != null) {
        await ApiClient.dio.post(
          '/api/v1/mobile/auth/logout/',
          data: {'refresh': session.refresh},
        );
      }
    } catch (_) {
      // best effort
    }
    ApiClient.accessToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_prefsKey);
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<Map<String, dynamic>> _fetchBootstrap() async {
    final resp = await ApiClient.dio.get('/api/v1/mobile/auth/bootstrap/');
    return resp.data as Map<String, dynamic>;
  }

  Future<bool> _tryRefresh(Session session) async {
    try {
      final resp = await ApiClient.dio.post(
        '/api/v1/mobile/auth/refresh/',
        data: {'refresh': session.refresh},
      );
      final data = resp.data as Map<String, dynamic>;
      final refreshed = Session(
        access: data['access'] as String? ?? session.access,
        refresh: data['refresh'] as String? ?? session.refresh,
        userId: session.userId,
        email: session.email,
        fullName: session.fullName,
        userType: session.userType,
        space: session.space,
        isCtc: session.isCtc,
        isPilotage: session.isPilotage,
        ctcRole: session.ctcRole,
        pilotageRole: session.pilotageRole,
      );
      ApiClient.accessToken = refreshed.access;
      final boot = await _fetchBootstrap();
      final merged = _merge(refreshed, boot);
      await _persist(merged);
      state = AuthState(status: AuthStatus.authenticated, session: merged);
      return true;
    } catch (_) {
      ApiClient.accessToken = null;
      return false;
    }
  }

  Session _merge(Session session, Map<String, dynamic> bootstrap) {
    return Session(
      access: session.access,
      refresh: session.refresh,
      userId: session.userId,
      email: session.email,
      fullName: session.fullName,
      userType: session.userType,
      space: bootstrap['space'] as String? ?? session.space,
      isCtc: bootstrap['is_ctc'] as bool? ?? session.isCtc,
      isPilotage: bootstrap['is_pilotage'] as bool? ?? session.isPilotage,
      ctcRole: bootstrap['ctc_role'] as String?,
      pilotageRole: bootstrap['pilotage_role'] as String?,
    );
  }

  Future<void> _persist(Session session) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, jsonEncode(session.toJson()));
  }

  String _readError(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['error'] != null) return data['error'].toString();
    if (data is Map && data['detail'] != null) return data['detail'].toString();
    if (e.response?.statusCode == 401) {
      return 'Email ou mot de passe incorrect.';
    }
    return 'Erreur réseau (${e.response?.statusCode ?? '?'}).';
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) => AuthController());
