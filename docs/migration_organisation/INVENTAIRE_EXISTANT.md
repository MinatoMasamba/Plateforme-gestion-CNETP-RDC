# Inventaire technique — préparation de migration CNE-ITP

Date : 12 octobre 2026. Lecture statique du checkout, y compris les modifications locales préexistantes. Base inspectée : `db.sqlite3`, connexion SQLite `mode=ro` et `query_only=ON`. Ce fichier local ne prouve pas l’état de la production ni celui de la base configurée à l’exécution. Aucun nom de personne, secret ou contenu de message n’est exporté.

## 1. Modèles et champs déclarés

Inventaire AST de tous les fichiers `apps/*/models.py`. Les champs hérités de BaseModel sont déclarés une seule fois ; les champs Django hérités de AbstractUser, relations inverses, tables automatiques et contraintes créées exclusivement dans les migrations ne sont pas développés ici. Les expressions sont des déclarations de code, pas des données de la base.

### apps/amendments/models.py

#### Amendement — ligne 7

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.ForeignKey` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='amendements' |
| `version` | `models.ForeignKey` | cible/arguments : NormeVersion; on_delete=models.CASCADE; related_name='amendements' |
| `proposed_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.PROTECT; related_name='amendements_proposed' |
| `title` | `models.CharField` | max_length=300 |
| `description` | `models.TextField` | — |
| `section` | `models.CharField` | max_length=100 |
| `old_text` | `models.TextField` | — |
| `proposed_text` | `models.TextField` | — |
| `justification` | `models.TextField` | — |
| `status` | `models.CharField` | max_length=20 |
| `proposal_date` | `models.DateTimeField` | — |
| `review_deadline` | `models.DateTimeField` | null=True |

- Meta `indexes` : `[models.Index(fields=['norme', 'status']), models.Index(fields=['status', 'proposal_date'])]`.

#### Vote — ligne 59

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `amendement` | `models.ForeignKey` | cible/arguments : Amendement; on_delete=models.CASCADE; related_name='votes' |
| `voter` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.PROTECT; related_name='amendement_votes' |
| `vote` | `models.CharField` | max_length=10 |
| `justification` | `models.TextField` | — |
| `vote_date` | `models.DateTimeField` | — |

- Meta `unique_together` : `('amendement', 'voter')`.

#### ResultatVote — ligne 93

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `amendement` | `models.OneToOneField` | cible/arguments : Amendement; on_delete=models.CASCADE; related_name='resultat_vote' |
| `total_votes` | `models.PositiveIntegerField` | — |
| `votes_for` | `models.PositiveIntegerField` | — |
| `votes_against` | `models.PositiveIntegerField` | — |
| `votes_abstain` | `models.PositiveIntegerField` | — |
| `quorum_reached` | `models.BooleanField` | — |
| `approval_percentage` | `models.DecimalField` | — |
| `vote_closed_at` | `models.DateTimeField` | null=True |


### apps/core/models.py

#### User — ligne 8

Bases : `AbstractUser`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `phone` | `models.CharField` | null=True; max_length=20 |
| `province` | `models.CharField` | null=True; max_length=100 |
| `profile_picture` | `models.ImageField` | null=True; upload_to='profiles/' |
| `is_expert` | `models.BooleanField` | — |
| `is_ctc_staff` | `models.BooleanField` | — |
| `is_minister` | `models.BooleanField` | — |
| `bio` | `models.TextField` | null=True |
| `email_confirmed` | `models.BooleanField` | — |
| `created_at` | `models.DateTimeField` | — |
| `updated_at` | `models.DateTimeField` | — |


#### BaseModel — ligne 31

Bases : `models.Model`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `created_at` | `models.DateTimeField` | — |
| `updated_at` | `models.DateTimeField` | — |
| `created_by` | `models.ForeignKey` | cible/arguments : User; on_delete=models.SET_NULL; null=True; related_name='%(class)s_created_by' |
| `updated_by` | `models.ForeignKey` | cible/arguments : User; on_delete=models.SET_NULL; null=True; related_name='%(class)s_updated_by' |

- Meta `abstract` : `True`.

#### AuditLog — ligne 54

Bases : `models.Model`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.ForeignKey` | cible/arguments : User; on_delete=models.SET_NULL; null=True |
| `action` | `models.CharField` | max_length=20 |
| `content_type` | `models.CharField` | max_length=100 |
| `object_id` | `models.PositiveIntegerField` | — |
| `object_repr` | `models.CharField` | max_length=200 |
| `changes` | `models.JSONField` | — |
| `ip_address` | `models.GenericIPAddressField` | null=True |
| `user_agent` | `models.TextField` | — |
| `timestamp` | `models.DateTimeField` | — |

- Meta `indexes` : `[models.Index(fields=['content_type', 'object_id']), models.Index(fields=['user', 'timestamp'])]`.

#### PasswordResetCode — ligne 89

Bases : `models.Model`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.ForeignKey` | cible/arguments : User; on_delete=models.CASCADE; related_name='reset_codes' |
| `code` | `models.CharField` | max_length=6 |
| `created_at` | `models.DateTimeField` | — |
| `expires_at` | `models.DateTimeField` | — |
| `is_used` | `models.BooleanField` | — |
| `attempts` | `models.PositiveSmallIntegerField` | — |


### apps/documents/models.py

#### DocumentFile — ligne 8

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `uploaded_by` | `models.ForeignKey` | cible/arguments : User; on_delete=models.CASCADE; related_name='uploaded_documents' |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE; null=True; related_name='expert_documents' |
| `file` | `models.FileField` | upload_to='documents/%Y/%m/' |
| `title` | `models.CharField` | max_length=255 |
| `description` | `models.TextField` | null=True |
| `file_type` | `models.CharField` | max_length=50 |
| `category` | `models.CharField` | null=True; max_length=100 |
| `norme` | `models.ForeignKey` | cible/arguments : 'norms.Norme'; on_delete=models.CASCADE; null=True; related_name='documents' |
| `reunion` | `models.ForeignKey` | cible/arguments : 'meetings.Reunion'; on_delete=models.CASCADE; null=True; related_name='documents' |
| `is_public` | `models.BooleanField` | — |
| `file_size` | `models.BigIntegerField` | — |
| `mime_type` | `models.CharField` | max_length=100 |

- Meta `indexes` : `[models.Index(fields=['uploaded_by', '-created_at']), models.Index(fields=['norme', '-created_at']), models.Index(fields=['reunion', '-created_at']), models.Index(fields=['is_public'])]`.

### apps/experts/models.py

#### Structure — ligne 5

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `name` | `models.CharField` | unique=True; max_length=200 |
| `acronym` | `models.CharField` | max_length=50 |
| `description` | `models.TextField` | — |
| `category` | `models.CharField` | max_length=50 |
| `email` | `models.EmailField` | — |
| `phone` | `models.CharField` | max_length=20 |
| `address` | `models.TextField` | — |
| `website` | `models.URLField` | — |
| `contact_person` | `models.CharField` | max_length=200 |


