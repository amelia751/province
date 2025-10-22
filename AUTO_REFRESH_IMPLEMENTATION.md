# Auto-Refresh Implementation for Form 1040 Live Versioning

**Issue**: The Form 1040 viewer should automatically reload when new versions are created by the backend agent, but it's not working properly.

---

## Current Implementation Overview

The auto-refresh feature is implemented in `/Users/anhlam/province/frontend/src/components/tax-forms/form-1040-viewer.tsx` using React hooks and polling.

---

## Implementation Details

### 1. Component State

```typescript
const [versionsData, setVersionsData] = useState<FormVersionsData | null>(null);
const [currentVersionIndex, setCurrentVersionIndex] = useState(0);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [lastChecked, setLastChecked] = useState<number>(Date.now());
const [forceReloadKey, setForceReloadKey] = useState(0);

// Use ref to avoid stale closure in interval
const versionsDataRef = useRef(versionsData);
useEffect(() => {
  versionsDataRef.current = versionsData;
}, [versionsData]);
```

**Key Points**:
- `versionsData`: Stores all form versions from the API
- `forceReloadKey`: Forces PDF viewer to remount when incremented
- `versionsDataRef`: Used to avoid stale closure issues in the polling interval

---

### 2. Polling Mechanism (Every 5 Seconds)

```typescript
// Auto-refresh: Poll for new versions every 5 seconds
useEffect(() => {
  const interval = setInterval(() => {
    // Silently check for new versions (don't show loading state)
    checkForNewVersions();
  }, 5000); // Check every 5 seconds

  return () => clearInterval(interval);
}, [engagementId, userId]); // Stable dependencies - don't reset interval on data changes
```

**Design Decision**: 
- Poll every 5 seconds
- Dependencies: `[engagementId, userId]` only (intentionally excludes `versionsData` to avoid resetting interval)
- Silent checks (no loading spinner)

---

### 3. Version Checking Logic

```typescript
const checkForNewVersions = async () => {
  try {
    // Include user_id in query if available
    const url = userId 
      ? `/api/forms/1040/${engagementId}/versions?tax_year=2024&user_id=${userId}`
      : `/api/forms/1040/${engagementId}/versions?tax_year=2024`;

    const response = await fetch(url);

    if (!response.ok) {
      return; // Silently fail
    }

    const data: FormVersionsData = await response.json();
    
    // Get current state from ref (avoids stale closure)
    const currentVersions = versionsDataRef.current;
    const currentTotal = currentVersions?.total_versions || 0;
    const currentLatest = currentVersions?.latest_version || '';
    
    // Check if there's ACTUALLY a new version (more strict comparison)
    const hasNewVersion = data.total_versions > currentTotal || 
                          (data.latest_version && data.latest_version !== currentLatest);
    
    if (hasNewVersion) {
      console.log('🔄 New form version detected!');
      console.log(`   Previous: ${currentTotal} versions, latest: ${currentLatest}`);
      console.log(`   New: ${data.total_versions} versions, latest: ${data.latest_version}`);
      setVersionsData(data);
      setCurrentVersionIndex(0); // Jump to latest version
      setForceReloadKey(prev => prev + 1); // Force complete PDF reload
      setLastChecked(Date.now());
    } else {
      // No changes detected - just update last checked time quietly
      setLastChecked(Date.now());
    }
  } catch (err) {
    // Silently fail - don't disrupt user experience
    console.debug('Background version check failed:', err);
  }
};
```

**Logic Flow**:
1. Fetch latest versions from API
2. Compare `total_versions` and `latest_version` with current state
3. If different:
   - Log to console
   - Update `versionsData`
   - Reset to index 0 (latest)
   - Increment `forceReloadKey`
4. If same: silently update `lastChecked`

---

### 4. PDF Viewer Rendering

```typescript
{(() => {
  const cacheKey = `${currentVersion.version}-${currentVersion.timestamp}`;
  const separator = currentVersion.download_url.includes('?') ? '&' : '?';
  const urlWithCache = `${currentVersion.download_url}${separator}v=${encodeURIComponent(cacheKey)}`;
  
  return (
    <PdfViewer
      key={`${cacheKey}-${forceReloadKey}`} // Forces remount when version changes or force reload triggered
      url={urlWithCache} // Cache-buster tied to version
      className="w-full h-full"
    />
  );
})()}
```

**Key Techniques**:
- **Cache Busting**: Append `?v=${version}-${timestamp}` to URL
- **Force Remount**: Use `key={cacheKey}-${forceReloadKey}` to force React to remount component
- **Double Layer**: Both `cacheKey` (version-based) and `forceReloadKey` (manual increment)

---

## API Response Structure

The backend `/api/v1/forms/1040/{engagement_id}/versions` endpoint returns:

