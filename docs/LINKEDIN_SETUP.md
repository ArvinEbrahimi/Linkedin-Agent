# LinkedIn Integration Setup

LinkAid connects to LinkedIn in **read-only** mode — no posting or messaging.

## What you get

| Method | Data |
|--------|------|
| **OAuth (Sign In with LinkedIn)** | Name, email, profile picture, subject ID |
| **Data export ZIP** | Past posts, headline, about/summary (from your archive) |

## 1. Create a LinkedIn app

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create an app (needs a LinkedIn Page for verification)
3. Open **Products** → add **Sign In with LinkedIn using OpenID Connect**
4. **Auth** tab → add Redirect URL:
   ```
   http://localhost:8000/api/v1/linkedin/auth/callback
   ```
5. Copy **Client ID** and **Client Secret**

## 2. Configure LinkAid

Add to `.env`:

```env
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/v1/linkedin/auth/callback
UI_BASE_URL=http://localhost:8501
```

Restart the API: `make run`

## 3. Connect in UI

1. `make run-ui`
2. Open tab **Setup**
3. Click **Connect LinkedIn**
4. Authorize → you'll return to LinkAid automatically

## 4. Import data export (recommended for posts)

1. LinkedIn → **Settings & Privacy** → **Data privacy**
2. **Get a copy of your data** → select **Posts** and **Profile**
3. Download ZIP when ready
4. In LinkAid **Setup** tab → upload ZIP → **Import**

Imported posts feed the **Advisor** and **Strategy** modules.

## Production

Update redirect URI to your deployed API, e.g.:

```
https://api.yourdomain.com/api/v1/linkedin/auth/callback
```

Set `UI_BASE_URL` to your Streamlit URL.

## Limitations (by design)

- LinkedIn OAuth does **not** expose post analytics or connections via API
- No automated posting — suggest-only per product rules
- Browser extension (in-context on linkedin.com) is planned for a future phase