#### Expert — ligne 39

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.OneToOneField` | cible/arguments : User; on_delete=models.CASCADE; related_name='expert_profile' |
| `structure` | `models.ForeignKey` | cible/arguments : Structure; on_delete=models.PROTECT; related_name='experts' |
| `appointment_decree_number` | `models.CharField` | max_length=100 |
| `appointment_date` | `models.DateField` | null=True |
| `specialties` | `models.CharField` | max_length=500 |
| `cv` | `models.FileField` | null=True; upload_to='experts/cv/' |
| `ctm` | `models.ForeignKey` | cible/arguments : 'governance.CTM'; on_delete=models.SET_NULL; null=True; related_name='member_experts' |
| `status` | `models.CharField` | max_length=20 |
| `accepted_by` | `models.ForeignKey` | cible/arguments : 'self'; on_delete=models.SET_NULL; null=True; related_name='experts_accepted' |
| `accepted_at` | `models.DateTimeField` | null=True |
| `rejected_by` | `models.ForeignKey` | cible/arguments : 'self'; on_delete=models.SET_NULL; null=True; related_name='experts_rejected' |
| `rejected_at` | `models.DateTimeField` | null=True |
| `rejection_reason` | `models.TextField` | — |
| `bank_account` | `models.CharField` | max_length=100 |
| `bank_name` | `models.CharField` | max_length=200 |
| `mobile_money_number` | `models.CharField` | max_length=20 |
| `whatsapp_number` | `models.CharField` | max_length=20 |
| `daily_rate` | `models.DecimalField` | — |
| `monthly_research_allowance` | `models.DecimalField` | — |
| `presence_count` | `models.PositiveIntegerField` | — |
| `inscription_date` | `models.DateTimeField` | — |
| `activation_date` | `models.DateTimeField` | null=True |
| `theme_preference` | `models.CharField` | max_length=10 |


### apps/gemini_drafts/models.py

#### Draft — ligne 6

Bases : `models.Model`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `id` | `models.UUIDField` | — |
| `ctm` | `models.CharField` | max_length=200 |
| `wg` | `models.CharField` | max_length=200 |
| `type` | `models.CharField` | max_length=50 |
| `domain` | `models.CharField` | null=True; max_length=200 |
| `input_json` | `models.JSONField` | null=True |
| `draft_text` | `models.TextField` | — |
| `created_at` | `models.DateTimeField` | — |
| `classification_reason` | `models.TextField` | — |


### apps/governance/models.py

#### CTM — ligne 8

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `name` | `models.CharField` | unique=True; max_length=200 |
| `number` | `models.PositiveIntegerField` | unique=True |
| `description` | `models.TextField` | — |
| `iso_reference` | `models.CharField` | max_length=50 |
| `arso_reference` | `models.CharField` | max_length=50 |
| `scientific_president` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='ctm_president_of' |
| `rapporteur` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='ctm_rapporteur_of' |
| `secretary` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='ctm_secretary_of' |


#### WG — ligne 51

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `ctm` | `models.ForeignKey` | cible/arguments : CTM; on_delete=models.CASCADE; related_name='working_groups' |
| `name` | `models.CharField` | max_length=200 |
| `number` | `models.PositiveIntegerField` | — |
| `description` | `models.TextField` | — |
| `president` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='wg_president_of' |
| `rapporteur` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='wg_rapporteur_of' |
| `secretary` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='wg_secretary_of' |

- Meta `unique_together` : `('ctm', 'number')`.

#### Affectation — ligne 91

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE; related_name='governance_affectations' |
| `ctm` | `models.ForeignKey` | cible/arguments : CTM; on_delete=models.CASCADE; related_name='affectations' |
| `wg` | `models.ForeignKey` | cible/arguments : WG; on_delete=models.CASCADE; null=True; related_name='affectations' |
| `is_primary_ctm` | `models.BooleanField` | — |
| `is_primary_wg` | `models.BooleanField` | — |

- Meta `unique_together` : `('expert', 'ctm', 'wg')`.

#### ComitePilotage — ligne 141

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `name` | `models.CharField` | max_length=200 |
| `president` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='pilotage_president' |
| `vice_president` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='pilotage_vice_president' |
| `secretary` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='pilotage_secretary' |
| `rapporteur` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='pilotage_rapporteur' |
| `members` | `models.ManyToManyField` | cible/arguments : Expert; through='PilotageMembreship'; related_name='pilotage_member_of' |


#### PilotageMembreship — ligne 188

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `comite` | `models.ForeignKey` | cible/arguments : ComitePilotage; on_delete=models.CASCADE |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE |
| `role` | `models.CharField` | max_length=50 |

- Meta `unique_together` : `('comite', 'expert')`.

#### PosteNominatif — ligne 220

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `comite` | `models.ForeignKey` | cible/arguments : ComitePilotage; on_delete=models.CASCADE; related_name='postes_nominatifs' |
| `role` | `models.CharField` | max_length=50 |
| `title` | `models.CharField` | max_length=300 |
| `required_structure` | `models.ForeignKey` | cible/arguments : 'experts.Structure'; on_delete=models.SET_NULL; null=True; related_name='postes_nominatifs' |
| `quota_line` | `models.PositiveSmallIntegerField` | null=True |
| `order` | `models.PositiveSmallIntegerField` | — |
| `holder` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='postes_nominatifs_occupes' |

- Meta `unique_together` : `('comite', 'title')`.

#### OriginStructure — ligne 286

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `name` | `models.CharField` | unique=True; max_length=200 |
| `code` | `models.CharField` | unique=True; max_length=50 |
| `description` | `models.TextField` | — |
| `expected_expert_count` | `models.PositiveIntegerField` | — |
| `giron` | `models.CharField` | max_length=50 |


#### TechnicalCell — ligne 315

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `name` | `models.CharField` | max_length=200 |
| `coordinator` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='ctc_coordinator' |
| `vice_coordinator` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='ctc_vice_coordinator' |
| `members` | `models.ManyToManyField` | cible/arguments : Expert; through='CTCMembership'; related_name='ctc_member_of' |


#### CTCMembership — ligne 348

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `ctc` | `models.ForeignKey` | cible/arguments : TechnicalCell; on_delete=models.CASCADE |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE |
| `role` | `models.CharField` | max_length=50 |

- Meta `unique_together` : `('ctc', 'expert')`.

#### PosteNominatifCTC — ligne 383

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `ctc` | `models.ForeignKey` | cible/arguments : TechnicalCell; on_delete=models.CASCADE; related_name='postes_nominatifs' |
| `role` | `models.CharField` | max_length=50 |
| `title` | `models.CharField` | max_length=300 |
| `required_structure` | `models.ForeignKey` | cible/arguments : 'experts.Structure'; on_delete=models.SET_NULL; null=True; related_name='postes_nominatifs_ctc' |
| `quota_line` | `models.PositiveSmallIntegerField` | null=True |
| `order` | `models.PositiveSmallIntegerField` | — |
| `holder` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='postes_nominatifs_ctc_occupes' |

- Meta `unique_together` : `('ctc', 'title')`.

#### CTCOperationalRequest — ligne 458

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `requester` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE; related_name='ctc_requests' |
| `restricted_resource` | `models.CharField` | max_length=300 |
| `reason` | `models.TextField` | — |
| `status` | `models.CharField` | max_length=20 |
| `reviewed_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='ctc_reviews' |
| `reviewed_at` | `models.DateTimeField` | null=True |
| `review_comment` | `models.TextField` | — |


