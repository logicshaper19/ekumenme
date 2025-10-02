# Ekumen Organization Model

## Overview
Organizations enable multi-tenancy, allowing cooperatives, advisory firms, and farm enterprises to manage multiple users and farms.

---

## Organization Types

### 1. **FARM** (Individual Farm Enterprise)
```
Example: "Ferme Tuferes EARL"
- Owner: Single farmer or family
- Members: Farm owner + employees/workers
- Farms: 1-3 farms (owned by the farmer)
- Use case: Individual farmer managing their own operations
```

**Roles:**
- **Owner**: Full control, can add/remove members, manage billing
- **Admin**: Can manage farm data, add workers
- **Worker**: Can log interventions, view farm data
- **Viewer**: Read-only access (family member, accountant)

### 2. **COOPERATIVE** (Agricultural Cooperative)
```
Example: "Coopérative Agricole du Sud-Ouest"
- Owner: Cooperative management
- Members: 50-500 farmers (members of the cooperative)
- Farms: 50-500 farms (owned by individual farmers)
- Use case: Cooperative providing services to member farmers
```

**Roles:**
- **Owner**: Cooperative director
- **Admin**: Cooperative staff managing member services
- **Advisor**: Agronomists providing recommendations
- **Member**: Individual farmers (can see their own farm + aggregated data)
- **Viewer**: Read-only access to aggregated data

**Key Features:**
- Aggregated analytics across all member farms
- Bulk product purchasing
- Shared knowledge base
- Regulatory compliance tracking

### 3. **ADVISOR** (Advisory Firm / Consulting)
```
Example: "AgroConseil Expert"
- Owner: Consulting firm owner
- Members: Agronomists/consultants
- Farms: 20-100 client farms (owned by clients)
- Use case: Advisory firm managing multiple client farms
```

**Roles:**
- **Owner**: Firm owner, manages billing and staff
- **Admin**: Senior consultant, manages client relationships
- **Advisor**: Agronomist providing recommendations to clients
- **Viewer**: Junior consultant, read-only access

**Key Features:**
- Client farm management
- Recommendation tracking
- Intervention planning for clients
- Client reporting

### 4. **INPUT_COMPANY** (Phyto Product Supplier)
```
Example: "Bayer CropScience France"
- Owner: Company management
- Members: Sales reps, technical advisors
- Farms: 100-1000+ farms (customers)
- Use case: Track product usage, provide technical support
```

**Roles:**
- **Owner**: Company management
- **Admin**: Regional manager
- **Sales_Rep**: Sales representative
- **Technical_Advisor**: Provides product recommendations
- **Viewer**: Analytics team

**Key Features:**
- Product usage tracking
- Customer farm analytics
- Recommendation engine (for their products)
- Compliance monitoring
- Sales analytics

### 5. **RESEARCH_INSTITUTE** (Research & Development)
```
Example: "INRAE - Institut National de Recherche"
- Owner: Institute director
- Members: Researchers
- Farms: 10-50 trial farms (anonymized data from many farms)
- Use case: Agricultural research, data analysis
```

**Roles:**
- **Owner**: Institute director
- **Researcher**: Can access anonymized data
- **Viewer**: Students, interns

**Key Features:**
- Anonymized data access
- Trial management
- Data export for analysis
- Research project tracking

### 6. **GOVERNMENT_AGENCY** (Internal - Ekumen Platform)
```
Example: "Ekumen Platform"
- Owner: Ekumen team
- Members: Ekumen staff
- Farms: None (platform administration only)
- Use case: Platform administration, public knowledge base curation
```

**Roles:**
- **Owner**: Ekumen CEO/CTO
- **Admin**: Ekumen staff managing platform

**Key Features:**
- Platform-wide analytics
- Public knowledge base curation (shared with all users)
- System configuration
- User/organization management

**Note:** This is an internal organization type, not available for customer creation.

---

## Organization Membership Model

### Database Schema
```sql
organization_memberships:
  - organization_id (which organization)
  - user_id (which user)
  - role (owner, admin, advisor, member, viewer, worker, sales_rep, researcher)
  - status (active, inactive, pending_invitation)
  - joined_at (when they joined)
  - invited_by (who invited them)
```

### Membership Lifecycle

#### 1. Creating an Organization
```
User clicks "Create Organization"
  → Fills form (name, type, SIRET, etc.)
  → System creates organization
  → User becomes "owner" automatically
  → Organization status = "pending_approval" (for Ekumen admin review)
```

#### 2. Inviting Members
```
Owner/Admin clicks "Invite Member"
  → Enters email + role
  → System sends invitation email
  → Membership status = "pending_invitation"
  → User clicks link, accepts invitation
  → Membership status = "active"
```

#### 3. Removing Members
```
Owner/Admin clicks "Remove Member"
  → Membership status = "inactive"
  → User loses access to organization
  → User's conversations in that org are archived
```

---

## Farm Access Control

### Database Schema
```sql
organization_farm_access:
  - organization_id (which organization)
  - farm_siret (which farm)
  - access_type (owner, advisor, viewer)
  - granted_by (who granted access)
  - granted_at (when access was granted)
```

### Access Types

#### **OWNER**
- Full control over farm data
- Can grant/revoke access to others
- Can delete farm data
- Can link farm to other organizations

#### **ADVISOR**
- Can view all farm data
- Can add recommendations
- Can create intervention plans
- Cannot delete data

#### **VIEWER**
- Read-only access to farm data
- Can view reports
- Cannot edit anything

### Farm Access Scenarios

#### Scenario 1: Individual Farmer
```
User: Jean Dupont (farmer)
Organization: "Ferme Dupont EARL" (FARM type)
Farm: SIRET 12345678901234

organization_farm_access:
  - organization_id: Ferme Dupont EARL
  - farm_siret: 12345678901234
  - access_type: owner
```

