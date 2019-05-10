### Authorization
#### Headers
Use *Authorization* header for user authorization 
(get it using `/auth/signup` and `/auth/login` methods)

Use *X-Status-Manager-Token* for status manager 
authorization (token is static)

#### Methods
- `/api/auth` - auth for Users
- `/api/wallet` - wallet management for Users
- `/api/operations` - operations statuses changing for Status Manager
- `/api/reports` - streaming reports generating in XML and CSV for Users and anybody

### Allowed transactions between operation statuses
DRAFT -> [PROCESSING, FAILED]

PROCESSING -> [ACCEPTED, FAILED]

ACCEPTED -> []

FAILED -> []

### Rates fetchin
https://api.exchangeratesapi.io/latest is used for rates fetching