#### PermissionRequest — ligne 503

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `requester` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE; related_name='permission_requests' |
| `restricted_resource` | `models.CharField` | max_length=300 |
| `reason` | `models.TextField` | — |
| `status` | `models.CharField` | max_length=20 |
| `reviewed_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='permission_reviews' |
| `reviewed_at` | `models.DateTimeField` | null=True |
| `review_comment` | `models.TextField` | — |


#### ExecutiveLevel — ligne 546

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `position` | `models.CharField` | unique=True; max_length=100 |
| `expert` | `models.OneToOneField` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='executive_position' |


#### Tache — ligne 574

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `working_group` | `models.ForeignKey` | cible/arguments : WG; on_delete=models.CASCADE; related_name='tasks' |
| `norme` | `models.ForeignKey` | cible/arguments : 'norms.Norme'; on_delete=models.SET_NULL; null=True; related_name='tasks' |
| `titre` | `models.CharField` | max_length=300 |
| `description` | `models.TextField` | — |
| `status` | `models.CharField` | max_length=50 |
| `progress` | `models.IntegerField` | — |
| `assigned_to` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='assigned_tasks' |
| `due_date` | `models.DateField` | null=True |


#### CTCProcessus — ligne 623

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : 'norms.Norme'; on_delete=models.CASCADE; related_name='ctc_processus' |
| `current_stage` | `models.CharField` | max_length=20 |
| `received_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='received_norms' |
| `received_at` | `models.DateTimeField` | null=True |
| `indexed_at` | `models.DateTimeField` | null=True |
| `intake_validated_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='intake_validated_norms' |
| `intake_validated_at` | `models.DateTimeField` | null=True |
| `requires_sig` | `models.BooleanField` | — |
| `sig_completed_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='sig_completed_norms' |
| `sig_completed_at` | `models.DateTimeField` | null=True |
| `it_stored_at` | `models.DateTimeField` | null=True |
| `multi_review_started_at` | `models.DateTimeField` | null=True |
| `all_reviews_completed` | `models.BooleanField` | — |
| `all_reviews_completed_at` | `models.DateTimeField` | null=True |
| `industrial_completed_at` | `models.DateTimeField` | null=True |
| `signed_out_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='signed_out_norms' |
| `signed_out_at` | `models.DateTimeField` | null=True |
| `transmitted_to_pilotage_at` | `models.DateTimeField` | null=True |
| `received_by_president` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='president_received_norms' |
| `received_by_president_at` | `models.DateTimeField` | null=True |
| `received_by_rapporteur` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='rapporteur_received_norms' |
| `received_by_rapporteur_at` | `models.DateTimeField` | null=True |


#### NormeCadrage — ligne 803

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : 'norms.Norme'; on_delete=models.CASCADE; related_name='cadrage' |
| `current_stage` | `models.CharField` | max_length=24 |
| `opened_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_ouverts' |
| `opened_at` | `models.DateTimeField` | null=True |
| `strategic_orientation` | `models.TextField` | — |
| `onic_validated_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_valides_onic' |
| `onic_validated_at` | `models.DateTimeField` | null=True |
| `onic_notes` | `models.TextField` | — |
| `btp_validated_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_valides_btp' |
| `btp_validated_at` | `models.DateTimeField` | null=True |
| `btp_notes` | `models.TextField` | — |
| `mandate_formalized_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_mandats_formalises' |
| `mandate_formalized_at` | `models.DateTimeField` | null=True |
| `operational_mandate` | `models.TextField` | — |
| `scheduled_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_planifies' |
| `scheduled_at` | `models.DateTimeField` | null=True |
| `deadline_ctm_review` | `models.DateField` | null=True |
| `deadline_ctc_handoff` | `models.DateField` | null=True |
| `deadline_pilotage_review` | `models.DateField` | null=True |
| `transmitted_to_ctc_at` | `models.DateTimeField` | null=True |
| `pv_verified_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_pv_verifies' |
| `pv_verified_at` | `models.DateTimeField` | null=True |
| `pv_reference` | `models.CharField` | max_length=100 |
| `onic_quitus_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_quitus_onic' |
| `onic_quitus_at` | `models.DateTimeField` | null=True |
| `btp_quitus_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_quitus_btp' |
| `btp_quitus_at` | `models.DateTimeField` | null=True |
| `final_validated_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='cadrages_valides_finaux' |
| `final_validated_at` | `models.DateTimeField` | null=True |
| `resolution_reference` | `models.CharField` | max_length=100 |
| `transmitted_to_ministry_at` | `models.DateTimeField` | null=True |


#### PlatformFreeze — ligne 1055

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `is_locked` | `models.BooleanField` | — |
| `locked_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='+' |
| `locked_at` | `models.DateTimeField` | null=True |


### apps/ia_agent/models.py

#### AgentSession — ligne 9

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.ForeignKey` | cible/arguments : settings.AUTH_USER_MODEL; on_delete=models.CASCADE; related_name='ia_agent_sessions' |
| `scope` | `models.CharField` | max_length=20 |
| `provider` | `models.CharField` | max_length=20 |
| `title` | `models.CharField` | max_length=200 |
| `is_active` | `models.BooleanField` | — |

- Meta `indexes` : `[models.Index(fields=['user', 'scope'])]`.

#### AgentMessage — ligne 43

Bases : `models.Model`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `session` | `models.ForeignKey` | cible/arguments : AgentSession; on_delete=models.CASCADE; related_name='messages' |
| `role` | `models.CharField` | max_length=10 |
| `content` | `models.TextField` | — |
| `tool_name` | `models.CharField` | max_length=100 |
| `tool_input` | `models.JSONField` | null=True |
| `tool_output` | `models.JSONField` | null=True |
| `created_at` | `models.DateTimeField` | — |

- Meta `indexes` : `[models.Index(fields=['session', 'created_at'])]`.

#### AgentArtifact — ligne 72

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `session` | `models.ForeignKey` | cible/arguments : AgentSession; on_delete=models.CASCADE; related_name='artifacts' |
| `message` | `models.ForeignKey` | cible/arguments : AgentMessage; on_delete=models.SET_NULL; null=True; related_name='artifacts' |
| `artifact_type` | `models.CharField` | max_length=20 |
| `title` | `models.CharField` | max_length=300 |
| `payload` | `models.JSONField` | — |
| `status` | `models.CharField` | max_length=10 |
| `content_type` | `models.ForeignKey` | cible/arguments : ContentType; on_delete=models.SET_NULL; null=True |
| `object_id` | `models.PositiveIntegerField` | null=True |
| `related_object` | `GenericForeignKey` | cible/arguments : 'content_type', 'object_id' |

- Meta `indexes` : `[models.Index(fields=['session', 'artifact_type']), models.Index(fields=['content_type', 'object_id'])]`.

#### RAGDocument — ligne 114

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `source_kind` | `models.CharField` | max_length=20 |
| `source_key` | `models.CharField` | unique=True; max_length=180 |
| `title` | `models.CharField` | max_length=500 |
| `mime_type` | `models.CharField` | max_length=120 |
| `content_hash` | `models.CharField` | max_length=64 |
| `status` | `models.CharField` | max_length=20 |
| `metadata` | `models.JSONField` | — |
| `extraction_error` | `models.TextField` | — |
| `indexed_at` | `models.DateTimeField` | null=True |

- Meta `indexes` : `[models.Index(fields=['source_kind', 'status']), models.Index(fields=['content_hash'])]`.

#### RAGChunk — ligne 151

Bases : `models.Model`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `document` | `models.ForeignKey` | cible/arguments : RAGDocument; on_delete=models.CASCADE; related_name='chunks' |
| `ordinal` | `models.PositiveIntegerField` | — |
| `content` | `models.TextField` | — |
| `page_number` | `models.PositiveIntegerField` | null=True |
| `section` | `models.CharField` | max_length=500 |
| `metadata` | `models.JSONField` | — |

- Meta `constraints` : `[models.UniqueConstraint(fields=['document', 'ordinal'], name='unique_rag_chunk_order')]`.
- Meta `indexes` : `[models.Index(fields=['document', 'page_number'])]`.

#### AgentScopeConfig — ligne 177

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `scope` | `models.CharField` | max_length=20 |
| `role_key` | `models.CharField` | max_length=60 |
| `label` | `models.CharField` | max_length=200 |
| `system_prompt_extra` | `models.TextField` | — |
| `allowed_tools` | `models.JSONField` | null=True |
| `is_active` | `models.BooleanField` | — |

- Meta `unique_together` : `[('scope', 'role_key')]`.

#### AgentPosteContext — ligne 211

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `organ` | `models.CharField` | max_length=20 |
| `sub_role` | `models.CharField` | max_length=60 |
| `hierarchy_level` | `models.PositiveSmallIntegerField` | — |
| `position_label` | `models.CharField` | max_length=500 |
| `mission_summary` | `models.TextField` | — |
| `tools_hint` | `models.TextField` | — |
| `poste_pilotage` | `models.OneToOneField` | cible/arguments : 'governance.PosteNominatif'; on_delete=models.SET_NULL; null=True; related_name='agent_context' |
| `poste_ctc` | `models.OneToOneField` | cible/arguments : 'governance.PosteNominatifCTC'; on_delete=models.SET_NULL; null=True; related_name='agent_context' |
| `is_active` | `models.BooleanField` | — |

- Meta `unique_together` : `[('organ', 'sub_role')]`.

### apps/meetings/models.py

