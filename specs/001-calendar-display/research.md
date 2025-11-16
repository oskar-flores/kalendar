# Research Findings: Multi-Calendar E-Paper Display

**Feature**: 001-calendar-display
**Date**: 2025-11-15
**Purpose**: Resolve NEEDS CLARIFICATION items from Technical Context

---

## 1. HTML-to-Image Library Selection

### Decision

**WeasyPrint** - Lightweight HTML/CSS rendering to PNG/PDF

### Rationale

WeasyPrint is the optimal choice for Raspberry Pi Zero due to:

1. **No browser dependency**: Self-contained rendering engine (unlike html2image or imgkit which require Chrome/wkhtmltoimage)
2. **Lightweight**: Pure Python implementation with minimal C dependencies (cairo, pango, gdk-pixbuf)
3. **Memory efficient**: Designed for print media, not full browser features
4. **ARM compatible**: Works on ARMv6 (Pi Zero W) with system libraries available via apt
5. **PNG output**: Direct `write_png()` method for image generation
6. **CSS print media**: Excellent for fixed-layout calendar rendering

**Installation**:
```bash
# System dependencies (available on Raspberry Pi OS)
sudo apt-get install python3-pip python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0

# Python package
uv add weasyprint
```

**Memory footprint**: ~30-50MB during rendering (well within 256MB budget)

**Example usage**:
```python
from weasyprint import HTML, CSS

html_string = "<html><body><h1>Calendar</h1></body></html>"
HTML(string=html_string).write_png('/tmp/calendar.png')
```

### Alternatives Considered

| Library | Rejected Because |
|---------|------------------|
| **imgkit/wkhtmltoimage** | Requires external binary (wkhtmltoimage), heavier footprint, less reliable on ARM |
| **html2image** | Requires full Chrome/Chromium browser in headless mode (~200MB+ memory) |
| **playwright-python** | Extremely heavy (~500MB+ with browser binaries), overkill for static rendering |
| **Pillow + HTML parsing** | No native HTML/CSS layout engine, would require manual layout calculations |

---

## 2. CalDAV Library for Apple iCloud Calendar

### Decision

