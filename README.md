# 🚀 All-in-One API Service

**Production-ready, self-contained API service with zero external dependencies**

Deploy once to Koyeb free tier and never touch it again.

---

## 🎯 What This Is

A **single Docker container** that provides:

1. **Web Scraping** (Crawl4AI) - Raw HTML/text extraction
2. **OCR** (Tesseract) - Image & PDF text extraction
3. **PDF Generation** (Python) - From text, HTML, markdown, images
4. **Video Processing** (FFmpeg) - Trimming, merging, compression, etc.

**No API keys. No external services. No AI models. 100% local.**

---

## ⚡ Quick Start

### Deploy to Koyeb

1. **Create Koyeb account** (free tier: 2GB RAM, 2 cores)

2. **Deploy from GitHub:**
   - Push this repo to GitHub
   - In Koyeb: New Service → GitHub
   - Select repository
   - Set service type: **Web**
   - Port: **8000**
   - Deploy!

3. **Get your URL:**
   ```
   https://your-service-name.koyeb.app
   ```

4. **Access docs:**
   ```
   https://your-service-name.koyeb.app/docs
   ```

### Local Testing

```bash
# Build
docker build -t all-in-one-service .

# Run
docker run -p 8000:8000 all-in-one-service

# Access
http://localhost:8000/docs
```

---

## 📚 API Endpoints

### 🕷️ Web Scraping

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/crawl/scrape` | POST | Simple scrape (clean text) |
| `/crawl/scrape/html` | POST | Fetch raw HTML |
| `/crawl/scrape/text` | POST | Plain text only |
| `/crawl/scrape/meta` | POST | Extract metadata & links |
| `/crawl/scrape/deep` | POST | Multi-page crawl |

**Example:**
```bash
curl -X POST https://your-service.koyeb.app/crawl/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

### 👁️ OCR (Text Extraction)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ocr/image` | POST | Extract text from image |
| `/ocr/pdf` | POST | Extract text from PDF |
| `/ocr/languages` | GET | List available languages |

**Supported formats:** JPG, PNG, WEBP, HEIF, HEIC, PDF

**Example:**
```bash
curl -X POST https://your-service.koyeb.app/ocr/image \
  -F "file=@image.jpg" \
  -F "language=eng" \
  -F "output_format=text"
```

### 📄 PDF Generation

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/pdf/from-text` | POST | Create PDF from text |
| `/pdf/from-html` | POST | Create PDF from HTML |
| `/pdf/from-markdown` | POST | Create PDF from markdown |
| `/pdf/from-images` | POST | Create PDF from images |
| `/pdf/merge` | POST | Merge multiple PDFs |

**Example:**
```bash
curl -X POST https://your-service.koyeb.app/pdf/from-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content",
    "title": "My Document",
    "style": "formal"
  }' \
  --output document.pdf
```

### 🎬 Video/Audio Processing

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ffmpeg/info` | POST | Get media information |
| `/ffmpeg/trim` | POST | Trim video |
| `/ffmpeg/merge` | POST | Merge videos |
| `/ffmpeg/resize` | POST | Resize video |
| `/ffmpeg/compress` | POST | Compress video |
| `/ffmpeg/extract-audio` | POST | Extract audio |
| `/ffmpeg/thumbnail` | POST | Generate thumbnail |
| `/ffmpeg/convert` | POST | Convert format |

**Example:**
```bash
curl -X POST https://your-service.koyeb.app/ffmpeg/trim \
  -F "file=@video.mp4" \
  -F "start_time=10" \
  -F "duration=30" \
  --output trimmed.mp4
```

### 🏥 System

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/info` | GET | System information |
| `/` | GET | API overview |

---

## 🔗 n8n Integration

### Example 1: Web Scraping Workflow

```
Trigger (Webhook)
  ↓
HTTP Request (Scrape URL)
  ↓
Extract Data
  ↓