#### Reunion — ligne 8

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `type` | `models.CharField` | max_length=20 |
| `titre` | `models.CharField` | max_length=255 |
| `description` | `models.TextField` | null=True |
| `ctm` | `models.ForeignKey` | cible/arguments : CTM; on_delete=models.SET_NULL; null=True; related_name='reunions' |
| `wg` | `models.ForeignKey` | cible/arguments : WG; on_delete=models.SET_NULL; null=True; related_name='reunions' |
| `document_reglementaire` | `models.CharField` | max_length=255 |
| `date` | `models.DateTimeField` | — |
| `lieu` | `models.CharField` | null=True; max_length=255 |
| `lien_reunion_virtuelle` | `models.URLField` | null=True |
| `ordre_jour` | `models.TextField` | null=True |
| `status` | `models.CharField` | max_length=20 |
| `organisateur` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='reunions_organisees' |

- Meta `indexes` : `[models.Index(fields=['type', 'date']), models.Index(fields=['status', 'date'])]`.

#### ReunionVote — ligne 51

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `reunion` | `models.ForeignKey` | cible/arguments : Reunion; on_delete=models.CASCADE; related_name='votes' |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE; related_name='reunion_votes' |
| `choix` | `models.CharField` | max_length=20 |
| `justification` | `models.TextField` | — |
| `voted_at` | `models.DateTimeField` | — |

- Meta `unique_together` : `('reunion', 'expert')`.
- Meta `indexes` : `[models.Index(fields=['reunion', 'choix'], name='meetings_re_reunion_581dc1_idx')]`.

#### Presence — ligne 77

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `reunion` | `models.ForeignKey` | cible/arguments : Reunion; on_delete=models.CASCADE; related_name='presences' |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE; related_name='presences' |
| `status` | `models.CharField` | max_length=20 |
| `marked_at` | `models.DateTimeField` | — |
| `marked_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='presences_marked' |

- Meta `unique_together` : `('reunion', 'expert')`.
- Meta `indexes` : `[models.Index(fields=['reunion', 'status'])]`.

#### ProcessusVerbaux — ligne 103

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `reunion` | `models.OneToOneField` | cible/arguments : Reunion; on_delete=models.CASCADE; related_name='pv' |
| `titre` | `models.CharField` | max_length=255 |
| `contenu` | `models.TextField` | — |
| `nombre_presents` | `models.IntegerField` | — |
| `nombre_absents` | `models.IntegerField` | — |
| `quorum_atteint` | `models.BooleanField` | — |
| `generated_at` | `models.DateTimeField` | — |
| `signed_by` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='pv_signed' |
| `signature_date` | `models.DateTimeField` | null=True |


### apps/messaging/models.py

#### Message — ligne 6

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `sender` | `models.ForeignKey` | cible/arguments : settings.AUTH_USER_MODEL; on_delete=models.CASCADE; related_name='sent_messages' |
| `recipient` | `models.ForeignKey` | cible/arguments : settings.AUTH_USER_MODEL; on_delete=models.SET_NULL; null=True; related_name='received_messages' |
| `reunion` | `models.ForeignKey` | cible/arguments : 'meetings.Reunion'; on_delete=models.SET_NULL; null=True; related_name='messages' |
| `subject` | `models.CharField` | max_length=200 |
| `content` | `models.TextField` | — |
| `status` | `models.CharField` | max_length=12 |
| `timestamp` | `models.DateTimeField` | — |
| `parent` | `models.ForeignKey` | cible/arguments : 'self'; on_delete=models.SET_NULL; null=True; related_name='replies' |
| `is_read` | `models.BooleanField` | — |
| `is_clause_share` | `models.BooleanField` | — |
| `clause_code` | `models.CharField` | null=True; max_length=255 |
| `clause_excerpt` | `models.TextField` | null=True |

- Meta `indexes` : `[models.Index(fields=['sender', 'timestamp']), models.Index(fields=['recipient', 'timestamp']), models.Index(fields=['reunion', 'timestamp'])]`.

### apps/mobileapp/models.py

#### ActivationToken — ligne 14

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `expert` | `models.OneToOneField` | cible/arguments : Expert; on_delete=models.CASCADE; related_name='activation_token' |
| `token` | `models.CharField` | unique=True; max_length=255 |
| `is_used` | `models.BooleanField` | — |
| `used_at` | `models.DateTimeField` | null=True |
| `expires_at` | `models.DateTimeField` | — |

- Meta `indexes` : `[models.Index(fields=['token', 'is_used']), models.Index(fields=['expert', 'is_used'])]`.

#### EmailConfirmationCode — ligne 68

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.ForeignKey` | cible/arguments : User; on_delete=models.CASCADE; related_name='email_confirmation_codes' |
| `code` | `models.CharField` | max_length=6 |
| `is_used` | `models.BooleanField` | — |
| `used_at` | `models.DateTimeField` | null=True |
| `expires_at` | `models.DateTimeField` | — |

- Meta `indexes` : `[models.Index(fields=['user', 'is_used'])]`.

#### PublicUser — ligne 120

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.OneToOneField` | cible/arguments : User; on_delete=models.CASCADE; related_name='public_profile' |
| `province` | `models.CharField` | max_length=100 |
| `profession` | `models.CharField` | null=True; max_length=255 |
| `bio` | `models.TextField` | null=True |
| `phone_number` | `models.CharField` | null=True; max_length=20 |
| `is_active` | `models.BooleanField` | — |
| `last_login_mobile` | `models.DateTimeField` | null=True |


#### PushToken — ligne 139

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.ForeignKey` | cible/arguments : User; on_delete=models.CASCADE; related_name='push_tokens' |
| `token` | `models.CharField` | unique=True; max_length=500 |
| `device_type` | `models.CharField` | max_length=20 |
| `device_name` | `models.CharField` | max_length=255 |
| `is_active` | `models.BooleanField` | — |
| `last_used` | `models.DateTimeField` | — |

- Meta `unique_together` : `('user', 'token')`.

#### Notification — ligne 164

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `id` | `models.UUIDField` | — |
| `user` | `models.ForeignKey` | cible/arguments : User; on_delete=models.CASCADE; related_name='notifications' |
| `title` | `models.CharField` | max_length=255 |
| `body` | `models.TextField` | — |
| `notification_type` | `models.CharField` | max_length=20 |
| `priority` | `models.CharField` | max_length=10 |
| `data` | `models.JSONField` | — |
| `is_read` | `models.BooleanField` | — |
| `read_at` | `models.DateTimeField` | null=True |

- Meta `indexes` : `[models.Index(fields=['user', 'is_read']), models.Index(fields=['user', 'notification_type'])]`.

#### NotificationLog — ligne 221

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `notification` | `models.ForeignKey` | cible/arguments : Notification; on_delete=models.CASCADE; related_name='logs' |
| `push_token` | `models.ForeignKey` | cible/arguments : PushToken; on_delete=models.SET_NULL; null=True; related_name='logs' |
| `status` | `models.CharField` | max_length=20 |
| `provider` | `models.CharField` | max_length=50 |
| `provider_response` | `models.JSONField` | — |
| `error_message` | `models.TextField` | null=True |
| `sent_at` | `models.DateTimeField` | null=True |

- Meta `indexes` : `[models.Index(fields=['status', 'sent_at']), models.Index(fields=['push_token', 'status'])]`.

#### NotificationPreference — ligne 251

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `user` | `models.OneToOneField` | cible/arguments : User; on_delete=models.CASCADE; related_name='notification_preferences' |
| `enable_reunion_invites` | `models.BooleanField` | — |
| `enable_votes` | `models.BooleanField` | — |
| `enable_amendments` | `models.BooleanField` | — |
| `enable_norm_updates` | `models.BooleanField` | — |
| `enable_system` | `models.BooleanField` | — |
| `enable_payments` | `models.BooleanField` | — |
| `quiet_hours_enabled` | `models.BooleanField` | — |
| `quiet_hours_start` | `models.TimeField` | null=True |
| `quiet_hours_end` | `models.TimeField` | null=True |
| `digest_enabled` | `models.BooleanField` | — |
| `digest_frequency` | `models.CharField` | max_length=20 |