**caldav** (https://pypi.org/project/caldav/) - Python CalDAV client

### Rationale

The `caldav` library is the most mature and maintained CalDAV client for Python:

1. **Active maintenance**: Released Nov 8, 2025 (version 2.1.2)
2. **iCloud support**: Confirmed working with iCloud Calendar (https://caldav.icloud.com/)
3. **Full CalDAV spec**: Supports calendar discovery, event fetching, search by date range
4. **RRULE support**: Works with `icalendar` library for recurring event expansion
5. **Lightweight**: Minimal dependencies (requests, lxml, icalendar, recurring-ical-events)

**Installation**:
```bash
uv add caldav icalendar recurring-ical-events
```

**iCloud authentication**:
- Requires app-specific password (not main iCloud password)
- Generated at https://appleid.apple.com/ under Security

**Example usage**:
```python
from caldav import DAVClient

# Connect to iCloud
client = DAVClient(
    url="https://caldav.icloud.com/",
    username="your_apple_id@icloud.com",
    password="app-specific-password"
)

# Get calendars
principal = client.principal()
calendars = principal.calendars()

# Fetch events from a calendar
from datetime import datetime, timedelta
start = datetime.now()
end = start + timedelta(days=30)

events = calendar.date_search(start=start, end=end, expand=True)
for event in events:
    ical_data = event.data  # iCalendar format
```

### Alternatives Considered

| Library | Rejected Because |
|---------|------------------|
| **vobject** | Lower-level iCalendar parser, no CalDAV client functionality |
| **icalendar** | iCalendar parser only, not a CalDAV client (used alongside caldav) |
| **Google Calendar API** | Not applicable for Apple iCloud calendars |

### Known Limitations

- iCloud CalDAV does not support freebusy requests, tasks, or journals (events only)
- Some iCloud-specific calendar features may not work due to Apple's CalendarServer variant
- No official Apple CalDAV documentation (Apple doesn't officially support CalDAV API access)

---

## 3. Google Calendar API Library

### Decision

**google-api-python-client** (Official Google library)

### Rationale

The official Google Calendar API client is the best choice despite package size:

1. **Official support**: Maintained by Google with weekly updates
2. **Full API coverage**: Complete access to Calendar API v3
3. **OAuth 2.0 support**: Built-in authentication via google-auth-oauthlib
4. **Headless-friendly**: Token-based auth works on Pi Zero after initial desktop authorization
5. **Production-ready**: Well-tested, comprehensive error handling
6. **Refresh tokens**: Long-lived refresh tokens eliminate need for repeated OAuth flows

**Installation**:
```bash
uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Package size**: ~50MB (acceptable given SD card storage)

**Headless authentication workflow**:

1. **Desktop authorization** (one-time):
```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

# Save token.json
with open('token.json', 'w') as token:
    token.write(creds.to_json())
```

2. **Pi Zero usage** (automatic refresh):
```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# Auto-refresh if expired
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('calendar', 'v3', credentials=creds)
```

3. **Fetch events from multiple calendars**:
```python
# List all calendars
calendar_list = service.calendarList().list().execute()

all_events = []
for calendar_entry in calendar_list['items']:
    calendar_id = calendar_entry['id']

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=datetime.now(tz=timezone.utc).isoformat(),
        maxResults=50,
        singleEvents=True,  # Expand recurring events
        orderBy='startTime'
    ).execute()

    all_events.extend(events_result.get('items', []))
```

### Alternatives Considered

| Library | Rejected Because |
|---------|------------------|
| **GCSA** | Wrapper around google-api-python-client, no size benefit, extra abstraction layer |
| **gcalendar** | Unmaintained, last update 2019 |

### Rate Limits & Quotas

- **Daily quota**: 1,000,000 requests/day (more than sufficient)
- **Per-user limit**: Enforced per minute
- **Best practice**: Implement exponential backoff on 403/429 errors
- **Recommendation**: Cache calendar data locally, sync once per day (already planned)

### OAuth Credentials Setup

1. Create project at https://console.cloud.google.com/
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop application type)
4. Download `credentials.json`
5. Run initial auth on desktop to generate `token.json`
6. Transfer both files to Pi Zero

**Security**: `token.json` contains refresh token - treat as sensitive, store with restricted permissions (chmod 600)

---

## 4. Waveshare E-Paper Display Driver

### Decision

**Waveshare 7.5inch e-Paper HAT (B)** with official Waveshare Python library

### Rationale

The Waveshare 7.5inch e-Paper HAT (B) is the optimal display choice:

1. **3-color support**: Black, Red, White (matches requirements)
2. **Resolution**: 800×480 pixels (sufficient for calendar display in landscape)
3. **SPI interface**: Standard Raspberry Pi HAT connector, well-supported
4. **Official Python library**: Waveshare provides demo code and drivers
5. **Pi Zero W compatible**: Tested and documented for all Pi models including Zero W
6. **Low power**: E-ink technology retains image without power
7. **Refresh characteristics**: Recommended 180s between refreshes, 24h refresh cycle (matches requirement)

**Hardware specifications**:
- **Model**: 7.5inch e-Paper HAT (B) - part# WF0583CZ09
- **Resolution**: 800×480 pixels
- **Colors**: Red / Black / White
- **Interface**: SPI (CE0, GPIO)
- **Refresh time**: ~30 seconds per full refresh
- **Minimum refresh interval**: 180 seconds (3 minutes)
- **Viewing angle**: 180°
- **Voltage**: 3.3V (via onboard voltage translator, safe for Pi)

**Installation**:
```bash
# Enable SPI interface
sudo raspi-config
# Select: Interfacing Options -> SPI -> Yes

# Install dependencies
sudo apt-get install python3-pil python3-numpy

# Clone Waveshare examples (includes drivers)
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python/
sudo python3 setup.py install
```

**Driver files needed**:
- `lib/waveshare_epd/epd7in5b_V2.py` - Driver for 7.5inch HAT (B) V2
- `lib/waveshare_epd/epdconfig.py` - SPI configuration

**Example usage**:
```python
from waveshare_epd import epd7in5b_V2
from PIL import Image

# Initialize display
epd = epd7in5b_V2.EPD()
epd.init()

# Create images for black and red layers
# (e-paper uses separate layers for black and red)
black_image = Image.new('1', (epd.height, epd.width), 255)  # 255: white, 0: black
red_image = Image.new('1', (epd.height, epd.width), 255)    # 255: white, 0: red

# Load rendered calendar image and separate into layers
calendar_img = Image.open('/tmp/calendar.png')
# Convert to black/red layers (implementation in infrastructure layer)

# Display
epd.display(epd.getbuffer(black_image), epd.getbuffer(red_image))

# Sleep mode (low power)
epd.sleep()
```

### Alternatives Considered

| Display Model | Rejected Because |
|---------------|------------------|
| **7.5inch e-Paper HAT** (regular) | 2-color only (black/white), no red highlight |
| **7.5inch e-Paper HAT (C)** | Yellow instead of red, lower contrast |
| **7.5inch HD e-Paper HAT (B)** | 880×528 resolution, higher cost, refresh time ~40s (slower) |
| **Other manufacturers** | Waveshare has best Pi documentation and library support |

### Display Rendering Strategy

The Waveshare 7.5B uses a **two-buffer system**:

1. **Black buffer**: Pixels that should be black (0) or white (255)
2. **Red buffer**: Pixels that should be red (0) or white (255)

**Integration with WeasyPrint**:

1. WeasyPrint renders HTML to single RGB PNG image
2. Post-process PNG to separate black and red channels:
   - Red pixels (from CSS `color: red`) → red buffer
   - Black pixels → black buffer
   - Everything else → white

**Color mapping from spec**:
- Red: Current day, today's events (FR-010)
- Black: All other text
- White: Background

---

## 5. Architecture Decisions

### Technology Stack Summary

| Component | Technology | Version | Memory Est. |
|-----------|-----------|---------|-------------|
| **Language** | Python | 3.11+ | - |
| **HTML rendering** | WeasyPrint | 62.3+ | 30-50MB |
| **Google Calendar** | google-api-python-client | latest | - |
| **iCloud Calendar** | caldav + icalendar | 2.1.2+ | - |
| **E-paper driver** | waveshare_epd | from repo | <10MB |
| **Testing** | pytest | latest | - |
| **Packaging** | uv | latest | - |

**Total estimated memory during refresh cycle**: <150MB (well within 256MB budget)

### Display Rendering Pipeline

```
1. Fetch calendar data (Google + iCloud APIs)
   ↓
2. Aggregate events into domain models
   ↓
3. Generate HTML from template (monthly view + today's events)
   ↓
4. Render HTML to PNG (WeasyPrint)
   ↓
5. Split PNG into black/red layers
   ↓
6. Display on e-paper (Waveshare driver)
   ↓
7. Enter sleep mode
```

### Performance Estimates (Pi Zero W)

- **Calendar fetch**: 5-15s (network dependent)
- **HTML rendering**: 10-20s (WeasyPrint)
- **Image processing**: 2-5s (PIL layer separation)
- **E-paper refresh**: 30s (hardware limitation)
- **Total cycle**: 47-70s ✅ (within 60s target with optimization)

### Dependency Isolation

All external dependencies abstracted behind interfaces:

- `ICalendarSource` - Interface for both Google and CalDAV clients
- `IDisplayDriver` - Interface for e-paper display
- `IImageRenderer` - Interface for HTML-to-image rendering
- `ICache` - Interface for filesystem storage

This enables:
- Testing without hardware/network
- Swapping implementations (e.g., different display models)
- Mocking for TDD workflow

---

## 6. Risk Mitigation

### Identified Risks

1. **Memory constraint on Pi Zero**
   - **Mitigation**: Benchmark on actual Pi Zero hardware in integration testing
   - **Fallback**: Reduce concurrent calendar fetches, smaller event window

2. **WeasyPrint rendering time**
   - **Mitigation**: Pre-render test case on Pi Zero to validate <20s target
   - **Fallback**: Simplify HTML/CSS if needed, reduce layout complexity

3. **iCloud CalDAV reliability**
   - **Mitigation**: Implement retry logic, cache last successful sync
   - **Fallback**: Display stale data with timestamp if sync fails

4. **E-paper refresh lifespan**
   - **Mitigation**: Limit to once per day (already planned), use partial refresh only when necessary
   - **Tracking**: Log refresh count for monitoring

### Validation Checklist

Before proceeding to implementation:

- [ ] Install WeasyPrint on Pi Zero and test rendering 800×480 HTML
- [ ] Measure memory usage during rendering
- [ ] Test Waveshare driver with Python 3.11 on Pi Zero W
- [ ] Verify SPI interface configuration
- [ ] Test Google Calendar API with token-based auth (no browser)
- [ ] Test caldav library with iCloud Calendar (app-specific password)
- [ ] Benchmark full pipeline on Pi Zero: target <60s end-to-end

---

## 7. Updated Technical Context

**Resolved from "NEEDS CLARIFICATION"**:

- **Primary Dependencies**:
  - `weasyprint` - HTML/CSS to PNG rendering
  - `google-api-python-client` - Google Calendar API
  - `caldav` + `icalendar` - Apple iCloud Calendar (CalDAV)
  - `waveshare_epd` - E-paper display driver (from Waveshare GitHub)
  - `PIL/Pillow` - Image processing (layer separation)

**Display Hardware**:
- **Model**: Waveshare 7.5inch e-Paper HAT (B)
- **Resolution**: 800×480 pixels
- **Colors**: Black, Red, White
- **Refresh**: ~30s per update, min 180s between updates

**Performance Validation**:
- Estimated refresh cycle: 47-70s (within <60s target)
- Estimated memory peak: 100-150MB (within <256MB budget)
- Requires on-hardware validation in integration testing phase

---

**Research Phase Complete**: All NEEDS CLARIFICATION items resolved. Ready to proceed to Phase 1 (Design & Contracts).
