# 🔐 Secure API Configuration Setup

## ⚠️ IMPORTANT SECURITY NOTICE

**NEVER commit API keys to version control!** Always use environment variables for sensitive configuration.

## 🚀 Quick Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual API keys:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Generate a strong SECRET_KEY:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## 🔑 API Key Configuration

### Required API Keys

1. **SECRET_KEY** (Required for security)
   - Generate a strong random string (see command above)
   - Used for JWT token signing and session security

2. **OPENAI_API_KEY** (Required for AI functionality)
   - Get from: https://platform.openai.com/api-keys
   - Format: `sk-...`

3. **WEATHER_API_KEY** (Required for weather data)
   - Get from: https://www.weatherapi.com/
   - Free tier available with 1M calls/month

### Optional API Keys

4. **ELEVENLABS_API_KEY** (For voice synthesis)
   - Get from: https://elevenlabs.io/
   - Only needed if using voice features

5. **METEO_FRANCE_API_KEY** (For French weather data)
   - Get from: Météo-France API
   - Alternative weather data source

## 📝 Environment File Example

```env
# Security (REQUIRED)
SECRET_KEY=your_generated_secret_key_here

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-your_openai_key_here

# Weather API (REQUIRED)
WEATHER_API_KEY=your_weather_api_key_here

# Voice Processing (OPTIONAL)
ELEVENLABS_API_KEY=sk_your_elevenlabs_key_here

# Additional APIs (OPTIONAL)
METEO_FRANCE_API_KEY=your_meteo_france_key_here
```

## ✅ Verification

After setting up your `.env` file, test the configuration:

```bash
cd Ekumen-assistant
python -c "from app.core.config import settings; print('✅ Configuration loaded successfully')"
```

## 🔒 Security Best Practices

1. **Never share API keys** in chat, email, or version control
2. **Rotate keys regularly** (every 3-6 months)
3. **Use different keys** for development and production
4. **Monitor API usage** for unusual activity
5. **Revoke unused keys** immediately

## 🚨 If API Keys Were Compromised

If you accidentally shared API keys:

1. **Immediately revoke/regenerate** the keys in your service dashboards
2. **Update your `.env` file** with new keys
3. **Check for unauthorized usage** in your API dashboards
4. **Consider enabling API usage alerts**

## 📞 Support

If you need help with API key setup, check the respective service documentation:
- OpenAI: https://platform.openai.com/docs
- WeatherAPI: https://www.weatherapi.com/docs/
- ElevenLabs: https://docs.elevenlabs.io/