```json
{
  "engagement_id": "ea3b3a4f-c877-4d29-bd66-2cff2aa77476",
  "form_type": "1040",
  "tax_year": 2024,
  "total_versions": 8,
  "latest_version": "v008",
  "versions": [
    {
      "version": "v008",
      "version_number": 8,
      "s3_key": "filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/1040/2024/v008_1040_1761069869.pdf",
      "size": 349928,
      "timestamp": "2025-10-21T18:04:30Z",
      "last_modified": "2025-10-21T18:04:30+00:00",
      "download_url": "https://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1.s3.amazonaws.com/..."
    },
    // ... more versions ...
  ]
}
```

---

## Problem Statement

### Expected Behavior
1. User starts conversation with agent
2. Agent fills Form 1040 progressively (v001, v002, v003, etc.)
3. Frontend polls every 5 seconds
4. When new version detected (`total_versions` increases):
   - Console logs "🔄 New form version detected!"
   - PDF viewer remounts
   - Latest form appears automatically
5. User sees live updates as agent fills the form

### Actual Behavior
- ❌ PDF does NOT reload when new versions are created
- ❌ Console does NOT show "🔄 New form version detected!"
- ❌ User must manually refresh to see new versions
- ✅ Polling IS happening (network tab shows requests every 5 seconds)
- ✅ API IS returning correct data (backend logs show 404 or 200 responses)

### Current Logs
From backend logs, the frontend is polling correctly:
```
GET /api/v1/forms/1040/ea3b3a4f-c877-4d29-bd66-2cff2aa77476/versions?tax_year=2024&user_id=user_33w9KAn1gw3xXSa6MnBsySAQIIm 404 in 442ms
```

However, in this specific case, the API returns `404` because:
- The `engagement_id` doesn't exist in DynamoDB
- No forms exist in S3 for that user

---

## Potential Issues

### 1. Stale Closure in `useEffect`
**Original Problem**: The `checkForNewVersions` function was captured in the `useEffect` closure with old `versionsData`.

**Attempted Fix**: Used `useRef` to store latest `versionsData`:
```typescript
const versionsDataRef = useRef(versionsData);
useEffect(() => {
  versionsDataRef.current = versionsData;
}, [versionsData]);

// Then in checkForNewVersions:
const currentVersions = versionsDataRef.current;
```

**Status**: Should work, but needs verification.

---

### 2. Comparison Logic
```typescript
const hasNewVersion = data.total_versions > currentTotal || 
                      (data.latest_version && data.latest_version !== currentLatest);
```

**Potential Issues**:
- If both API calls return `404`, `total_versions` is always 0
- If `latest_version` is undefined/null in both responses, comparison fails
- String comparison for `latest_version` might have whitespace/encoding issues

---

### 3. API Response Caching
**Browser Level**: Fetch requests might be cached by the browser.

**Current Mitigation**: None explicitly set (no `Cache-Control` headers in request).

**Possible Fix**: Add cache-busting headers:
```typescript
const response = await fetch(url, {
  headers: {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
  }
});
```

---

### 4. React Reconciliation
**Issue**: React might not recognize the PDF viewer needs to remount.

**Current Approach**: Use compound key with `forceReloadKey`:
```typescript
key={`${cacheKey}-${forceReloadKey}`}
```

**Question**: Is this sufficient for React to remount the `<iframe>` inside `PdfViewer`?

---

### 5. Network Tab vs. Console Logs
**Observation**: 
- Network tab shows requests every 5 seconds ✅
- Console should show version comparison logs
- Console is NOT showing "🔄 New form version detected!" ❌

**Hypothesis**: 
- Either comparison logic is broken
- Or `console.log` is somehow not firing
- Or browser dev tools console is filtered

---

## Testing Scenarios

### Scenario 1: Fresh Start (No Forms Exist)
1. User ID: `user_33w9KAn1gw3xXSa6MnBsySAQIIm`
2. Engagement: `ea3b3a4f-c877-4d29-bd66-2cff2aa77476`
3. Backend test creates v001 → v008
4. **Expected**: Frontend detects v001 → v002 → v003...
5. **Actual**: Frontend stays at "No Form 1040 Available"

### Scenario 2: Existing Forms
1. Forms already exist (v001-v008)
2. Agent creates v009
3. **Expected**: Frontend auto-loads v009
4. **Actual**: Stays on v008

---

## Code Location

### Main Component
**File**: `/Users/anhlam/province/frontend/src/components/tax-forms/form-1040-viewer.tsx`

**Lines**:
- State setup: Lines 41-52
- Polling interval: Lines 59-66
- Version checking: Lines 108-148
- PDF rendering: Lines 268-281

### Related Components
- **PdfViewer**: `/Users/anhlam/province/frontend/src/components/pdf-viewer.tsx`
- **Main Editor** (parent): `/Users/anhlam/province/frontend/src/components/main-editor/main-editor.tsx`

---

## Browser Environment

- **Framework**: Next.js 15.5.0 (Turbopack)
- **React Version**: 18+ (with Suspense, useRef, etc.)
- **Browser**: Safari/Chrome (macOS)
- **Console**: Should show logs, but currently silent

---

## Questions for Debugging

1. **Stale Closure**: Is the `useRef` approach correct for avoiding stale closures in `setInterval`?

