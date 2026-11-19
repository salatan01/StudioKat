# Publishing to YouTube via Zapier (optional, OpenCode Code Mode only)

This flow is optional, is not part of the OpenMontage v1 `faceless-short` pipeline, and must confirm title, visibility, and category before uploading.

All calls are Code Mode tools: run them inside `execute` as `tools.zapier.*` (do not call them as normal tools). Validated once in a real upload; the values below are exact.

1. **Connect.** If `list_zapier_skills` has a saved skill for uploading, use it. Otherwise make sure the YouTube app is enabled:
   `discover_zapier_actions({ app: "YouTube" })` → `enable_zapier_action({ selected_api: "YouTubeV4CLIAPI", app_display_name: "YouTube", action: "upload_video" })`.
   If no connection exists yet, `manage_zapier_connections({ selected_api: "YouTubeV4CLIAPI" })` returns a connect URL for the user.
2. **Host the file.** The action's `video` / `thumbnail` params need a URL Zapier's servers can fetch; a local path is silently wrong.
   Put the MP4 on a temp host, in this order (all tested 2026-11-03; on Windows use `curl.exe`):
   - a. **litterbox** (1 h to 72 h expiry, up to 1 GB): `curl -F "reqtype=fileupload" -F "time=1h" -F "fileToUpload=@renders/<name>.mp4" https://litterbox.catbox.moe/resources/internals/api.php` → returns the direct URL as plain text.
   - b. **uguu.se** (about 3 h expiry, good for shorts under 35 MB): `curl -F "files[]=@renders/<name>.mp4" https://uguu.se/upload` → returns JSON; use `files[0].url` (the `d.uguu.se/...` link).
   - c. **catbox** (permanent, no expiry): same call as (a) without `-F "time=1h"`. Public forever, so only with the user's OK.
   - Skip these (verified broken 2026-11-03, don't waste retries): 0x0.st (uploads disabled), tmpfiles.org (link is a viewer page, not the raw file), gofile.io (raw download needs an account token), file.io (curl API redirects to its web app), bashupload.com, temp.sh (dead).
   - **Always verify** the URL before using it: `curl -sSI <url>` must return 200/206 with a video content-type. Never trust a host's JSON without checking.
   - Tell the user this puts their video on a public temp host that expires by itself.
3. **Confirm first.** This writes to the user's real channel, so confirm before executing: title, visibility (private / unlisted / public) and category.
   Resolve `category_id` with `inspect_zapier_actions({ tool_name: "youtube_upload_video", enum_property: "category_id" })` if needed.
   Comedy = 23 (default suggestion for Tall Tale and Deep Dive), Education = 27, Pets & Animals = 15.
4. **Upload.**
   `execute_zapier_write_action({ selected_api: "YouTubeV4CLIAPI", action: "upload_video", tool_name: "youtube_upload_video", params: { video: "<temp URL>", title, description (end it with #shorts), tags: [5-8 hashtags without #], category_id: "23", privacy_status, made_for_kids: false, embeddable: true, notify_subscribers: true, default_language: "en", license: "youtube" } })`
5. **Report.** The result contains `id`; the link is `https://www.youtube.com/watch?v=<id>`. A vertical video of 60 s or less becomes a Short automatically (no extra field).
   Open the local file for the user with `xdg-open renders/<name>.mp4` (Linux) or `open renders/<name>.mp4` (macOS), or return the local path, and give the YouTube URL in text. The in-app browser often fails to load youtube.com with ERR_ABORTED; that is not a failed upload.
6. **Thumbnails.** Unlisted uploads don't take a custom thumbnail through this action; offer the saved cover frame if the user later makes the video public.
