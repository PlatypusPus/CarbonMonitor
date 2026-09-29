# Facilities and user access

Each facility is an isolated workspace in the shared database. A facility manager belongs to one facility; multiple managers can belong to the same facility. Administrators can access every facility. This is facility-level tenancy within one organization, not separate customer organizations with independent administrators.

## Administrator workflow

1. Sign in and open **Facilities & users**.
2. Use **Add facility** to create a site and enter its location, type, and optional region code.
3. Open **Users & access**, choose **Add user**, and supply a name, email, initial password, role, and facility assignment.
4. Share sign-in details privately. Passwords are hashed and are never returned by the API.
5. Use **Edit** to change a name, role, facility assignment, or active status. Deactivation blocks API access and login. Changes to permissions revoke refresh sessions. An administrator cannot disable or demote their own account.

The header selector switches dashboards, trends, drafts, scenarios, and PDF exports between all facilities and a selected facility. The administration directory always shows the complete organization.

## Facility manager workflow

Managers sign in with their individual account, upload to their assigned facility, review its shared draft queue, and confirm records. They can edit their facility details and view its dashboards, anomaly results, scenarios, and PDFs. Managers cannot create facilities, manage accounts, or read and modify another facility's records, even by changing a URL or API parameter.

Reassigning a manager changes their access immediately on the backend. Their previous uploads stay with the original facility. Accounts without a facility assignment cannot access aggregate reports; an administrator must assign them first. Reload or sign in again after an assignment changes to refresh the displayed workspace.

## Verification

`backend/tests/test_tenancy.py` covers account creation, duplicate emails, login, assignment changes, deactivation, cross-facility reads and writes, shared draft confirmation, and PDF isolation. The PostgreSQL upload integration tests verify independent manager uploads and facility-scoped monthly aggregates. Test data belongs only in `carbontrace_e2e`, never in the college database.