#### MobileSession — ligne 284

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `id` | `models.UUIDField` | — |
| `user` | `models.ForeignKey` | cible/arguments : User; on_delete=models.CASCADE; related_name='mobile_sessions' |
| `device_id` | `models.CharField` | max_length=255 |
| `device_type` | `models.CharField` | max_length=20 |
| `ip_address` | `models.GenericIPAddressField` | null=True |
| `user_agent` | `models.TextField` | — |
| `last_activity` | `models.DateTimeField` | — |
| `is_active` | `models.BooleanField` | — |
| `expires_at` | `models.DateTimeField` | — |

- Meta `indexes` : `[models.Index(fields=['user', 'is_active'])]`.

### apps/norms/models.py

#### Norme — ligne 12

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `title` | `models.CharField` | max_length=500 |
| `reference_number` | `models.CharField` | unique=True; max_length=50 |
| `description` | `models.TextField` | — |
| `ctm` | `models.ForeignKey` | cible/arguments : CTM; on_delete=models.PROTECT; related_name='normes' |
| `wg` | `models.ForeignKey` | cible/arguments : WG; on_delete=models.PROTECT; related_name='normes' |
| `standard_family` | `models.CharField` | max_length=10 |
| `category` | `models.CharField` | max_length=100 |
| `iso_reference` | `models.CharField` | max_length=50 |
| `arso_reference` | `models.CharField` | max_length=50 |
| `norm_type` | `models.CharField` | max_length=3 |
| `target_count` | `models.PositiveIntegerField` | — |
| `status` | `models.CharField` | max_length=20 |
| `start_date` | `models.DateField` | — |
| `ctm_submission_date` | `models.DateField` | null=True |
| `legistic_review_date` | `models.DateField` | null=True |
| `public_inquiry_start` | `models.DateField` | null=True |
| `public_inquiry_end` | `models.DateField` | null=True |
| `pilotage_validation_date` | `models.DateField` | null=True |
| `adoption_date` | `models.DateField` | null=True |
| `homologation_date` | `models.DateField` | null=True |
| `publication_date` | `models.DateField` | null=True |
| `jo_reference` | `models.CharField` | max_length=100 |
| `jo_file` | `models.FileField` | null=True; upload_to='norms/jo/' |
| `current_version` | `models.FileField` | null=True; upload_to='norms/versions/' |
| `tags` | `models.CharField` | max_length=500 |
| `is_public` | `models.BooleanField` | — |
| `locked_by` | `models.ForeignKey` | cible/arguments : User; on_delete=models.SET_NULL; null=True; related_name='locked_norms' |
| `lock_timeout` | `models.DateTimeField` | null=True |

- Meta `indexes` : `[models.Index(fields=['status', 'ctm']), models.Index(fields=['publication_date'])]`.

#### NormeVersion — ligne 189

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.ForeignKey` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='versions' |
| `version_number` | `models.PositiveIntegerField` | — |
| `title` | `models.CharField` | max_length=500 |
| `content` | `models.TextField` | — |
| `document` | `models.FileField` | null=True; upload_to='norms/versions/' |
| `summary` | `models.TextField` | — |
| `is_draft` | `models.BooleanField` | — |
| `version_author` | `models.ForeignKey` | cible/arguments : User; on_delete=models.SET_NULL; null=True |
| `created_at` | `models.DateTimeField` | — |

- Meta `unique_together` : `('norme', 'version_number')`.

#### NormeComment — ligne 220

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.ForeignKey` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='comments' |
| `author` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='norme_comments' |
| `body` | `models.TextField` | — |


#### ChangementVersion — ligne 237

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `version` | `models.ForeignKey` | cible/arguments : NormeVersion; on_delete=models.CASCADE; related_name='changes' |
| `previous_version` | `models.ForeignKey` | cible/arguments : NormeVersion; on_delete=models.SET_NULL; null=True; related_name='changes_from' |
| `section` | `models.CharField` | max_length=100 |
| `old_text` | `models.TextField` | — |
| `new_text` | `models.TextField` | — |
| `change_type` | `models.CharField` | max_length=20 |
| `change_reason` | `models.TextField` | — |


#### NormeVote — ligne 271

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.ForeignKey` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='votes' |
| `voter` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.PROTECT; related_name='norme_votes' |
| `vote` | `models.CharField` | max_length=10 |
| `justification` | `models.TextField` | — |
| `vote_date` | `models.DateTimeField` | — |

- Meta `unique_together` : `('norme', 'voter')`.
- Meta `indexes` : `[models.Index(fields=['norme', 'vote'], name='norms_norme_vote_idx')]`.

#### NormeContentBlock — ligne 299

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `version` | `models.ForeignKey` | cible/arguments : NormeVersion; on_delete=models.CASCADE; related_name='content_blocks' |
| `parent` | `models.ForeignKey` | cible/arguments : 'self'; on_delete=models.CASCADE; null=True; related_name='children' |
| `kind` | `models.CharField` | max_length=20 |
| `code` | `models.CharField` | max_length=50 |
| `title` | `models.CharField` | max_length=500 |
| `body` | `models.TextField` | — |
| `position` | `models.PositiveIntegerField` | — |
| `metadata` | `models.JSONField` | — |

- Meta `unique_together` : `('version', 'position')`.

#### NormeDocumentImport — ligne 335

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `filename` | `models.CharField` | unique=True; max_length=255 |
| `source_path` | `models.CharField` | max_length=500 |
| `document_type` | `models.CharField` | max_length=50 |
| `paragraph_count` | `models.PositiveIntegerField` | — |
| `extracted_json` | `models.JSONField` | — |
| `checksum` | `models.CharField` | max_length=64 |
| `imported_at` | `models.DateTimeField` | — |
| `norme` | `models.ForeignKey` | cible/arguments : Norme; on_delete=models.SET_NULL; null=True; related_name='document_imports' |


### apps/payments/models.py

#### Cotisation — ligne 9

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `structure` | `models.ForeignKey` | cible/arguments : Structure; on_delete=models.CASCADE; related_name='cotisations' |
| `annee` | `models.IntegerField` | — |
| `montant` | `models.DecimalField` | — |
| `status` | `models.CharField` | max_length=20 |
| `due_date` | `models.DateField` | — |
| `notes` | `models.TextField` | null=True |

- Meta `unique_together` : `('structure', 'annee')`.
- Meta `indexes` : `[models.Index(fields=['structure', 'annee']), models.Index(fields=['status', 'due_date'])]`.

#### Paiement — ligne 51

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `cotisation` | `models.ForeignKey` | cible/arguments : Cotisation; on_delete=models.CASCADE; related_name='paiements' |
| `montant` | `models.DecimalField` | — |
| `status` | `models.CharField` | max_length=20 |
| `methode_paiement` | `models.CharField` | max_length=20 |
| `numero_recu` | `models.CharField` | null=True; unique=True; max_length=50 |
| `numero_transaction` | `models.CharField` | null=True; max_length=100 |
| `proof_file` | `models.FileField` | null=True; upload_to='payment_proofs/' |
| `payment_date` | `models.DateField` | — |
| `confirmed_at` | `models.DateTimeField` | null=True |
| `notes` | `models.TextField` | null=True |

- Meta `indexes` : `[models.Index(fields=['cotisation', 'status']), models.Index(fields=['payment_date', 'status'])]`.

#### JetonPresence — ligne 100

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.CASCADE; related_name='jetons' |
| `reunion` | `models.ForeignKey` | cible/arguments : Reunion; on_delete=models.CASCADE; related_name='jetons_presence' |
| `montant` | `models.DecimalField` | — |
| `status` | `models.CharField` | max_length=20 |
| `payment_date` | `models.DateField` | null=True |
| `notes` | `models.TextField` | null=True |

- Meta `unique_together` : `('expert', 'reunion')`.
- Meta `indexes` : `[models.Index(fields=['expert', 'status']), models.Index(fields=['reunion', 'status'])]`.

### apps/public/models.py

#### PublicAmendement — ligne 7

Bases : `models.Model`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.ForeignKey` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='public_amendments' |
| `proposed_by_name` | `models.CharField` | max_length=255 |
| `proposed_by_email` | `models.EmailField` | — |
| `proposed_by_organization` | `models.CharField` | max_length=255 |
| `title` | `models.CharField` | max_length=255 |
| `description` | `models.TextField` | — |
| `justification` | `models.TextField` | — |
| `status` | `models.CharField` | max_length=20 |
| `review_notes` | `models.TextField` | — |
| `reviewed_by` | `models.CharField` | max_length=255 |
| `reviewed_at` | `models.DateTimeField` | null=True |
| `created_at` | `models.DateTimeField` | — |
| `updated_at` | `models.DateTimeField` | — |

