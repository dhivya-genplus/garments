# Enterprise User Password Reset & Recovery Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-AUTH-002`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, security guardrails, rate limiting, cryptographic token handling, Zod validation schema, TypeScript interfaces, and backend API integration for the **User Password Reset & Credential Recovery Desk** (`SCR-AUTH-002`).

In an enterprise ERP containing sensitive financial ledgers, GST tax filings, and trade secrets, credential recovery must balance rapid user access with strict security standards:
1. **Multi-Tenant Account Disambiguation**: In multi-company environments, username or employee email must resolve within the user's specific tenant scope without leaking corporate existence to unauthorized probes.
2. **Cryptographic Token Verification**: Time-bounded, single-use cryptographic recovery tokens (valid for 15 minutes) with secure URL delivery (`/reset-password?token=...`).
3. **Enterprise Password Complexity Policies**: Enforcing robust entropy standards:
   - Minimum 8 characters (recommended $\ge 12$)
   - At least 1 uppercase letter ($[A-Z]$)
   - At least 1 lowercase letter ($[a-z]$)
   - At least 1 numeric digit ($[0-9]$)
   - At least 1 special symbol ($[!@#$%^&*]$)
   - Disallowing last 3 historical passwords.
4. **Brute-Force & Abuse Mitigation**: Rate limiting requests to a maximum of 3 requests per IP/account within a 15-minute sliding window, accompanied by constant-time response latency to prevent email enumeration attacks.

### 1.2 Scope
- **Backend Endpoints**: `/api/v1/auth/password-reset-request/` and `/api/v1/auth/password-reset-confirm/`.
- **Target Route**: `/forgot-password` and `/reset-password` (Next.js route: `app/(auth)/forgot-password/page.tsx` & `app/(auth)/reset-password/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 1 — Authentication & RBAC` |
| **Screen ID** | `SCR-AUTH-002` |
| **Frontend Route** | `/forgot-password` (Request) & `/reset-password` (Confirm) |
| **File Location** | `app/(auth)/forgot-password/page.tsx` & `app/(auth)/reset-password/page.tsx` |
| **Required Privilege** | Public / Unauthenticated (Protected by IP rate limiting and CAPTCHA) |
| **Authorized Roles** | All registered users (`SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER`) |
| **Country Pack** | `IN` (India: Mobile SMS OTP verification supported with $+91$ prefix) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|

| `POST` | `/api/v1/auth/password-reset-request/` | Public (Rate Limited) | Submit email/username to dispatch a secure one-time password reset link |

| `POST` | `/api/v1/auth/password-reset-confirm/` | Public (Token Verified)| Validate token and commit new enterprise password |

| `POST` | `/api/v1/auth/change-password/` | Authenticated | Change password from inside the app using current password |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
|                                              GARMENTS ERP ENTERPRISE CLOUD                                                  |
+-----------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                             |
|                                   +-------------------------------------------------------+                                 |
|                                   |  [ LOGO: ABC TEXTILES ERP ]                           |                                 |
|                                   |  Reset Your Account Password                          |                                 |
|                                   |  Enter your registered email address or employee ID.  |                                 |
|                                   +-------------------------------------------------------+                                 |
|                                   |                                                       |                                 |
|                                   |  Company Code (Optional for Single Tenant):           |                                 |
|                                   |  [ ABC-TEX                                          ] |                                 |
|                                   |                                                       |                                 |
|                                   |  Registered Email / Username:                         |                                 |
|                                   |  [ arun.kumar@abctextiles.com                       ] |                                 |
|                                   |                                                       |                                 |
|                                   |  [ Send Password Reset Link (Enter)                 ] |                                 |
|                                   |                                                       |                                 |
|                                   |  ------------------------ OR -----------------------  |                                 |
|                                   |                                                       |                                 |
|                                   |  [ Return to Secure Login Screen                    ] |                                 |
|                                   |                                                       |                                 |
|                                   +-------------------------------------------------------+                                 |
|                                   | (i) If an active account matches these credentials,   |                                 |
|                                   | a recovery email will be dispatched within 2 minutes. |                                 |
|                                   +-------------------------------------------------------+                                 |
|                                                                                                                             |
+-----------------------------------------------------------------------------------------------------------------------------+
| STEP 2: PASSWORD RESET CONFIRMATION SCREEN (`/reset-password?token=XYZ...`)                                                 |
|                                   +-------------------------------------------------------+                                 |
|                                   |  Set New Enterprise Password                          |                                 |
|                                   |                                                       |                                 |
|                                   |  New Password:                                        |                                 |
|                                   |  [ ******************                             (o) ] |                                 |
|                                   |  Password Strength: [████████████████████] STRONG     |                                 |
|                                   |  [v] Minimum 8 characters                             |                                 |
|                                   |  [v] At least one uppercase letter (A-Z)              |                                 |
|                                   |  [v] At least one numeric digit (0-9)                 |                                 |
|                                   |  [v] At least one special symbol (!@#$%^&*)           |                                 |
|                                   |                                                       |                                 |
|                                   |  Confirm New Password:                                |                                 |
|                                   |  [ ******************                             (o) ] |                                 |
|                                   |                                                       |                                 |
|                                   |  [ Commit Password & Log In (Enter)                 ] |                                 |
|                                   +-------------------------------------------------------+                                 |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Recovery Request (`/forgot-password`)**:
   - User inputs registered email or username and optional Company Code.
   - Clicks **Send Password Reset Link**.
   - UI displays a neutral confirmation message: *"If an account matches your details, password reset instructions have been dispatched."* (Prevents account discovery attacks).
2. **Email / SMS Dispatch**:
   - Server creates a cryptographic HMAC-SHA256 token linked to user ID with a 15-minute expiry.
   - Sends HTML email with direct link: `https://erp.abctextiles.com/reset-password?token=a8f9c2...`
3. **Password Commitment (`/reset-password`)**:
   - User clicks link, opening the password creation form.
   - User types new password; real-time client-side evaluator checks strength and policy adherence.
   - Upon successful submission, backend hashes password with Argon2/PBKDF2, revokes all existing refresh tokens, and displays success notification before redirecting to `/login`.

### 4.2 Edge-Case Handling
- **Expired Token**: If the user clicks the link after 15 minutes, the UI shows: *"This reset link has expired for security reasons. Please request a new link."*
- **Already Used Token**: Tokens are single-use; a second attempt returns a token invalid error.
- **Enumeration Defense**: The server always returns `HTTP 200 OK` with identical timing ($~250\text{ms}$) regardless of whether the email exists in the database.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Form | Field Label | Field Key | Input Type | Required | Validation & Rules |
|---|---|---|---|---|---|
| **Request** | Company Code | `company_code` | Text | No | Alphanumeric, max 20 chars |
| **Request** | Email / Username | `email_or_username` | Text / Email | Yes | Valid email or username string |
| **Confirm** | Reset Token | `token` | Hidden | Yes | 64-character hex cryptographic token |
| **Confirm** | New Password | `new_password` | Password | Yes | $\ge 8$ chars, $[A-Z]$, $[a-z]$, $[0-9]$, $[!@#$%^&*]$ |
| **Confirm** | Confirm Password | `confirm_password` | Password | Yes | Must match `new_password` identically |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Cryptographic Token Expiry Invariant
Given token creation timestamp $T_{\text{created}}$ and current verification timestamp $T_{\text{verify}}$:

$$\Delta T = T_{\text{verify}} - T_{\text{created}}$$

$$\text{Token Validity} = \begin{cases} 
\text{VALID}, & \text{if } \Delta T \le 900\text{ seconds } (15\text{ minutes}) \land \text{is\_used} = \text{false} \\ 
\text{EXPIRED / INVALID}, & \text{otherwise} 
\end{cases}$$

### 6.2 Password Entropy Estimation ($H$)
Given character pool size $N$ and password length $L$:

$$N = N_{\text{upper}} (26) + N_{\text{lower}} (26) + N_{\text{digits}} (10) + N_{\text{symbols}} (32) = 94$$

$$H = L \times \log_2(N) \approx L \times 6.55\text{ bits}$$

$$\text{Policy Enforces: } L \ge 8 \implies H \ge 52.4\text{ bits (Moderate to Strong)}$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Real-Time Password Complexity Gauge**:
   - As the user types their new password, 4 checkmarks dynamically illuminate from gray to green:
     - 8+ characters
     - 1+ uppercase letter
     - 1+ number
     - 1+ special symbol
2. **Password Visibility Toggle**:
   - Eye icon allows toggling between masked `••••••••` and cleartext.
3. **Copy-Paste Confirmation Lockout**:
   - Pasting into the `confirm_password` field is disabled to prevent accidental duplication of typos.

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Password Reset Request (`POST /api/v1/auth/password-reset-request/`)

```json
{
  "email_or_username": "arun.kumar@abctextiles.com",
  "company_code": "ABC-TEX"
}
```

```json
{
  "success": true,
  "message": "If this account is registered in our enterprise directory, a password reset link has been dispatched to your email address."
}
```

### 8.2 Password Reset Confirm (`POST /api/v1/auth/password-reset-confirm/`)

```json
{
  "token": "7b3f9a2e8c1d4a0b5f6e8d2c1b4a9f3e",
  "new_password": "SecureEnterprise#2026",
  "confirm_password": "SecureEnterprise#2026"
}
```

```json
{
  "success": true,
  "message": "Your enterprise password has been updated successfully. Please log in with your new credentials."
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(auth)/
├── forgot-password/
│   └── page.tsx                         # Request reset link form
├── reset-password/
│   └── page.tsx                         # Commit new password with token
└── components/
    ├── PasswordResetCard.tsx            # Styled card container
    ├── PasswordStrengthMeter.tsx        # Animated entropy bar and criteria checks
    └── ResetSuccessBanner.tsx           # Confirmation dialog with login redirect
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

export const PasswordResetRequestSchema = z.object({
  email_or_username: z.string().min(3, { message: "Enter a valid username or email." }),
  company_code: z.string().optional(),
});

export const PasswordResetConfirmSchema = z
  .object({
    token: z.string().min(10, { message: "Invalid or missing recovery token." }),
    new_password: z
      .string()
      .min(8, { message: "Password must be at least 8 characters." })
      .regex(/[A-Z]/, { message: "Password must contain at least one uppercase letter." })
      .regex(/[a-z]/, { message: "Password must contain at least one lowercase letter." })
      .regex(/[0-9]/, { message: "Password must contain at least one numeric digit." })
      .regex(/[!@#$%^&*(),.?":{}|<>]/, { message: "Password must contain at least one special symbol." }),
    confirm_password: z.string().min(1, { message: "Please confirm your new password." }),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match.",
    path: ["confirm_password"],
  });

export type PasswordResetRequestFormData = z.infer<typeof PasswordResetRequestSchema>;
export type PasswordResetConfirmFormData = z.infer<typeof PasswordResetConfirmSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface IPasswordResetRequestDTO {
  email_or_username: string;
  company_code?: string;
}

export interface IPasswordResetConfirmDTO {
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface IPasswordResetResponseDTO {
  success: boolean;
  message: string;
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Enter` | Submit Request / Commit New Password | Active Form |
| `Esc` | Return to `/login` | Recovery View |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | Centered 480px security card with background enterprise branding |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | Centered 420px card |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Full width mobile form with prominent touch inputs |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Token expired ($>15\text{m}$) | Red alert card: *"This link has expired"* | Button: *"Request New Link"* |
| Passwords do not match | Red field border on confirm input | Match passwords |
| Rate limit exceeded ($>3\text{ requests}$) | Amber banner: *"Too many attempts. Please try again in 15 minutes."* | Cooldown timer displayed |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Spinner inside button with text *"Securing Link..."*.
- **Success State**: Green card with animated checkmark and 5-second countdown to `/login`.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- All inputs have `<label>` tags with matching `htmlFor` references.
- Password strength announcements use `aria-live="polite"`.
- Error messages explicitly associated via `aria-describedby`.

---

## 17. Security, RBAC, and Audit Logging

- **Session Invalidation**: Committing a new password automatically invalidates all active JWT refresh tokens across all devices.
- **Audit Logging**: Every reset request and confirmation logs user IP, user-agent, and timestamp to `ta_security_audit`.
- **Zero Plaintext**: Passwords are never logged in plaintext or transmitted in GET query parameters.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Requesting reset returns `HTTP 200` with generic success message regardless of email existence.
2. Token expires after 15 minutes and cannot be reused.
3. Password rejecting strings lacking special characters or numbers.

---

## 19. Performance Budgets and Optimization Targets

- Page load: $< 300\text{ms}$.
- Request submission: $< 300\text{ms}$.

---

## 20. Future Enhancements and Scalability Roadmap

1. **SMS OTP Recovery**: Delivering 6-digit OTP codes via Indian SMS gateways (DND-compliant).
2. **Hardware Security Key (FIDO2/WebAuthn)**: Self-service recovery using YubiKey or biometric authentication.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Security Officer** | Suresh Balakrishnan (CISO) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Engineering Lead** | Arun Kumar | 16/10/2026 | **APPROVED** |
