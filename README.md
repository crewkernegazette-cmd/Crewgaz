# Crewkerne Gazette

## Production domains
- Frontend (static site): https://crewkernegazette.co.uk
- Backend API: https://api.crewkernegazette.co.uk

## Frontend env (prod)
- CRA:  REACT_APP_API_URL=https://api.crewkernegazette.co.uk

## Cookies
- Set-Cookie flags: HttpOnly; Secure; SameSite=None; Domain=.crewkernegazette.co.uk; Path=/
- All client requests use credentials (fetch) / withCredentials (axios).

## Test API health
```javascript
fetch('https://api.crewkernegazette.co.uk/api/health', { credentials: 'include' })
  .then(r => r.json()).then(console.log);
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   cd frontend && npm install
   cd ../backend && pip install -r requirements.txt
   ```
3. Set up your database
4. Run the application
