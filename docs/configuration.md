# Kalendar Configuration Guide

This guide explains how to configure Kalendar for your calendar sources and display preferences.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration File Location](#configuration-file-location)
- [Configuration Options](#configuration-options)
  - [Refresh Settings](#refresh-settings)
  - [Calendar Sources](#calendar-sources)
  - [Display Settings](#display-settings)
- [Setting Up Calendar Sources](#setting-up-calendar-sources)
  - [Google Calendar](#google-calendar)
  - [Apple iCloud Calendar (CalDAV)](#apple-icloud-calendar-caldav)
  - [Nextcloud Calendar (CalDAV)](#nextcloud-calendar-caldav)
- [Credentials Management](#credentials-management)
- [Validation Rules](#validation-rules)
- [Troubleshooting](#troubleshooting)

## Quick Start

1. Copy the example configuration:
   ```bash
   cp config/example.config.yaml config/config.yaml
   ```

2. Edit `config/config.yaml` with your preferences

3. Set up calendar credentials (see [Setting Up Calendar Sources](#setting-up-calendar-sources))

4. Test your configuration:
   ```bash
   uv run kalendar refresh --config config/config.yaml --simulator
   ```

## Configuration File Location

Default locations (in order of precedence):

1. Path specified via `--config` flag: `uv run kalendar refresh --config /path/to/config.yaml`
2. `config/config.yaml` in the project root
3. `/etc/kalendar/config.yaml` (system-wide on Raspberry Pi)

## Configuration Options

### Refresh Settings

```yaml
refresh_hour: 0  # Hour to refresh calendar data (0-23)
timezone: "America/New_York"  # IANA timezone string
```

**`refresh_hour`** (required)
- Type: Integer (0-23)
- Default: None
- Description: Hour of day to automatically refresh calendar data
- Examples:
  - `0` = midnight
  - `6` = 6 AM
  - `18` = 6 PM
- **Validation**: Must be between 0 and 23

**`timezone`** (required)
- Type: String (IANA timezone)
- Default: None
- Description: Timezone used for display and scheduling
- Examples:
  - `"America/New_York"` (US Eastern)
  - `"America/Los_Angeles"` (US Pacific)
  - `"Europe/London"` (UK)
  - `"Asia/Tokyo"` (Japan)
  - `"UTC"` (Coordinated Universal Time)
- **Validation**: Must be a valid IANA timezone string
- Find your timezone: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

**`week_start_day`** (optional)
- Type: Integer (0-6)
- Default: 0 (Monday)
- Description: First day of the week in calendar display
- Values:
  - `0` = Monday (common in Europe)
  - `1` = Tuesday
  - `2` = Wednesday
  - `3` = Thursday
  - `4` = Friday
  - `5` = Saturday
  - `6` = Sunday (common in North America)
- **Validation**: Must be between 0 and 6

### Calendar Sources

```yaml
calendar_sources:
  - id: "google-primary"
    name: "My Google Calendar"
    source_type: "google"
    calendar_id: "primary"
    enabled: true
    color: "#4285F4"  # Optional
```

**`calendar_sources`** (required)
- Type: List of calendar source objects
- Description: List of calendars to display
- **Validation**: At least one source must be enabled

**Calendar Source Object:**

- **`id`** (required): Unique identifier for this source
  - Type: String
  - Must be unique across all sources
  - Example: `"google-primary"`, `"icloud-family"`

- **`name`** (required): Display name for this calendar
  - Type: String
  - Max length: 100 characters
  - Example: `"Family Calendar"`, `"Work Schedule"`

- **`source_type`** (required): Type of calendar source
  - Type: String (enum)
  - Values: `"google"` or `"caldav"`
  - `"google"`: Google Calendar
  - `"caldav"`: iCloud, Nextcloud, or any CalDAV-compatible calendar

- **`calendar_id`** (required): Calendar identifier
  - Type: String
  - Format depends on `source_type`:
    - Google: `"primary"` or specific calendar email (e.g., `"family@group.calendar.google.com"`)
    - CalDAV: Full calendar URL (e.g., `"https://caldav.icloud.com/XXXXX/calendars/YYYYY/"`)

- **`enabled`** (optional): Whether to include events from this source
  - Type: Boolean
  - Default: `true`
  - Set to `false` to temporarily disable a calendar without removing it

- **`color`** (optional): Color hint for this calendar
  - Type: String (hex color)
  - Not used in current 3-color e-paper display
  - Reserved for future use
  - Example: `"#4285F4"`, `"#0B8043"`

### Display Settings

```yaml
display:
  max_daily_events: 5
  layout: "horizontal"
```

**`max_daily_events`** (required)
- Type: Integer (> 0)
- Default: 5
- Description: Maximum number of events to show in "Today's Events" section
- If more events exist, an overflow indicator is shown
- **Validation**: Must be greater than 0
- Recommended: `5` (fits well on 7.5" display with monthly view)

**`layout`** (required)
- Type: String (enum)
- Default: `"horizontal"`
- Values:
  - `"horizontal"`: Landscape orientation (800×480)
  - `"vertical"`: Portrait orientation (480×800) - not yet implemented
- Note: Current version only supports `"horizontal"`

## Setting Up Calendar Sources

### Google Calendar

#### 1. Create Google Cloud Project and Enable API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable Google Calendar API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

#### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure consent screen if prompted
4. Select "Desktop app" as application type
5. Download credentials JSON file
6. Save as `config/google_credentials.json`

#### 3. Authorize Access

On your development machine (with a browser):

```bash
uv run kalendar auth google --credentials config/google_credentials.json
```

This will:
1. Open a browser for Google OAuth flow
2. Ask you to sign in and grant permissions
3. Save refresh token to `config/google_token.json`

#### 4. Add to Configuration

```yaml
calendar_sources:
  - id: "google-primary"
    name: "My Google Calendar"
    source_type: "google"
    calendar_id: "primary"  # Or specific calendar ID
    enabled: true
```

**Finding specific calendar IDs:**
1. Open Google Calendar in browser
2. Click settings (gear icon) > "Settings"
3. Click on the calendar in left sidebar
4. Scroll to "Integrate calendar"
5. Copy "Calendar ID"

#### 5. Create Credentials File

Create `config/credentials.json`:

```json
{
  "google": {
    "token_file": "config/google_token.json",
    "credentials_file": "config/google_credentials.json"
  }
}
```

### Apple iCloud Calendar (CalDAV)

#### 1. Generate App-Specific Password

1. Go to [Apple ID management](https://appleid.apple.com/)
2. Sign in with your Apple ID
3. Navigate to "Security" section
4. Under "App-Specific Passwords", click "Generate Password"
5. Enter a label (e.g., "Kalendar")
6. Copy the generated password (format: `xxxx-xxxx-xxxx-xxxx`)

#### 2. Discover Calendar URLs

**For @icloud.com email addresses (auto-detected):**
```bash
uv run kalendar discover-caldav \
  --username your_apple_id@icloud.com \
  --password xxxx-xxxx-xxxx-xxxx
```

**For non-@icloud.com Apple IDs (Gmail, Yahoo, etc.):**
```bash
uv run kalendar discover-caldav \
  --username your_apple_id@gmail.com \
  --service icloud \
  --password xxxx-xxxx-xxxx-xxxx
```

Note: Many people use Gmail or other email addresses as their Apple ID. If your Apple ID is not an @icloud.com address, use the `--service icloud` parameter to specify that you want to connect to Apple's iCloud CalDAV server.

Output will show:
```
Found 3 calendars:
  1. Personal
     URL: https://caldav.icloud.com/123456/calendars/ABC-DEF-GHI/

  2. Family
     URL: https://caldav.icloud.com/123456/calendars/XYZ-123-456/

  3. Work
     URL: https://caldav.icloud.com/123456/calendars/789-012-345/
```

#### 3. Add to Configuration

```yaml
calendar_sources:
  - id: "icloud-family"
    name: "iCloud Family Calendar"
    source_type: "caldav"
    calendar_id: "https://caldav.icloud.com/123456/calendars/XYZ-123-456/"
    enabled: true
```

#### 4. Update Credentials File

Add to `config/credentials.json`:

```json
{
  "caldav": {
    "username": "your_apple_id@icloud.com",
    "app_password": "xxxx-xxxx-xxxx-xxxx"
  }
}
```

### Nextcloud Calendar (CalDAV)

#### 1. Find Calendar URL

In Nextcloud web interface:
1. Open Calendar app
2. Click settings (gear icon)
3. Find the calendar you want to sync
4. Click the three-dot menu > "Link"
5. Copy the CalDAV URL

Example format: `https://cloud.example.com/remote.php/dav/calendars/username/personal/`

#### 2. Add to Configuration

```yaml
calendar_sources:
  - id: "nextcloud-personal"
    name: "Nextcloud Personal"
    source_type: "caldav"
    calendar_id: "https://cloud.example.com/remote.php/dav/calendars/username/personal/"
    enabled: true
```

#### 3. Update Credentials File

Add to `config/credentials.json`:

```json
{
  "caldav": {
    "username": "your_nextcloud_username",
    "app_password": "your_nextcloud_password"
  }
}
```

Note: Consider creating an app-specific password in Nextcloud for better security.

### Google Calendar (CalDAV)

Google Calendar can also be accessed via CalDAV (in addition to the OAuth method described in the Google Calendar section above).

#### 1. Generate App-Specific Password

1. Go to [Google Account App Passwords](https://myaccount.google.com/apppasswords)
2. Sign in with your Google account
3. Select "Mail" and "Other (Custom name)"
4. Enter a name (e.g., "Kalendar CalDAV")
5. Click "Generate"
6. Copy the generated 16-character password

#### 2. Discover Calendar URLs

```bash
uv run kalendar discover-caldav \
  --username your_email@gmail.com \
  --service gmail \
  --password your-app-password
```

#### 3. Add to Configuration

```yaml
calendar_sources:
  - id: "gmail-personal"
    name: "Gmail Personal Calendar"
    source_type: "caldav"
    calendar_id: "https://caldav.google.com/user/your_calendar_id/"
    enabled: true
```

#### 4. Update Credentials File

Add to `config/credentials.json`:

```json
{
  "caldav": {
    "username": "your_email@gmail.com",
    "app_password": "your-app-password"
  }
}
```

Note: Google Calendar via OAuth (see [Google Calendar](#google-calendar) section) is recommended over CalDAV as it provides better features and reliability.

## Credentials Management

### Security Best Practices

1. **File Permissions**: Secure your credentials file
   ```bash
   chmod 600 config/credentials.json
   chmod 600 config/google_token.json
   ```

2. **Git Ignore**: Never commit credentials to version control
   ```bash
   # Already in .gitignore:
   config/credentials.json
   config/google_token.json
   config/google_credentials.json
   config/config.yaml  # May contain calendar IDs
   ```

3. **Separate Storage**: Keep credentials separate from main config
   - `config.yaml`: Calendar IDs, display settings (can be versioned)
   - `credentials.json`: Authentication tokens (NEVER version)

### Credentials File Structure

Complete example of `config/credentials.json`:

```json
{
  "google": {
    "token_file": "config/google_token.json",
    "credentials_file": "config/google_credentials.json"
  },
  "caldav": {
    "username": "your_apple_id@icloud.com",
    "app_password": "xxxx-xxxx-xxxx-xxxx"
  }
}
```

## Validation Rules

The configuration is validated when loaded. The following rules must be met:

| Field | Rule | Error Message |
|-------|------|---------------|
| `refresh_hour` | Must be 0-23 | "refresh_hour must be between 0 and 23" |
| `timezone` | Valid IANA timezone | "timezone must be a valid IANA timezone, got: {value}" |
| `week_start_day` | Must be 0-6 | "week_start_day must be between 0 and 6" |
| `max_daily_events` | Must be > 0 | "max_daily_events must be greater than 0" |
| `calendar_sources` | At least one enabled | "At least one calendar source must be enabled" |

### Testing Configuration

Validate your configuration without running a full sync:

```bash
# Test configuration validity
uv run kalendar validate-config --config config/config.yaml

# Test calendar connectivity
uv run kalendar test-sync --config config/config.yaml

# Test full refresh in simulator mode (no hardware needed)
uv run kalendar refresh --config config/config.yaml --simulator
```

## Troubleshooting

### Configuration not loading

**Error**: `FileNotFoundError: Config file not found`

**Solution**: Specify config path explicitly:
```bash
uv run kalendar refresh --config config/config.yaml
```

### Invalid timezone error

**Error**: `ValueError: timezone must be a valid IANA timezone`

**Solution**: Check timezone name against [IANA timezone database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

Common mistakes:
- ❌ `"EST"` → ✅ `"America/New_York"`
- ❌ `"PST"` → ✅ `"America/Los_Angeles"`
- ❌ `"GMT+5"` → ✅ `"Asia/Kolkata"`

### No enabled calendar sources

**Error**: `ValueError: At least one calendar source must be enabled`

**Solution**: Ensure at least one calendar source has `enabled: true`

### Google Calendar authentication fails

**Error**: `Authentication error` or `Invalid credentials`

**Solutions**:
1. Verify credentials file exists: `ls -la config/google_credentials.json`
2. Re-run authorization: `uv run kalendar auth google --credentials config/google_credentials.json`
3. Check OAuth consent screen is configured in Google Cloud Console
4. Ensure Google Calendar API is enabled

### CalDAV connection fails

**Error**: `Connection refused` or `401 Unauthorized`

**Solutions**:
1. Verify calendar URL is correct (run `discover-caldav` again)
2. Check app-specific password is correct
3. Test credentials manually with curl:
   ```bash
   curl -u "username:app-password" "https://caldav.icloud.com/..."
   ```

### Events not appearing

**Checks**:
1. Verify calendar source is `enabled: true`
2. Check sync logs: `sudo journalctl -u kalendar.service -f`
3. Verify calendar has events in the current month
4. Test sync: `uv run kalendar test-sync --config config/config.yaml`

### Configuration changes not taking effect

**Solution**: Restart the service after config changes:
```bash
sudo systemctl restart kalendar.service
```

Or run manual refresh:
```bash
uv run kalendar refresh --config config/config.yaml
```

---

## Complete Example Configuration

Here's a complete example with multiple calendar sources:

```yaml
# Kalendar Configuration
refresh_hour: 6  # Refresh at 6 AM
timezone: "America/New_York"
week_start_day: 6  # Sunday

calendar_sources:
  # Google Calendar - Primary
  - id: "google-primary"
    name: "Personal Calendar"
    source_type: "google"
    calendar_id: "primary"
    enabled: true
    color: "#4285F4"

  # Google Calendar - Work
  - id: "google-work"
    name: "Work Calendar"
    source_type: "google"
    calendar_id: "work@company.com"
    enabled: true
    color: "#0B8043"

  # iCloud Calendar - Family
  - id: "icloud-family"
    name: "Family Events"
    source_type: "caldav"
    calendar_id: "https://caldav.icloud.com/123456/calendars/ABC-DEF/"
    enabled: true
    color: "#FF9500"

  # Nextcloud Calendar
  - id: "nextcloud-shared"
    name: "Shared Calendar"
    source_type: "caldav"
    calendar_id: "https://cloud.example.com/remote.php/dav/calendars/user/shared/"
    enabled: false  # Temporarily disabled
    color: "#0082C9"

display:
  max_daily_events: 5
  layout: "horizontal"

credentials_file: "config/credentials.json"
```

---

For more information, see:
- [Quickstart Guide](../specs/001-calendar-display/quickstart.md)
- [Example Configuration](../config/example.config.yaml)
- [Project README](../README.md)