Save to Database
```

**HTTP Request Node:**
- Method: POST
- URL: `https://your-service.koyeb.app/crawl/scrape`
- Body: `{"url": "{{ $json.url }}"}`

### Example 2: OCR + PDF Workflow

```
Trigger (File Upload)
  ↓
HTTP Request (OCR)
  ↓
HTTP Request (Generate PDF)
  ↓
Send Email with PDF
```

**OCR Node:**
- Method: POST
- URL: `https://your-service.koyeb.app/ocr/image`
- Body Type: Form-Data
- File: `{{ $binary.data }}`

### Example 3: Video Processing

```
Trigger (New Video)
  ↓
HTTP Request (Compress)
  ↓
HTTP Request (Generate Thumbnail)
  ↓
Upload to Storage
```

---

## 🎛️ Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | 8000 | API port |
| `WORKERS` | 2 | Uvicorn workers |
| `MAX_UPLOAD_SIZE` | 100 | Max file size (MB) |
| `CLEANUP_HOURS` | 24 | Auto-cleanup interval |
| `MAX_CRAWL_PAGES` | 50 | Max pages per deep crawl |
| `MAX_PDF_PAGES` | 500 | Max PDF pages for OCR |

### Resource Limits

**Koyeb Free Tier:**
- RAM: 2GB
- CPU: 2 cores
- Storage: Container + temp files

**Actual Usage:**
- Idle: ~800MB RAM
- Under load: ~1.5GB RAM
- CPU: Varies by task

---

## 🛡️ Stability & Safety

### Built-in Protections

1. **Automatic file cleanup** - Removes old files every 24 hours
2. **Size limits** - Prevents resource exhaustion
3. **Request limits** - Max 10 concurrent requests
4. **Timeouts** - All operations have timeouts
5. **Error handling** - Graceful failure recovery

### What Can Break

❌ **Running out of disk space**
- Solution: Files auto-cleanup after 24 hours
- Manual: Delete `/app/storage/outputs/*`

❌ **Memory exhaustion**
- Solution: Service auto-restarts
- Prevention: Use resource limits

❌ **Too many concurrent requests**
- Solution: Built-in rate limiting
- Prevention: Queue requests in n8n

### What Won't Break

✅ **API key expiration** - There are none
✅ **External service downtime** - Everything is local
✅ **Rate limits** - No external APIs
✅ **Version conflicts** - Everything is pinned

---

## 📊 Performance Tips

### Optimize for Speed

1. **Use `/crawl/scrape/text`** instead of `/scrape/html` if you only need text
2. **Use FFmpeg trim with `-c copy`** (no re-encoding) for speed
3. **Compress videos with CRF 28** for faster processing
4. **Limit OCR to specific pages** instead of entire PDFs

### Optimize for Quality

1. **Use CRF 18-23** for video compression
2. **Set OCR DPI to 300+** for better accuracy
3. **Use `fit_to_page=true`** for better PDF quality from images

### Optimize for Resources

1. **Process videos sequentially** (not in parallel)
2. **Use deep scraping sparingly** (max 10-20 pages)
3. **Split large PDFs** into smaller batches
4. **Delete files immediately** after processing

---

## 🔧 Troubleshooting

### Service won't start

**Check logs:**
```bash
# Koyeb dashboard → Service → Logs
```

**Common issues:**
- Port 8000 not exposed
- Insufficient memory (need 2GB minimum)
- Docker build failed

### Endpoints return 500 errors

**Check:**
1. File size under 100MB?
2. Valid file format?
3. Correct parameters?

**Debug:**
- Check `/health` endpoint
- Check `/info` for resource usage
- Review error message in response

### Out of disk space

**Solution:**
```bash
# Manual cleanup (if SSH access)
rm -rf /app/storage/uploads/*
rm -rf /app/storage/outputs/*
rm -rf /app/storage/temp/*
```

**Prevention:**
- Set `CLEANUP_HOURS=12` for more frequent cleanup
- Process files and delete immediately

