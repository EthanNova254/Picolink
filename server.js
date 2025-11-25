const express = require('express');
const path = require('path');
const { nanoid } = require('nanoid');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const PORT = process.env.PORT || 3000;

// SQLite database (persistent)
const db = new sqlite3.Database('./links.db');
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS links (
    code TEXT PRIMARY KEY,
    final_url TEXT NOT NULL,
    ad_url TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER
  )`);
});

const AD_URL = process.env.AD_URL || 'https://otieu.com/4/10234378';
const REDIRECT_DELAY = parseInt(process.env.REDIRECT_DELAY || '15');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// API endpoint to create short link
app.post('/api/create', (req, res) => {
  const { url, expiry } = req.body;
  if (!url) return res.json({ success: false, error: 'Missing URL' });

  const shortCode = nanoid(8);
  const now = Date.now();
  let expiresAt = null;

  if (expiry !== 'never') {
    expiresAt = now + parseInt(expiry) * 24 * 60 * 60 * 1000;
  }

  db.run(
    `INSERT INTO links (code, final_url, ad_url, created_at, expires_at)
     VALUES (?, ?, ?, ?, ?)`,
    [shortCode, url, AD_URL, now, expiresAt],
    (err) => {
      if (err) return res.json({ success: false, error: err.message });

      res.json({
        success: true,
        shortUrl: `${req.protocol}://${req.get('host')}/go/${shortCode}`,
        shortCode,
        originalUrl: url,
        expiryDate: expiresAt ? new Date(expiresAt).toISOString() : null,
        expiryDays: expiry
      });
    }
  );
});

// Redirect to ad page with countdown
app.get('/go/:code', (req, res) => {
  db.get(`SELECT * FROM links WHERE code = ?`, [req.params.code], (err, data) => {
    if (err || !data) return res.send('<h1>⚠️ Link not found</h1>');

    const now = Date.now();
    if (data.expires_at && now > data.expires_at) return res.send('<h1>⚠️ Link expired</h1>');

    res.send(`
      <html>
      <head>
        <title>Viewing Ad</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { text-align:center; font-family:sans-serif; padding:50px; background:#030712; color:white; }
          #count { font-size: 24px; color: #00eaff; }
          button { padding:15px; font-size:18px; margin:10px; border:none; border-radius:8px; cursor:pointer; }
        </style>
      </head>
      <body>
        <h1>Viewing Ad...</h1>
        <p id="count">${REDIRECT_DELAY}</p>
        <button id="continue" style="display:none; background:#00eaff;">Continue to Link</button>
        <button onclick="window.open('${data.ad_url}','_blank')" style="background:#00eaff;">Learn More</button>
        <script>
          let countdown = ${REDIRECT_DELAY};
          const countEl = document.getElementById('count');
          const btn = document.getElementById('continue');
          btn.onclick = () => { window.location='/final/${req.params.code}'; };
          const interval = setInterval(()=>{
            countdown--;
            countEl.textContent = countdown;
            if(countdown<=0){ clearInterval(interval); btn.style.display='inline-block'; countEl.style.display='none'; }
          },1000);
        </script>
      </body>
      </html>
    `);
  });
});

// Final redirect to original URL
app.get('/final/:code', (req, res) => {
  db.get(`SELECT * FROM links WHERE code = ?`, [req.params.code], (err, data) => {
    if (err || !data) return res.send('<h1>⚠️ Link not found</h1>');
    const now = Date.now();
    if (data.expires_at && now > data.expires_at) return res.send('<h1>⚠️ Link expired</h1>');
    res.redirect(data.final_url);
  });
});

app.listen(PORT, () => console.log(`PicoLink running on port ${PORT}`));
