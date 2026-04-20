const fs = require('fs')
const zlib = require('zlib')

const raw = fs.readFileSync('extra/data.1.js', 'utf8')
// format: window["hzv5"]["flpk"] = [ [num, num, "b64"], [...], ... ];
// extract each base64 payload with regex
const re = /\[\s*(\d+)\s*,\s*(\d+)\s*,\s*"([^"]+)"\s*\]/g
let m, i = 0
if (!fs.existsSync('decoded')) fs.mkdirSync('decoded')
while ((m = re.exec(raw))) {
  const [, pid, sid, b64] = m
  try {
    const buf = Buffer.from(b64, 'base64')
    const txt = zlib.gunzipSync(buf).toString('utf8')
    fs.writeFileSync(`decoded/${i}_${sid}.json`, txt)
    console.log(`#${i} sid=${sid} bytes=${txt.length}`)
    i++
  } catch (e) {
    console.log(`#${i} fail: ${e.message}`)
    i++
  }
}
console.log('done:', i)