### Memory errors

**Koyeb free tier has 2GB RAM limit**

**Solutions:**
- Reduce concurrent requests
- Process smaller files
- Upgrade to Koyeb paid tier (8GB RAM)

---

## 📈 Scaling Considerations

### When to Upgrade

**You need more resources if:**
- Regular 500 errors
- Frequent timeouts
- Memory warnings in logs
- Queue backlog in n8n

### Upgrade Options

**Koyeb Paid Tier:**
- 8GB RAM: $20/month
- 16GB RAM: $40/month
- Dedicated CPU

**Horizontal Scaling:**
- Deploy multiple instances
- Use load balancer
- Separate by function (one for video, one for OCR, etc.)

---

## 🎯 Use Cases

### Content Automation

- Scrape articles → Extract text → Generate PDF
- Monitor websites → Alert on changes
- Archive web pages → OCR images → Store text

### Document Processing

- Upload receipts → OCR → Parse data
- Scan documents → Extract text → Analyze
- Convert images → PDF → Archive

### Video Operations

- Compress videos → Generate thumbnails → Upload
- Trim clips → Merge → Export
- Extract audio → Convert format → Store

### n8n Workflows

- RSS feed → Scrape full article → Generate PDF → Email
- Upload image → OCR → Parse invoice → Save to database
- New video → Compress → Thumbnail → Post to social media

---

## ⚠️ Limitations

### What This Service CANNOT Do

❌ AI/ML tasks (no models included)
❌ Transcription (no Whisper/speech-to-text)
❌ Auto-captioning (removed for simplicity)
❌ Cloud storage (no S3/MinIO built-in)
❌ Database (no PostgreSQL/MongoDB)
❌ Authentication (no API keys/auth)

### Why These Limitations?

**Philosophy:** Keep it simple, stable, and maintenance-free.

Adding these features would require:
- External dependencies
- Configuration complexity
- Regular updates
- More memory/CPU
- Potential breaking changes

### What to Use Instead

- **Transcription:** Use external services (Deepgram, AssemblyAI)
- **Storage:** Use n8n's built-in storage or external S3
- **Database:** Use n8n's database nodes or external services
- **Auth:** Add authentication in n8n or API gateway

---

## 🎓 Best Practices

### File Management

1. **Delete after processing** - Don't accumulate files
2. **Use streaming** - For large files
3. **Check size first** - Before uploading
4. **Batch operations** - Process multiple files efficiently

### Error Handling

1. **Always check response status**
2. **Implement retries** - For network issues
3. **Validate inputs** - Before sending
4. **Log errors** - For debugging

### Resource Management

1. **Queue requests** - Don't overwhelm the service
2. **Monitor usage** - Check `/info` regularly
3. **Scale horizontally** - If needed
4. **Set timeouts** - In your client

---

## 📝 Version History

### v1.0.0 (Current)

**Initial release:**
- Crawl4AI 0.3.74 (raw mode only)
- Tesseract OCR (multi-language)
- PDF Generation (4 methods)
- FFmpeg (8 operations)
- Auto-cleanup
- Koyeb-optimized

**Future versions:**
- Will maintain backward compatibility
- Will not add external dependencies
- Will not require API keys
- Will remain maintenance-free

---

## 🤝 Contributing

This service is designed to be **zero-maintenance**. Contributions should:

1. Not add external dependencies
2. Not require API keys
3. Not break existing endpoints
4. Not increase resource usage significantly
5. Include documentation

---

## 📄 License

MIT License - Use freely in any project.

---

## 🎉 Ready to Deploy?

1. Push to GitHub
2. Deploy to Koyeb
3. Test with `/docs`
4. Integrate with n8n
5. Forget about it (it just works™)

**Questions?** Check `/info` for system status and capabilities.

**Need help?** All endpoints are documented in `/docs` with examples.

---

**Made for Koyeb free tier. Optimized for n8n. Zero maintenance required.**