2. **Comparison Logic**: Should I compare version numbers instead of strings?
   ```typescript
   const hasNewVersion = data.versions[0]?.version_number > (currentVersions?.versions[0]?.version_number || 0);
   ```

3. **Force Remount**: Is `key={cacheKey}-${forceReloadKey}` sufficient to force React to remount the PDF viewer?

4. **Browser Caching**: Do I need to add `Cache-Control` headers to the fetch request?

5. **Console Logs**: Why aren't the debug logs showing in the console? Are they being filtered somehow?

6. **API 404s**: When the API returns 404 (no forms found), should I still update state? Currently, I `return` early, which means state never updates.

7. **Race Conditions**: Could there be a race condition where the agent creates forms faster than the 5-second polling interval?

8. **React DevTools**: How can I verify that the component is actually re-rendering when `versionsData` changes?

---

## Expected vs. Actual Flow

### Expected
```
1. Agent fills form → v001 created in S3
2. (5 seconds pass)
3. Frontend polls API → gets {total_versions: 1, latest: "v001"}
4. Comparison: 1 > 0 → hasNewVersion = true
5. Console: "🔄 New form version detected!"
6. setVersionsData(newData)
7. setForceReloadKey(prev => prev + 1)
8. PDF viewer remounts with new URL
9. User sees v001
10. (Agent fills more) → v002 created
11. (5 seconds pass)
12. Frontend polls → {total_versions: 2, latest: "v002"}
13. Comparison: 2 > 1 → hasNewVersion = true
14. ... (repeat)
```

### Actual
```
1. Agent fills form → v001 created in S3
2. (5 seconds pass)
3. Frontend polls API → gets 404 or {total_versions: 0}
4. Comparison: 0 > 0 → hasNewVersion = false
5. No console logs
6. State unchanged
7. PDF viewer shows "No Form 1040 Available"
8. User manually refreshes → still "No Form 1040 Available"
```

---

## Additional Context

### Backend Logs Show
```
Engagement ea3b3a4f-c877-4d29-bd66-2cff2aa77476 not found in DynamoDB, scanning S3 for forms
Scanning all users for 1040 forms (engagement not found in DynamoDB)
Found 0 versions for user_id=ALL, form=1040, year=2024
```

**This suggests**:
1. The `engagement_id` is not in the `tax_engagements` table
2. The backend scans all users' forms in S3
3. No forms are found (possibly wrong S3 prefix or no forms exist)

**BUT**: The backend test script (`test_full_user_conversation.py`) successfully created 8 versions in S3:
```
✅ Found 8 filled form(s):
   - filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/1040/2024/v001_1040_1761069712.pdf
   - filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/1040/2024/v002_1040_1761069733.pdf
   ...
   - filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/1040/2024/v008_1040_1761069869.pdf
```

**Discrepancy**: Why does the backend API not find these forms?

---

## Possible Root Cause

**Hypothesis**: The real issue might not be the frontend auto-refresh logic, but rather the **backend API not finding the forms** that exist in S3.

If the API always returns `404` or `{total_versions: 0}`, then:
- `hasNewVersion` will always be `false` (0 > 0 = false)
- No console logs will appear
- Frontend will never update

**To verify**: Manually call the API in Postman/curl:
```bash
curl "http://localhost:8000/api/v1/forms/1040/ea3b3a4f-c877-4d29-bd66-2cff2aa77476/versions?tax_year=2024&user_id=user_33w9KAn1gw3xXSa6MnBsySAQIIm"
```

**Expected**: Should return the 8 versions created by the test script.

**If it returns 404**: The problem is backend form lookup logic, NOT frontend auto-refresh.

---

## Next Steps to Debug

1. **Verify API Response**: Call the backend API directly (curl/Postman) to see if it returns forms.

2. **Add More Console Logs**: In `checkForNewVersions`, add logs BEFORE the comparison:
   ```typescript
   console.log('Polling API...');
   console.log('Current state:', { currentTotal, currentLatest });
   console.log('API response:', { newTotal: data.total_versions, newLatest: data.latest_version });
   console.log('Has new version?', hasNewVersion);
   ```

3. **Check Browser Console Filters**: Make sure console isn't filtering out `console.log`.

4. **Test with Known Data**: Manually set initial state to `{total_versions: 1, latest_version: 'v001'}`, then trigger the backend to create v002. Does the frontend detect it?

5. **React DevTools**: Open React DevTools and watch `versionsData` state. Does it ever update?

6. **Network Tab**: Check the actual API response in the browser network tab. What does the payload look like?

---

## Summary for ChatGPT

**I implemented an auto-refresh feature for a React component that should poll an API every 5 seconds and reload a PDF viewer when new versions are detected.**

**The polling happens (network requests every 5s), but the component never updates to show new content.**

**I suspect either**:
1. A stale closure issue (despite using `useRef`)
2. Incorrect comparison logic
3. React not recognizing the need to remount
4. Backend API not returning the correct data

**Can you help identify the issue and suggest a fix?**