- Meta `indexes` : `[models.Index(fields=['norme', 'status']), models.Index(fields=['created_at'])]`.

### apps/validation/models.py

#### LegisticReview — ligne 17

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='legistic_review' |
| `legist` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='reviews_as_legist' |
| `status` | `models.CharField` | max_length=20 |
| `comments` | `models.TextField` | null=True |
| `review_start_date` | `models.DateField` | null=True |
| `review_end_date` | `models.DateField` | null=True |
| `approval_date` | `models.DateField` | null=True |


#### ISOReview — ligne 45

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='iso_review' |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='reviews_as_iso_expert' |
| `status` | `models.CharField` | max_length=20 |
| `harmonization_notes` | `models.TextField` | — |
| `iso_references` | `models.CharField` | max_length=500 |
| `review_start_date` | `models.DateField` | null=True |
| `review_end_date` | `models.DateField` | null=True |


#### EcologicalReview — ligne 66

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='ecological_review' |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='reviews_as_environmental_expert' |
| `status` | `models.CharField` | max_length=20 |
| `impact_matrix` | `models.JSONField` | — |
| `comments` | `models.TextField` | — |
| `review_start_date` | `models.DateField` | null=True |
| `review_end_date` | `models.DateField` | null=True |


#### EconomicReview — ligne 91

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='economic_review' |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='reviews_as_economist' |
| `status` | `models.CharField` | max_length=20 |
| `construction_cost_usd_per_km` | `models.DecimalField` | null=True |
| `annual_maintenance_cost_usd` | `models.DecimalField` | null=True |
| `lifecycle_years` | `models.PositiveIntegerField` | null=True |
| `discount_rate_pct` | `models.DecimalField` | null=True |
| `lifecycle_cost_usd` | `models.DecimalField` | null=True |
| `comments` | `models.TextField` | — |
| `review_start_date` | `models.DateField` | null=True |
| `review_end_date` | `models.DateField` | null=True |


#### ScheduleReview — ligne 116

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='schedule_review' |
| `planner` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='reviews_as_planner' |
| `scientist` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='reviews_as_scientist' |
| `planner_status` | `models.CharField` | max_length=20 |
| `scientist_status` | `models.CharField` | max_length=20 |
| `planner_notes` | `models.TextField` | — |
| `scientist_notes` | `models.TextField` | — |
| `review_start_date` | `models.DateField` | null=True |
| `review_end_date` | `models.DateField` | null=True |


#### IndustrialConsultation — ligne 145

Bases : `BaseModel`.

| Champ | Type | Relation / contraintes |
|---|---|---|
| `norme` | `models.OneToOneField` | cible/arguments : Norme; on_delete=models.CASCADE; related_name='industrial_consultation' |
| `expert` | `models.ForeignKey` | cible/arguments : Expert; on_delete=models.SET_NULL; null=True; related_name='industrial_consultations' |
| `status` | `models.CharField` | max_length=20 |
| `fec_feedback` | `models.TextField` | — |
| `companies_consulted` | `models.JSONField` | — |
| `market_feasible` | `models.BooleanField` | null=True |
| `review_start_date` | `models.DateField` | null=True |
| `review_end_date` | `models.DateField` | null=True |


Total : 65 classes déclarées, dont BaseModel abstrait.

## 2. Points de contrôle des permissions et routes

Index statique : chaque extrait doit être lu avec get_permissions, les contrôles du handler et le filtrage du queryset. Une permission affichée ou déclarée ne prouve pas une protection effective de toutes les actions.

### api/v1/amendments/views.py

- Ligne 25 : `permission_classes = [IsAuthenticated]`.
- Ligne 44 : `def get_permissions(self):`.
- Ligne 66 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 79 : `@action(detail=True, methods=['post'], permission_classes=[IsExpert])`.
- Ligne 206 : `permission_classes = [IsAuthenticated]`.
- Ligne 231 : `permission_classes = [IsAuthenticated]`.

### api/v1/auth/views.py

- Ligne 28 : `permission_classes = [AllowAny]  # Par défaut, tout le monde peut s'enregistrer/connecter`.
- Ligne 30 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny])`.
- Ligne 63 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny])`.
- Ligne 99 : `@action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])`.
- Ligne 112 : `@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])`.
- Ligne 122 : `@action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])`.
- Ligne 149 : `@action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])`.
- Ligne 186 : `permission_classes = [IsAuthenticated]`.

### api/v1/documents/bridge_views.py

- Ligne 23 : `permission_classes = [AllowAny]`.
- Ligne 53 : `permission_classes = [AllowAny]`.

### api/v1/documents/views.py

- Ligne 17 : `permission_classes = [IsAuthenticated]`.

### api/v1/experts/registration_views.py

- Ligne 29 : `permission_classes = [AllowAny]`.
- Ligne 31 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny])`.
- Ligne 93 : `@action(detail=False, methods=['get'], permission_classes=[AllowAny])`.
- Ligne 105 : `@action(detail=False, methods=['get'], permission_classes=[AllowAny])`.
- Ligne 133 : `permission_classes = [AllowAny]`.

### api/v1/experts/views.py

- Ligne 24 : `permission_classes = [IsAuthenticated]`.
- Ligne 43 : `permission_classes = [IsAuthenticated]`.
- Ligne 87 : `def get_permissions(self):`.
- Ligne 109 : `@action(detail=False, methods=['post'], permission_classes=[])`.
- Ligne 120 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 136 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='admit-to-ctm')`.
- Ligne 177 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='reject')`.
- Ligne 217 : `@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending-for-my-ctm')`.
- Ligne 236 : `@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending-count-for-my-ctm')`.
- Ligne 253 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.

### api/v1/governance/views.py

