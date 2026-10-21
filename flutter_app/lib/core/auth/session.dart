/// Session utilisateur reconstruite depuis la réponse de login + bootstrap.
class Session {
  const Session({
    required this.access,
    required this.refresh,
    required this.userId,
    required this.email,
    required this.fullName,
    required this.userType,
    required this.space,
    this.isCtc = false,
    this.isPilotage = false,
    this.ctcRole,
    this.pilotageRole,
  });

  final String access;
  final String refresh;
  final int userId;
  final String email;
  final String fullName;
  final String userType;

  /// Espace de travail cible : `pilotage_directoire`, `pilotage_conseillers`,
  /// `pilotage_atf`, `pilotage`, `ctc`, `expert`, `public`.
  final String space;

  final bool isCtc;
  final bool isPilotage;
  final String? ctcRole;
  final String? pilotageRole;

  Map<String, dynamic> toJson() => {
        'access': access,
        'refresh': refresh,
        'userId': userId,
        'email': email,
        'fullName': fullName,
        'userType': userType,
        'space': space,
        'isCtc': isCtc,
        'isPilotage': isPilotage,
        'ctcRole': ctcRole,
        'pilotageRole': pilotageRole,
      };

  factory Session.fromJson(Map<String, dynamic> json) => Session(
        access: json['access'] as String? ?? '',
        refresh: json['refresh'] as String? ?? '',
        userId: json['userId'] as int? ?? 0,
        email: json['email'] as String? ?? '',
        fullName: json['fullName'] as String? ?? '',
        userType: json['userType'] as String? ?? 'public',
        space: json['space'] as String? ?? 'public',
        isCtc: json['isCtc'] as bool? ?? false,
        isPilotage: json['isPilotage'] as bool? ?? false,
        ctcRole: json['ctcRole'] as String?,
        pilotageRole: json['pilotageRole'] as String?,
      );
}