#### Scenario 2: Farmer + Cooperative
```
User: Jean Dupont (farmer)
Organizations:
  1. "Ferme Dupont EARL" (FARM type) - owner
  2. "Coopérative ABC" (COOPERATIVE type) - member

Farm: SIRET 12345678901234

organization_farm_access:
  - organization_id: Ferme Dupont EARL
  - farm_siret: 12345678901234
  - access_type: owner
  
  - organization_id: Coopérative ABC
  - farm_siret: 12345678901234
  - access_type: viewer  (cooperative can see aggregated data)
```

#### Scenario 3: Farmer + Advisor
```
User: Jean Dupont (farmer)
Organizations:
  1. "Ferme Dupont EARL" (FARM type) - owner
  2. "AgroConseil Expert" (ADVISOR type) - client

Farm: SIRET 12345678901234

organization_farm_access:
  - organization_id: Ferme Dupont EARL
  - farm_siret: 12345678901234
  - access_type: owner
  
  - organization_id: AgroConseil Expert
  - farm_siret: 12345678901234
  - access_type: advisor  (advisor can view + add recommendations)
```

---

## Permission System

### Role-Based Permissions

```python
PERMISSIONS = {
    "owner": {
        "view_farm_data": True,
        "edit_farm_data": True,
        "delete_farm_data": True,
        "manage_members": True,
        "grant_farm_access": True,
        "view_billing": True,
        "manage_billing": True,
    },
    "admin": {
        "view_farm_data": True,
        "edit_farm_data": True,
        "delete_farm_data": False,
        "manage_members": True,
        "grant_farm_access": True,
        "view_billing": True,
        "manage_billing": False,
    },
    "advisor": {
        "view_farm_data": True,
        "edit_farm_data": True,  # Can add recommendations
        "delete_farm_data": False,
        "manage_members": False,
        "grant_farm_access": False,
        "view_billing": False,
        "manage_billing": False,
    },
    "member": {
        "view_farm_data": True,  # Only their own farm
        "edit_farm_data": True,  # Only their own farm
        "delete_farm_data": False,
        "manage_members": False,
        "grant_farm_access": False,
        "view_billing": False,
        "manage_billing": False,
    },
    "viewer": {
        "view_farm_data": True,
        "edit_farm_data": False,
        "delete_farm_data": False,
        "manage_members": False,
        "grant_farm_access": False,
        "view_billing": False,
        "manage_billing": False,
    },
}
```

### Permission Checks

```python
async def check_permission(user_id, organization_id, permission):
    # Get user's role in organization
    membership = await get_membership(user_id, organization_id)
    if not membership:
        return False
    
    # Check if role has permission
    return PERMISSIONS[membership.role].get(permission, False)

# Usage
if await check_permission(user_id, org_id, "edit_farm_data"):
    # Allow edit
else:
    # Deny
```

---

## Ekumen Platform Roles

### Superadmin (Ekumen Team)
```
Permissions:
  - View all organizations
  - Approve/reject new organizations
  - Suspend organizations
  - View all user data (for support)
  - Access analytics dashboard
  - Manage platform settings
  - View system logs
```

**Use Cases:**
- Customer support
- Platform monitoring
- Fraud detection
- Feature usage analysis

### Organization Owner
```
Permissions:
  - Full control over their organization
  - Manage members and roles
  - Grant farm access
  - View billing and usage
  - Configure organization settings
```

### Organization Admin
```
Permissions:
  - Manage members (except owner)
  - Grant farm access
  - View billing (but not manage)
  - Configure some organization settings
```

---

## Implementation Notes

### 1. Organization Context - ONE Per Session (No Switching)

**Decision:** Follow ChatGPT Teams pattern - NO mid-session organization switching.

#### Scenario 1: User Belongs to ONE Organization (90% of cases)
```
User logs in → Automatically in their organization context
JWT token contains: user_id + organization_id
All API calls filtered by organization_id from token
No selection needed!
```

#### Scenario 2: User Belongs to MULTIPLE Organizations (10% of cases)
```
User logs in → Sees "Select Organization" screen ONCE
User selects "Ferme Dupont EARL"
JWT token contains: user_id + organization_id
All conversations, farms, data filtered by this organization

To switch to "Coopérative ABC":
  → Log out and log back in (or use different browser tab)
  → Select different organization
  → Get new JWT token with different org_id
```

**Why no mid-session switching?**
- ✅ Simpler UX (like ChatGPT Teams)
- ✅ Clearer context (no confusion about which org you're in)
- ✅ Simpler implementation (org_id in JWT, no state management)
- ✅ More secure (can't accidentally leak data between orgs)

### 2. Data Isolation
```
Conversations are scoped to organization:
  - conversation.organization_id = current_org_id
  - User can only see conversations in current organization
  - Switching organization = different conversation list
```

### 3. Farm Data Access
```
When user queries farm data:
  1. Check user's current organization
  2. Check organization_farm_access for this farm
  3. If access exists, return data
  4. If no access, return 403 Forbidden
```

---

## Summary

**Organizations enable:**
1. ✅ Multi-user collaboration (cooperatives, advisory firms)
2. ✅ Role-based access control
3. ✅ Farm data sharing with permission control
4. ✅ Isolated conversation contexts
5. ✅ Scalable multi-tenancy
6. ✅ Knowledge base sharing (internal/shared/public)

**Keep it simple:**
- ✅ Start with FARM COOPERATIVE types with ADVISOR as a role  and INPUT_COMPANY from Ephy db
- ✅ **ONE organization per session** (no mid-session switching)
- ✅ Organization ID embedded in JWT token
- ✅ Enforce permissions at API level
- ✅ Like ChatGPT Teams - log out to switch workspace

