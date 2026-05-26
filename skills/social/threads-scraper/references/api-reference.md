# scrapecreators.com API Reference

## Endpoint

```
GET https://api.scrapecreators.com/v1/threads/search
```

## Headers

| Header | Value |
|--------|-------|
| `x-api-key` | `$SCRAPECREATORS_API_KEY` |

## Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | yes | Search keyword |
| `start_date` | string (YYYY-MM-DD) | yes | Start date (inclusive) |
| `end_date` | string (YYYY-MM-DD) | yes | End date (inclusive) |
| `trim` | boolean | no | Default `false`. Whether to trim fields. |

## Response Shape (fields we consume)

```json
{
  "data": {
    "items": [
      {
        "id": "1234567890",
        "code": "CxYzAbCdEfG",
        "username": "john_doe",
        "full_name": "John Doe",
        "caption": {
          "text": "Full caption text with #hashtags and @mentions"
        },
        "like_count": 142,
        "taken_at": 1680000000,
        "image_versions2": {
          "candidates": [{"url": "...", "width": 1080, "height": 1080}]
        },
        "video_versions": [...],
        "carousel_media": [...],
        "text_post_app_info": {
          "direct_reply_count": 23,
          "is_reply": false,
          "reshare_count": 12,
          "repost_count": 5,
          "quote_count": 3,
          "text_fragments": {
            "fragments": [
              {"fragment_type": "tag", "text": "ai"},
              {"fragment_type": "text", "text": " normal text "}
            ]
          }
        },
        "is_paid_partnership": false,
        "is_sponsored": false
      }
    ]
  }
}
```

## Rate Limiting

If the API returns HTTP 429, the scraper backs off with exponential retry:
1s, 2s, 4s, 8s, then abort. Other 4xx errors abort immediately.

## Cache Strategy

Each (query, start_date, end_date) combination is SHA256-hashed and cached
for 24 hours. Cache lives at `<output_dir>/cache/<hash>.json`. Cache is
bypassed only when the key is missing or older than 24h.
