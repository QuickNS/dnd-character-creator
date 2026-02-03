# Server-Side Session Configuration

This application uses Flask-Session with filesystem storage for server-side sessions.

## Local Development

Sessions are stored in `./flask_session/` directory (auto-created).

## Azure App Service Deployment

### Configuration:

1. **Enable ARR Affinity** (usually enabled by default):
   - Azure Portal → App Service → Configuration → General Settings
   - Set "ARR affinity" to **On**

2. **Session Lifetime**: 24 hours (configurable in app.py)

3. **Session Storage**: 
   - Local filesystem (`./flask_session/`)
   - Session files automatically cleaned up after expiration

### Why ARR Affinity?

ARR (Application Request Routing) affinity ensures users stick to the same instance, allowing filesystem sessions to work correctly. This is:
- ✅ Free (no additional Azure costs)
- ✅ Sufficient for character creator traffic patterns
- ✅ Eliminates cookie size limits (no more 4KB warnings!)

### Scaling Considerations

If you need to scale beyond a single instance without affinity:
- Consider migrating to Azure Cache for Redis
- Cost: ~$15/month (Basic C0 tier)
- Update app.py configuration to use Redis backend

## Session Cleanup

Session files in `./flask_session/` are automatically managed:
- Expired sessions cleaned on access
- No manual cleanup needed
- Directory should be excluded from git (via .gitignore)