- Ligne 24 : `permission_classes = [IsAuthenticated]`.
- Ligne 40 : `def get_permissions(self):`.
- Ligne 77 : `permission_classes = [IsAuthenticated]`.
- Ligne 93 : `def get_permissions(self):`.
- Ligne 116 : `permission_classes = [IsAuthenticated]`.
- Ligne 130 : `def get_permissions(self):`.
- Ligne 136 : `@action(detail=False, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 193 : `permission_classes = [IsAuthenticated]`.
- Ligne 200 : `def get_permissions(self):`.
- Ligne 212 : `permission_classes = [IsAuthenticated]`.
- Ligne 219 : `def get_permissions(self):`.

### api/v1/hierarchy/views.py

- Ligne 23 : `permission_classes = [IsAuthenticated]`.
- Ligne 42 : `permission_classes = [IsAuthenticated]`.
- Ligne 51 : `permission_classes = [IsAuthenticated]`.
- Ligne 58 : `permission_classes = [IsAuthenticated]`.
- Ligne 80 : `permission_classes = [IsAuthenticated]`.

### api/v1/meetings/views.py

- Ligne 27 : `permission_classes = [IsAuthenticated]`.
- Ligne 46 : `def get_permissions(self):`.
- Ligne 75 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 163 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 323 : `permission_classes = [IsAuthenticated]`.
- Ligne 327 : `def get_permissions(self):`.
- Ligne 344 : `permission_classes = [IsAuthenticated]`.
- Ligne 353 : `permission_classes = [IsAuthenticated]`.
- Ligne 357 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.

### api/v1/messaging/views.py

- Ligne 18 : `permission_classes = [permissions.IsAuthenticated, IsMemberOfAnySharedCTM]`.
- Ligne 112 : `@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])`.
- Ligne 131 : `@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])`.
- Ligne 137 : `@action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])`.
- Ligne 150 : `@action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMemberOfAnySharedCTM])`.

### api/v1/mobile/views.py

- Ligne 37 : `permission_classes = [AllowAny]`.
- Ligne 39 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny],`.
- Ligne 54 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny],`.
- Ligne 86 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny],`.
- Ligne 140 : `@action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])`.
- Ligne 157 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny],`.
- Ligne 180 : `@action(detail=False, methods=['get'], permission_classes=[AllowAny],`.
- Ligne 219 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny],`.
- Ligne 247 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny],`.
- Ligne 280 : `permission_classes = [IsAuthenticated]`.
- Ligne 299 : `permission_classes = [IsAuthenticated]`.
- Ligne 320 : `permission_classes = [IsAuthenticated]`.
- Ligne 363 : `permission_classes = [IsAuthenticated]`.
- Ligne 502 : `permission_classes = [AllowAny]`.

### api/v1/norms/views.py

- Ligne 46 : `permission_classes = [IsAuthenticated]`.
- Ligne 143 : `def get_permissions(self):`.
- Ligne 307 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 316 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsExpertOrCTC])`.
- Ligne 341 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsExpertOrCTC], url_path='lock')`.
- Ligne 365 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsExpertOrCTC], url_path='unlock')`.
- Ligne 400 : `@action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticated, IsExpertOrCTC], url_path='comments')`.
- Ligne 421 : `@action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated, IsExpertOrCTC], url_path='comments/(?P<comment_id>[^/.]+)')`.
- Ligne 437 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsExpert])`.
- Ligne 615 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])`.
- Ligne 685 : `permission_classes = [IsAuthenticated]`.
- Ligne 706 : `permission_classes = [IsAuthenticated]`.

### api/v1/payments/views.py

- Ligne 27 : `permission_classes = [IsAuthenticated]`.
- Ligne 44 : `def get_permissions(self):`.
- Ligne 50 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 128 : `permission_classes = [IsAuthenticated]`.
- Ligne 145 : `def get_permissions(self):`.
- Ligne 153 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 172 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.
- Ligne 223 : `permission_classes = [IsAuthenticated]`.
- Ligne 240 : `def get_permissions(self):`.
- Ligne 283 : `@action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])`.

### api/v1/public/views.py

- Ligne 25 : `def get_permissions(self):`.
- Ligne 54 : `@action(detail=False, methods=['post'], permission_classes=[AllowAny])`.
- Ligne 79 : `@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])`.
- Ligne 93 : `@action(detail=False, methods=['get'], permission_classes=[AllowAny])`.
- Ligne 111 : `@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])`.
- Ligne 123 : `@action(detail=False, methods=['get'], permission_classes=[AllowAny])`.

### api/v1/sidebar/views.py

- Ligne 36 : `permission_classes = [IsAuthenticated]`.
- Ligne 94 : `permission_classes = [IsAuthenticated]`.
- Ligne 150 : `permission_classes = [IsAuthenticated]`.
- Ligne 173 : `permission_classes = [IsAuthenticated]`.
- Ligne 217 : `permission_classes = [IsAuthenticated]`.
- Ligne 236 : `permission_classes = [IsAuthenticated]`.
- Ligne 263 : `permission_classes = [IsAuthenticated]`.
- Ligne 290 : `permission_classes = [IsAuthenticated]`.
- Ligne 333 : `permission_classes = [IsAuthenticated]`.
- Ligne 376 : `permission_classes = [IsAuthenticated]`.

### api/v1/validation/views.py

- Ligne 66 : `permission_classes = [IsAuthenticated]`.
- Ligne 121 : `def get_permissions(self):`.

### api/v1/permissions.py

- Classe `IsExpert`, ligne 4.
- Classe `IsCTCCoordinator`, ligne 22.
- Classe `IsMinister`, ligne 33.
- Classe `IsExpertOrCTC`, ligne 44.
- Classe `IsOwnerOrCTC`, ligne 55.
- Classe `IsMeetingOrganizerOrCTC`, ligne 73.
- Classe `IsExpertOfCTM`, ligne 85.
- Classe `ReadOnly`, ligne 103.
- Classe `IsPublicOrAuthenticated`, ligne 110.
- Classe `IsLegist`, ligne 121.
- Classe `IsMemberOfAnySharedCTM`, ligne 134.

### apps/ia_agent/services/permissions.py

- Fonction `available_scopes`, ligne 13.
- Fonction `user_can_access_scope`, ligne 30.

### web/pilotage_views.py

- Fonction `_vp_sub_role_from_title`, ligne 66.
- Fonction `_cadrages_for_subrole`, ligne 593.
- Fonction `get_pilotage_context`, ligne 664.
- Fonction `pilotage_context_api`, ligne 1210.

### web/ctc_views.py

- Fonction `_resolve_ctc_sub_role`, ligne 127.
- Fonction `_pole_for_sub_role`, ligne 205.
- Fonction `get_ctc_context`, ligne 220.
- Fonction `_ctc_shared_context`, ligne 445.
- Fonction `ctc_context_api`, ligne 1220.

### web/urls.py

- Ligne 60 : `path('wgs/', wg_redirect, name='wg_redirect_index'),`.
- Ligne 61 : `path('wgs/<int:wg_id>/', wg_redirect, name='wg_redirect'),`.
- Ligne 64 : `path('pilotage/', PilotageDashboardView.as_view(), name='pilotage_dashboard'),`.
- Ligne 65 : `path('pilotage/demande-permission/', PilotagePermissionRequestView.as_view(), name='pilotage_permission_request'),`.
- Ligne 66 : `path('pilotage/approuver-demande/<int:pk>/', PilotageApproveRequestView.as_view(), name='pilotage_approve_request'),`.
- Ligne 67 : `path('pilotage/processus/<int:pk>/receptionner/', PilotageAcknowledgeReceptionView.as_view(), name='pilotage_acknowledge_reception'),`.
- Ligne 68 : `path('pilotage/cadrage/<int:pk>/action/', PilotageCadrageActionView.as_view(), name='pilotage_cadrage_action'),`.
- Ligne 69 : `path('pilotage/bureau-directoire/', PilotageDirectoireAppView.as_view(), name='pilotage_directoire_app'),`.
- Ligne 70 : `path('pilotage/conseillers/', PilotageConseillersAppView.as_view(), name='pilotage_conseillers_app'),`.
- Ligne 71 : `path('pilotage/atf/', PilotageATFAppView.as_view(), name='pilotage_atf_app'),`.
- Ligne 72 : `path('pilotage/ctm/<int:number>/', PilotageCTMDetailView.as_view(), name='pilotage_ctm_detail'),`.
- Ligne 73 : `path('pilotage/norme/<int:pk>/commenter/', PilotageNormeCommentView.as_view(), name='pilotage_norme_comment'),`.
- Ligne 74 : `path('pilotage/gestion-acces/', PilotageExpertAccessView.as_view(), name='pilotage_expert_access'),`.
- Ligne 75 : `path('pilotage/gestion-acces/expert/<int:pk>/statut/', PilotageExpertStatusActionView.as_view(), name='pilotage_expert_status_action'),`.
- Ligne 76 : `path('pilotage/gestion-acces/affectation/<int:pk>/exclure/', PilotageAffectationExcludeView.as_view(), name='pilotage_affectation_exclude'),`.
- Ligne 77 : `path('pilotage/plateforme/verrouillage/', PilotagePlatformFreezeToggleView.as_view(), name='pilotage_platform_freeze_toggle'),`.
- Ligne 78 : `path('pilotage/ia-agent/', PilotageIAConsoleView.as_view(), name='pilotage_ia_console'),`.
- Ligne 81 : `path('api/pilotage/contexte/', pilotage_context_api, name='pilotage_context_api'),`.
- Ligne 84 : `path('ctc/', CTCDashboardView.as_view(), name='ctc_dashboard'),`.
- Ligne 85 : `path('ctc/demande-operationnelle/', CTCOperationalRequestView.as_view(), name='ctc_operational_request'),`.
- Ligne 86 : `path('ctc/approuver-demande/<int:pk>/', CTCApproveRequestView.as_view(), name='ctc_approve_request'),`.
- Ligne 87 : `path('ctc/methodologie/<int:pk>/', CTCMethodologyActionView.as_view(), name='ctc_methodology_action'),`.
- Ligne 88 : `path('ctc/revue/<str:review_type>/<int:pk>/', CTCReviewActionView.as_view(), name='ctc_review_action'),`.
- Ligne 89 : `path('ctc/dossiers/<int:pk>/reception/', CTCReceptionActionView.as_view(), name='ctc_reception_action'),`.
- Ligne 90 : `path('ctc/consultation-industrielle/<int:pk>/', CTCIndustrialActionView.as_view(), name='ctc_industrial_action'),`.
- Ligne 91 : `path('ctc/dossiers/<int:pk>/transmettre-pilotage/', CTCTransmitPilotageView.as_view(), name='ctc_transmit_pilotage'),`.
- Ligne 92 : `path('ctc/norme/<int:pk>/lecture/', CTCNormeReadView.as_view(), name='ctc_norme_read'),`.
- Ligne 93 : `path('ctc/norme/<int:pk>/qr/', ctc_norme_qr_view, name='ctc_norme_qr'),`.
- Ligne 94 : `path('ctc/ctm/<int:number>/', CTCCtmDetailView.as_view(), name='ctc_ctm_detail'),`.
- Ligne 95 : `path('api/ctc/contexte/', ctc_context_api, name='ctc_context_api'),`.

