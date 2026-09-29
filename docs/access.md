# Accounts and organizations

## Create an account

Open `/signup`, enter your name, email, organization name, and a password of at least 10 characters. Signup creates a private organization with one empty facility. Verify your email before signing in. Verification links expire after 24 hours and work once. Resend verification from signup or login.

For local development, open the email in [Mailpit](http://localhost:8025). Mailpit captures messages locally; it does not deliver them to real inboxes. See [email setup](setup.md#email-verification).

## Manage your account

Open **Your account** from the sidebar or your avatar. Update your name, view your organization, role, join date, last sign-in, upload count, and active session count, or change your password. Password changes revoke every session.

Account deletion requires your password and typing `DELETE`. It removes sign-in access and anonymizes your profile. Shared facility records and their upload attribution stay with the organization. A sole administrator must assign another administrator before leaving an organization that has members or activity records.

## Organization and facility access

Administrators manage facilities and users only within their organization. Facility managers can upload, confirm drafts, and review reports only for their assigned facility. Multiple managers can share a facility. Dashboards, trends, scenarios, calculations, and reports apply these boundaries on the backend.

Use **Facilities & users** to create facilities or manage roles and assignments. Directly provisioned accounts are trusted administrator-created accounts and do not require email verification. Permission changes invalidate their sessions. An administrator cannot disable or demote their own account.

## Join another organization

1. The destination administrator opens **Your account**, enters your email under **Invite a facility manager**, selects a facility, and sends an invitation.
2. Open the invitation while signed in with that verified email. New users create and verify an account first, then reopen the invitation.
3. Review the destination organization and facility, then accept. Invitations expire after seven days and work once.
4. Sign in again. Your account moves to the destination organization as a facility manager. Your previous organization's records stay there.

An account belongs to one organization at a time. Invitations stop working if their issuing administrator leaves, is disabled, or loses administrator access.

## Existing installations and checks

The first upgrade places existing users and facilities into **College organization**, preserving records and assignments. New signup organizations cannot access that data. The administrator CLI creates a separate organization and empty facility for a new account; use invitations to join an existing organization.

`backend/tests/test_accounts.py` exercises verification, invitation acceptance, organization isolation, profile changes, session revocation, deletion, expired links, and mail failure rollback. `backend/tests/test_tenancy.py` covers facility access and reporting isolation. Tests use isolated databases, never the college ledger.
