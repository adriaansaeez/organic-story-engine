---
name: ose-comments
description: Capture and read what the community asked for in a video's comments, stored as one request per person per video (their first comment, verbatim). Use when the user asks "what did they comment on ep03", "what are people asking for", "top comments", "what did @someone say", or before writing any script that must answer the community.
---

# Comments become requests

A request is a person's FIRST comment on a video, kept verbatim. One per person per video.
Requests are never overwritten: a new capture only refreshes their like counts. Likes are the
community's priority signal. Requests are private working data: never publish the list.

## Read (no browser needed)

```bash
python3 engine/audience/audience.py comments                  # every video and its pending requests
python3 engine/audience/audience.py comments ep03             # requests, most liked first
python3 engine/audience/audience.py comments ep03 --all       # every raw comment of the last capture
#   --sort likes|time  --user <handle>  --search <text>  --status pending|accepted|fulfilled|rejected|duplicate  --json
```

The video can be given as its id (ep03), the platform id or the URL. When you report, quote the
comment verbatim with its @ and likes; do not paraphrase it.

## Refresh (agent browser, read-only)

1. Open a NEW tab at the video URL (about 1400x900 so the comments panel fits), panel closed.
2. Run `engine/capture/comments.js` in the page, prefixed with `await `. It listens to the
   page's own comment responses, scrolls and expands replies, and returns every comment oldest first.
3. Save the result to `data/comments/YYYY-MM-DD-HHMM-<platform id>.json`.
4. `python3 engine/audience/audience.py requests <file> --world <world> --census` to preview,
   then add `--confirm`. `--census` also adds unknown commenters as citizens, in order of their first
   comment. A video seen for the first time is registered as the next episode id.

## Rules

- Read-only on the platform: never like, reply or pin.
- Login wall or captcha: stop and tell the user.
- If there is nothing new, delete the capture file instead of keeping duplicates.