## 3. Volumes de la base locale

| Table | Nombre de lignes |
|---|---:|
| `amendments_amendement` | 0 |
| `amendments_resultatvote` | 0 |
| `amendments_vote` | 0 |
| `core_auditlog` | 0 |
| `core_passwordresetcode` | 1 |
| `core_user` | 14 |
| `core_user_groups` | 0 |
| `core_user_user_permissions` | 0 |
| `documents_documentfile` | 2 |
| `experts_expert` | 14 |
| `experts_structure` | 17 |
| `governance_affectation` | 11 |
| `governance_comitepilotage` | 1 |
| `governance_ctcmembership` | 1 |
| `governance_ctcoperationalrequest` | 0 |
| `governance_ctcprocessus` | 17 |
| `governance_ctm` | 8 |
| `governance_executivelevel` | 0 |
| `governance_normecadrage` | 0 |
| `governance_originstructure` | 0 |
| `governance_permissionrequest` | 0 |
| `governance_pilotagemembreship` | 1 |
| `governance_platformfreeze` | 1 |
| `governance_postenominatif` | 27 |
| `governance_postenominatifctc` | 20 |
| `governance_tache` | 0 |
| `governance_technicalcell` | 1 |
| `governance_wg` | 24 |
| `ia_agent_agentartifact` | 4 |
| `ia_agent_agentmessage` | 10 |
| `ia_agent_agentpostecontext` | 0 |
| `ia_agent_agentscopeconfig` | 0 |
| `ia_agent_agentsession` | 2 |
| `ia_agent_ragchunk` | 129 |
| `ia_agent_ragdocument` | 129 |
| `meetings_presence` | 0 |
| `meetings_processusvverbaux` | 0 |
| `meetings_reunion` | 2 |
| `meetings_reunionvote` | 0 |
| `messaging_message` | 122 |
| `mobileapp_activationtoken` | 0 |
| `mobileapp_emailconfirmationcode` | 0 |
| `mobileapp_mobilesession` | 0 |
| `mobileapp_notification` | 304 |
| `mobileapp_notificationlog` | 0 |
| `mobileapp_notificationpreference` | 0 |
| `mobileapp_publicuser` | 0 |
| `mobileapp_pushtoken` | 0 |
| `norms_changementversion` | 61 |
| `norms_norme` | 18 |
| `norms_normecomment` | 0 |
| `norms_normecontentblock` | 163 |
| `norms_normedocumentimport` | 0 |
| `norms_normeversion` | 109 |
| `norms_normevote` | 0 |
| `payments_cotisation` | 5 |
| `payments_jetonpresence` | 1 |
| `payments_paiement` | 3 |
| `public_publicamendement` | 0 |
| `validation_ecologicalreview` | 3 |
| `validation_economicreview` | 3 |
| `validation_industrialconsultation` | 2 |
| `validation_isoreview` | 3 |
| `validation_legisticreview` | 3 |
| `validation_schedulereview` | 3 |

Intégrité SQLite : `ok`. Violations de clés étrangères : 0. Ces contrôles ne vérifient pas la cohérence métier.

### États présents

- `norms_norme` : {"CTM_REVIEW": 3, "DRAFT": 1, "INTERNAL_REVIEW": 8, "PILOTAGE_REVIEW": 2, "PUBLISHED": 4}.
- `governance_ctcprocessus` : {"GEOSPATIAL": 4, "INDUSTRIAL": 3, "MULTI_REVIEW": 3, "RECEPTION": 4, "SIGNED_OUT": 3}.
- `governance_normecadrage` : {}.

### Versions de migrations déclarées dans la base

- `admin` : `0003_logentry_add_action_flag_choices` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `amendments` : `0001_initial` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `auth` : `0012_alter_user_first_name_max_length` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `contenttypes` : `0002_remove_content_type_name` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `core` : `0003_password_reset_code` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `documents` : `0002_alter_documentfile_options_and_more` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `experts` : `0007_expert_theme_preference` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `gemini_drafts` : `0003_draft_norm_type` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `governance` : `0012_affectation_wg_nullable` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `ia_agent` : `0008_ragdocument_ragchunk` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `meetings` : `0004_reunion_ctm_wg_document_reunionvote` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `messaging` : `0002_add_subject_status` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `mobileapp` : `0004_rename_mobileapp_e_user_id_4b7e3a_idx_mobileapp_e_user_id_34d23a_idx` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `norms` : `0011_normedocumentimport_norme` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `payments` : `0001_initial` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `public` : `0001_initial` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `sessions` : `0001_initial` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `token_blacklist` : `0013_alter_blacklistedtoken_options_and_more` (maximum lexical des noms appliqués ; pas une validation du graphe).
- `validation` : `0002_ecologicalreview_economicreview_and_more` (maximum lexical des noms appliqués ; pas une validation du graphe).

## 4. Empreintes des sources documentaires

- `Note_comparative_CNE_ITP_avec_propositions_denomination.pdf` : SHA-256 `1c9b1d6a2f14b1be461e8ef2edc550bfad6d92474238d675b2ad1df06befb118`.
- `Note_comparative_CNE_ITP_migration_plateforme_2026-1.pdf` : SHA-256 `4ffd83040ca8e1b969a923788dcd8b7180780ce5302a2057e9e559eb26b52443`.
- `Note_comparative_CNE_ITP_migration_plateforme_2026.docx` : SHA-256 `aa4883f5745c25b786421c0da0bd33bb2e3df2313ea2449fad8dba2eb1594e8a`.
- `Note_comparative_CNE_ITP_migration_plateforme_2026.pdf` : SHA-256 `4ffd83040ca8e1b969a923788dcd8b7180780ce5302a2057e9e559eb26b52443`.

## 5. Limites de cet inventaire

Lecture statique et contrôles locaux seulement. Les contrôles web/API ne sont pas testés par des requêtes mutantes ; aucune restauration, migration ou activation n’a été effectuée. Les volumes et identifiants doivent être recalculés sur une copie autorisée de la base réellement utilisée avant exécution. Les fichiers média référencés, leur contenu et les références stockées dans les JSON ou textes doivent être inclus dans le futur contrôle de conservation.


